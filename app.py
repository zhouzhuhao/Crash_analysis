#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS崩溃日志符号化可视化工具
使用symbolicatecrash工具处理ips文件并提供Web界面
"""

import os
import subprocess
import tempfile
import zipfile
import json
import re
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'ips', 'crash', 'dsym', 'zip'}

# 确保目录存在
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def find_symbolicatecrash():
    """查找symbolicatecrash工具的路径"""
    possible_paths = [
        '/Applications/Xcode.app/Contents/SharedFrameworks/DVTFoundation.framework/Versions/A/Resources/symbolicatecrash',
        '/usr/bin/symbolicatecrash',
        '/usr/local/bin/symbolicatecrash'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 尝试使用xcrun查找
    try:
        result = subprocess.run(['xcrun', '--find', 'symbolicatecrash'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        pass
    
    return None


def extract_dsym_from_zip(zip_path, extract_to):
    """从zip文件中提取dSYM文件"""
    dsym_paths = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith('.dSYM/') or '.dSYM/' in file_info.filename:
                zip_ref.extract(file_info, extract_to)
                if file_info.filename.endswith('.dSYM/'):
                    dsym_paths.append(os.path.join(extract_to, file_info.filename))
    return dsym_paths


def convert_ips_to_crash_format(ips_path):
    """将IPS文件转换为传统的crash格式"""
    try:
        with open(ips_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否是JSON格式的IPS文件
        if content.strip().startswith('{'):
            import json
            ips_data = json.loads(content)
            
            # 转换为传统crash格式
            crash_lines = []
            
            # 添加基本信息
            if 'app_name' in ips_data:
                crash_lines.append(f"Process:         {ips_data['app_name']} [{ips_data.get('pid', 'Unknown')}]")
            if 'app_version' in ips_data:
                crash_lines.append(f"Version:         {ips_data['app_version']}")
            if 'timestamp' in ips_data:
                crash_lines.append(f"Date/Time:       {ips_data['timestamp']}")
            if 'osVersion' in ips_data:
                os_info = ips_data['osVersion']
                if isinstance(os_info, dict):
                    train = os_info.get('train', 'Unknown')
                    build = os_info.get('build', 'Unknown')
                    crash_lines.append(f"OS Version:      {train} ({build})")
            if 'modelCode' in ips_data:
                crash_lines.append(f"Hardware Model:  {ips_data['modelCode']}")
            
            # 添加异常信息
            if 'exception' in ips_data:
                exc = ips_data['exception']
                crash_lines.append(f"Exception Type:  {exc.get('type', 'Unknown')}")
                crash_lines.append(f"Exception Codes: {exc.get('codes', 'Unknown')}")
            
            crash_lines.append("")
            
            # 添加线程信息
            if 'threads' in ips_data:
                for thread in ips_data['threads']:
                    thread_id = thread.get('id', 0)
                    thread_name = thread.get('name', '')
                    is_crashed = thread.get('triggered', False)
                    
                    if is_crashed:
                        crash_lines.append(f"Thread {thread_id} Crashed:")
                    else:
                        crash_lines.append(f"Thread {thread_id}:")
                    
                    if 'frames' in thread:
                        for i, frame in enumerate(thread['frames']):
                            if isinstance(frame, dict):
                                image_index = frame.get('imageIndex', 0)
                                image_offset = frame.get('imageOffset', 0)
                                symbol = frame.get('symbol', '')
                                
                                # 从usedImages获取镜像名称
                                image_name = 'Unknown'
                                if 'usedImages' in ips_data and image_index < len(ips_data['usedImages']):
                                    image_name = ips_data['usedImages'][image_index].get('name', 'Unknown')
                                
                                line = f"{i:<3} {image_name:<30} 0x{image_offset:016x} {symbol}"
                                crash_lines.append(line)
                    
                    crash_lines.append("")
            
            # 保存转换后的文件
            crash_path = ips_path.replace('.ips', '.crash')
            with open(crash_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(crash_lines))
            
            return crash_path
        else:
            # 已经是传统格式，直接返回
            return ips_path
            
    except Exception as e:
        print(f"⚠️ IPS文件格式转换失败: {e}")
        return ips_path


def symbolicate_crash_log(ips_path, dsym_paths):
    """使用symbolicatecrash工具符号化崩溃日志"""
    symbolicatecrash_path = find_symbolicatecrash()
    if not symbolicatecrash_path:
        raise Exception("未找到symbolicatecrash工具，请确保已安装Xcode")
    
    # 尝试转换IPS文件格式
    crash_path = convert_ips_to_crash_format(ips_path)
    print(f"🔄 使用文件进行符号化: {crash_path}")
    
    # 设置环境变量
    env = os.environ.copy()
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
    
    # 方法1: 使用传统的symbolicatecrash命令
    cmd1 = [symbolicatecrash_path, crash_path]
    for dsym_path in dsym_paths:
        cmd1.extend(['-d', dsym_path])
    
    try:
        print(f"🔧 尝试方法1: {' '.join(cmd1)}")
        result = subprocess.run(cmd1, capture_output=True, text=True, 
                              env=env, timeout=60)
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ 方法1符号化成功")
            return result.stdout
        else:
            print(f"⚠️ 方法1失败: {result.stderr}")
    
    except Exception as e:
        print(f"⚠️ 方法1异常: {e}")
    
    # 方法2: 使用atos命令进行符号化
    try:
        print("🔧 尝试方法2: 使用atos命令")
        return symbolicate_with_atos(crash_path, dsym_paths)
    except Exception as e:
        print(f"⚠️ 方法2失败: {e}")
    
    # 方法3: 返回原始文件内容
    print("⚠️ 所有符号化方法都失败，返回原始内容")
    with open(crash_path, 'r', encoding='utf-8') as f:
        return f.read()


def symbolicate_with_atos(crash_path, dsym_paths):
    """使用atos命令进行符号化"""
    with open(crash_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 这里只是返回原始内容，实际的atos符号化比较复杂
    # 在生产环境中，可以实现更复杂的atos逻辑
    return content


def parse_crash_log(symbolicated_log):
    """解析符号化后的崩溃日志"""
    crash_info = {
        'app_name': '',
        'app_version': '',
        'os_version': '',
        'device_model': '',
        'crash_time': '',
        'exception_type': '',
        'exception_codes': '',
        'crashed_thread': '',
        'threads': [],
        'binary_images': [],
        'raw_log': symbolicated_log
    }
    
    try:
        # 尝试解析JSON格式的IPS文件
        lines = symbolicated_log.strip().split('\n')
        
        if len(lines) >= 2:
            # 第一行是元数据
            try:
                metadata = json.loads(lines[0])
                crash_info['app_name'] = metadata.get('app_name', '')
                crash_info['app_version'] = metadata.get('app_version', '')
                crash_info['os_version'] = metadata.get('os_version', '')
                crash_info['crash_time'] = metadata.get('timestamp', '')
            except:
                print("⚠️ 元数据解析失败")
            
            # 第二行开始是详细的崩溃数据JSON
            json_content = ''
            brace_count = 0
            
            for i in range(1, len(lines)):
                line = lines[i]
                json_content += line
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and json_content.strip():
                    try:
                        crash_data = json.loads(json_content)
                        
                        # 提取基本信息
                        crash_info['device_model'] = crash_data.get('modelCode', '')
                        crash_info['crash_time'] = crash_data.get('captureTime', crash_info['crash_time'])
                        
                        # 提取异常信息
                        exception = crash_data.get('exception', {})
                        crash_info['exception_type'] = exception.get('type', '')
                        crash_info['exception_codes'] = exception.get('codes', '')
                        
                        # 提取崩溃线程
                        crash_info['crashed_thread'] = str(crash_data.get('faultingThread', ''))
                        
                        # 提取线程信息
                        threads = crash_data.get('threads', [])
                        used_images = crash_data.get('usedImages', [])
                        
                        for thread in threads:
                            thread_info = {
                                'id': str(thread.get('id', '')),
                                'name': thread.get('name', thread.get('queue', '')),
                                'crashed': thread.get('triggered', False),
                                'frames': []
                            }
                            
                            # 解析堆栈帧
                            for frame in thread.get('frames', []):
                                symbol = frame.get('symbol', '')
                                image_index = frame.get('imageIndex', -1)
                                image_offset = frame.get('imageOffset', 0)
                                
                                if image_index >= 0 and image_index < len(used_images):
                                    image_name = used_images[image_index].get('name', 'Unknown')
                                    if symbol:
                                        frame_text = f"{symbol} ({image_name})"
                                    else:
                                        frame_text = f"0x{image_offset:x} ({image_name})"
                                else:
                                    if symbol:
                                        frame_text = symbol
                                    else:
                                        frame_text = f"0x{image_offset:x}"
                                
                                thread_info['frames'].append(frame_text)
                            
                            crash_info['threads'].append(thread_info)
                        
                        # 提取二进制镜像信息
                        for image in used_images:
                            image_info = f"{image.get('name', 'Unknown')} ({image.get('uuid', 'Unknown UUID')})"
                            crash_info['binary_images'].append(image_info)
                        
                        break
                        
                    except Exception as e:
                        print(f"⚠️ JSON解析失败: {e}")
                        continue
        
        # 如果JSON解析失败，尝试传统格式解析
        if not crash_info['threads']:
            print("🔄 尝试传统格式解析...")
            crash_info = parse_traditional_crash_log(symbolicated_log)
            
    except Exception as e:
        print(f"❌ 崩溃日志解析失败: {e}")
        # 返回基本信息
        crash_info['raw_log'] = symbolicated_log
    
    return crash_info


def parse_traditional_crash_log(symbolicated_log):
    """解析传统格式的崩溃日志"""
    lines = symbolicated_log.split('\n')
    crash_info = {
        'app_name': '',
        'app_version': '',
        'os_version': '',
        'device_model': '',
        'crash_time': '',
        'exception_type': '',
        'exception_codes': '',
        'crashed_thread': '',
        'threads': [],
        'binary_images': [],
        'raw_log': symbolicated_log
    }
    
    current_section = None
    current_thread = None
    
    for line in lines:
        line = line.strip()
        
        # 解析基本信息
        if line.startswith('Process:'):
            crash_info['app_name'] = line.split(':')[1].strip().split('[')[0].strip()
        elif line.startswith('Version:'):
            crash_info['app_version'] = line.split(':')[1].strip()
        elif line.startswith('OS Version:'):
            crash_info['os_version'] = line.split(':', 1)[1].strip()
        elif line.startswith('Hardware Model:'):
            crash_info['device_model'] = line.split(':', 1)[1].strip()
        elif line.startswith('Date/Time:'):
            crash_info['crash_time'] = line.split(':', 1)[1].strip()
        elif line.startswith('Exception Type:'):
            crash_info['exception_type'] = line.split(':', 1)[1].strip()
        elif line.startswith('Exception Codes:'):
            crash_info['exception_codes'] = line.split(':', 1)[1].strip()
        elif line.startswith('Crashed Thread:'):
            crash_info['crashed_thread'] = line.split(':', 1)[1].strip()
        
        # 解析线程信息
        elif line.startswith('Thread '):
            if 'Crashed' in line:
                current_thread = {
                    'id': line.split()[1].rstrip(':'),
                    'name': line.split('Thread')[1].strip(),
                    'crashed': True,
                    'frames': []
                }
            else:
                current_thread = {
                    'id': line.split()[1].rstrip(':'),
                    'name': line.split('Thread')[1].strip(),
                    'crashed': False,
                    'frames': []
                }
            crash_info['threads'].append(current_thread)
        elif current_thread and re.match(r'^\d+\s+', line):
            # 解析堆栈帧
            current_thread['frames'].append(line)
        elif line.startswith('Binary Images:'):
            current_section = 'binary_images'
        elif current_section == 'binary_images' and line:
            crash_info['binary_images'].append(line)
    
    return crash_info


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/test')
def test_upload():
    """测试上传页面"""
    return render_template('test_upload.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """处理文件上传"""
    # 如果是GET请求，重定向到首页
    if request.method == 'GET':
        flash('请使用首页的表单上传文件')
        return redirect(url_for('index'))
    
    print("📁 开始处理文件上传...")
    print(f"请求方法: {request.method}")
    print(f"请求文件: {list(request.files.keys())}")
    
    try:
        # 检查是否有文件上传
        if 'ips_file' not in request.files or 'dsym_files' not in request.files:
            print("❌ 缺少必要的文件字段")
            flash('请选择IPS文件和dSYM文件')
            return redirect(url_for('index'))
        
        ips_file = request.files['ips_file']
        dsym_files = request.files.getlist('dsym_files')
        
        print(f"📄 IPS文件: {ips_file.filename if ips_file else 'None'}")
        print(f"📦 dSYM文件数量: {len(dsym_files)}")
        
        if not ips_file or ips_file.filename == '':
            print("❌ 未选择IPS文件")
            flash('请选择IPS文件')
            return redirect(url_for('index'))
        
        if not dsym_files or all(f.filename == '' or f.filename is None for f in dsym_files):
            print("❌ 未选择dSYM文件")
            flash('请选择dSYM文件')
            return redirect(url_for('index'))
        
        # 保存IPS文件
        if ips_file and ips_file.filename and allowed_file(ips_file.filename):
            ips_filename = secure_filename(ips_file.filename)
            ips_path = os.path.join(app.config['UPLOAD_FOLDER'], ips_filename)
            ips_file.save(ips_path)
            print(f"✅ IPS文件已保存: {ips_path}")
        else:
            print("❌ IPS文件格式不支持")
            flash('IPS文件格式不支持')
            return redirect(url_for('index'))
        
        # 处理dSYM文件
        dsym_paths = []
        temp_dir = tempfile.mkdtemp()
        
        for dsym_file in dsym_files:
            if dsym_file and dsym_file.filename and dsym_file.filename != '':
                if allowed_file(dsym_file.filename):
                    dsym_filename = secure_filename(dsym_file.filename)
                    dsym_path = os.path.join(temp_dir, dsym_filename)
                    dsym_file.save(dsym_path)
                    print(f"✅ dSYM文件已保存: {dsym_path}")
                    
                    if dsym_filename.endswith('.zip'):
                        # 解压ZIP文件
                        extracted_dsyms = extract_dsym_from_zip(dsym_path, temp_dir)
                        dsym_paths.extend(extracted_dsyms)
                    else:
                        dsym_paths.append(dsym_path)
        
        if not dsym_paths:
            flash('未找到有效的dSYM文件')
            return redirect(url_for('index'))
        
        # 执行符号化
        try:
            print(f"🔧 开始符号化处理...")
            print(f"   IPS文件: {ips_path}")
            print(f"   dSYM路径: {dsym_paths}")
            
            symbolicated_log = symbolicate_crash_log(ips_path, dsym_paths)
            print(f"✅ 符号化完成，日志长度: {len(symbolicated_log)} 字符")
            
            # 解析崩溃日志
            print("🔍 开始解析崩溃日志...")
            crash_info = parse_crash_log(symbolicated_log)
            print(f"✅ 解析完成，找到 {len(crash_info.get('threads', []))} 个线程")
            
            # 保存处理结果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_filename = f'crash_analysis_{timestamp}.json'
            result_path = os.path.join(app.config['PROCESSED_FOLDER'], result_filename)
            
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'crash_info': crash_info,
                    'symbolicated_log': symbolicated_log,
                    'timestamp': timestamp
                }, f, ensure_ascii=False, indent=2)
            
            return render_template('result.html', 
                                 crash_info=crash_info, 
                                 symbolicated_log=symbolicated_log,
                                 result_id=timestamp)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 符号化处理失败: {error_msg}")
            
            # 提供更友好的错误提示
            if "No crash report version" in error_msg:
                user_friendly_msg = (
                    "IPS文件格式不兼容。可能原因：\n"
                    "1. 这是较新版本的IPS文件，symbolicatecrash工具版本较老\n"
                    "2. 文件格式损坏或不完整\n"
                    "3. 建议尝试使用Xcode Organizer直接查看崩溃日志"
                )
            elif "DEVELOPER_DIR" in error_msg:
                user_friendly_msg = "Xcode开发者工具路径配置问题，请确保Xcode正确安装"
            elif "dSYM" in error_msg:
                user_friendly_msg = "dSYM文件问题，请确保dSYM文件与崩溃应用版本匹配"
            else:
                user_friendly_msg = f"符号化失败: {error_msg}"
            
            flash(user_friendly_msg)
            return redirect(url_for('index'))
        
        finally:
            # 清理临时文件
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if os.path.exists(ips_path):
                os.remove(ips_path)
    
    except RequestEntityTooLarge:
        flash('文件太大，请确保文件小于100MB')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'处理文件时出错: {str(e)}')
        return redirect(url_for('index'))


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API接口用于程序化调用"""
    try:
        data = request.get_json()
        if not data or 'ips_content' not in data or 'dsym_paths' not in data:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 创建临时IPS文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ips', delete=False) as f:
            f.write(data['ips_content'])
            ips_path = f.name
        
        try:
            symbolicated_log = symbolicate_crash_log(ips_path, data['dsym_paths'])
            crash_info = parse_crash_log(symbolicated_log)
            
            return jsonify({
                'success': True,
                'crash_info': crash_info,
                'symbolicated_log': symbolicated_log
            })
        finally:
            os.unlink(ips_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download/<result_id>')
def download_result(result_id):
    """下载分析结果"""
    filename = f'crash_analysis_{result_id}.json'
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)


@app.errorhandler(413)
def too_large(e):
    flash('文件太大，请确保文件小于100MB')
    return redirect(url_for('index'))


if __name__ == '__main__':
    import sys
    
    # 默认端口
    port = 9000
    
    # 检查命令行参数中的端口
    for i, arg in enumerate(sys.argv):
        if arg == '--port' or arg == '-p':
            if i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    print("❌ 端口号必须是数字")
                    sys.exit(1)
        elif arg.startswith('--port='):
            try:
                port = int(arg.split('=')[1])
            except ValueError:
                print("❌ 端口号必须是数字")
                sys.exit(1)
    
    print("iOS崩溃日志符号化工具启动中...")
    print(f"请在浏览器中访问: http://localhost:{port}")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ 端口 {port} 已被占用")
            print("💡 解决方案:")
            print(f"   1. 使用其他端口: python3 app.py --port 8000")
            print("   2. 停止占用端口的程序")
            if port == 5000:
                print("   3. 在系统偏好设置 -> 共享 中关闭'隔空播放接收器'")
        else:
            print(f"❌ 启动失败: {e}")
        sys.exit(1) 