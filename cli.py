#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS崩溃日志符号化命令行工具
支持批量处理和脚本化使用
"""

import argparse
import os
import sys
import json
import subprocess
import tempfile
import zipfile
import glob
from pathlib import Path
from datetime import datetime


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


def find_dsym_files(dsym_paths):
    """查找并收集所有dSYM文件"""
    all_dsym_paths = []
    temp_dirs = []
    
    for path in dsym_paths:
        if os.path.isfile(path) and path.endswith('.zip'):
            # 处理ZIP文件
            temp_dir = tempfile.mkdtemp()
            temp_dirs.append(temp_dir)
            extracted_dsyms = extract_dsym_from_zip(path, temp_dir)
            all_dsym_paths.extend(extracted_dsyms)
        elif os.path.isdir(path) and path.endswith('.dSYM'):
            # 直接的dSYM目录
            all_dsym_paths.append(path)
        elif os.path.isdir(path):
            # 搜索目录中的dSYM文件
            dsym_pattern = os.path.join(path, '**/*.dSYM')
            found_dsyms = glob.glob(dsym_pattern, recursive=True)
            all_dsym_paths.extend(found_dsyms)
    
    return all_dsym_paths, temp_dirs


def symbolicate_crash_log(ips_path, dsym_paths, verbose=False):
    """使用symbolicatecrash工具符号化崩溃日志"""
    symbolicatecrash_path = find_symbolicatecrash()
    if not symbolicatecrash_path:
        raise Exception("未找到symbolicatecrash工具，请确保已安装Xcode")
    
    if verbose:
        print(f"使用symbolicatecrash工具: {symbolicatecrash_path}")
        print(f"处理IPS文件: {ips_path}")
        print(f"dSYM文件路径: {dsym_paths}")
    
    # 设置环境变量
    env = os.environ.copy()
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
    
    # 构建命令
    cmd = [symbolicatecrash_path, ips_path]
    
    # 添加dSYM路径
    for dsym_path in dsym_paths:
        cmd.extend(['-d', dsym_path])
    
    if verbose:
        print(f"执行命令: {' '.join(cmd)}")
    
    try:
        # 执行符号化
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              env=env, timeout=120)
        
        if result.returncode == 0:
            return result.stdout
        else:
            error_msg = result.stderr or "符号化失败"
            raise Exception(f"符号化失败: {error_msg}")
            
    except subprocess.TimeoutExpired:
        raise Exception("符号化超时")
    except Exception as e:
        raise Exception(f"执行符号化时出错: {str(e)}")


def parse_crash_log(symbolicated_log):
    """解析符号化后的崩溃日志"""
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
        'binary_images': []
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
        elif current_thread and line and line[0].isdigit():
            # 解析堆栈帧
            current_thread['frames'].append(line)
        elif line.startswith('Binary Images:'):
            current_section = 'binary_images'
        elif current_section == 'binary_images' and line:
            crash_info['binary_images'].append(line)
    
    return crash_info


def process_single_file(ips_path, dsym_paths, output_dir, verbose=False):
    """处理单个IPS文件"""
    if verbose:
        print(f"\n处理文件: {ips_path}")
    
    try:
        # 查找dSYM文件
        all_dsym_paths, temp_dirs = find_dsym_files(dsym_paths)
        
        if not all_dsym_paths:
            raise Exception("未找到有效的dSYM文件")
        
        if verbose:
            print(f"找到dSYM文件: {all_dsym_paths}")
        
        # 执行符号化
        symbolicated_log = symbolicate_crash_log(ips_path, all_dsym_paths, verbose)
        
        # 解析崩溃日志
        crash_info = parse_crash_log(symbolicated_log)
        
        # 生成输出文件名
        ips_basename = os.path.splitext(os.path.basename(ips_path))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存符号化日志
        symbolicated_path = os.path.join(output_dir, f"{ips_basename}_symbolicated_{timestamp}.crash")
        with open(symbolicated_path, 'w', encoding='utf-8') as f:
            f.write(symbolicated_log)
        
        # 保存解析结果
        json_path = os.path.join(output_dir, f"{ips_basename}_analysis_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'crash_info': crash_info,
                'symbolicated_log': symbolicated_log,
                'timestamp': timestamp,
                'source_file': ips_path,
                'dsym_files': all_dsym_paths
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 处理成功: {ips_path}")
        print(f"   符号化日志: {symbolicated_path}")
        print(f"   分析结果: {json_path}")
        
        # 清理临时文件
        import shutil
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {ips_path}")
        print(f"   错误信息: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='iOS崩溃日志符号化命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 处理单个文件
  python cli.py -i crash.ips -d App.dSYM -o output/
  
  # 处理多个文件
  python cli.py -i "crashes/*.ips" -d "dsyms/*.dSYM" -o output/
  
  # 使用ZIP压缩包中的dSYM
  python cli.py -i crash.ips -d dsyms.zip -o output/
  
  # 批量处理并显示详细信息
  python cli.py -i "crashes/*.ips" -d dsyms/ -o output/ -v
        '''
    )
    
    parser.add_argument('-i', '--input', required=True,
                        help='IPS文件路径，支持通配符模式')
    parser.add_argument('-d', '--dsym', required=True, nargs='+',
                        help='dSYM文件或目录路径，可指定多个')
    parser.add_argument('-o', '--output', required=True,
                        help='输出目录路径')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='显示详细信息')
    
    args = parser.parse_args()
    
    # 检查输出目录
    output_dir = os.path.abspath(args.output)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")
    
    # 查找IPS文件
    ips_files = []
    if '*' in args.input or '?' in args.input:
        ips_files = glob.glob(args.input)
    else:
        if os.path.exists(args.input):
            ips_files = [args.input]
    
    if not ips_files:
        print(f"❌ 未找到IPS文件: {args.input}")
        sys.exit(1)
    
    print(f"找到 {len(ips_files)} 个IPS文件")
    
    # 检查symbolicatecrash工具
    if not find_symbolicatecrash():
        print("❌ 未找到symbolicatecrash工具，请确保已安装Xcode")
        sys.exit(1)
    
    # 处理文件
    success_count = 0
    total_count = len(ips_files)
    
    for ips_file in ips_files:
        if process_single_file(ips_file, args.dsym, output_dir, args.verbose):
            success_count += 1
    
    print(f"\n处理完成: {success_count}/{total_count} 个文件成功")
    
    if success_count < total_count:
        sys.exit(1)


if __name__ == '__main__':
    main() 