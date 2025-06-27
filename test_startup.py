#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动测试脚本 - 验证所有组件是否正常工作
"""

import os
import sys
import subprocess
import importlib.util

def test_python_environment():
    """测试Python环境"""
    print("🐍 测试Python环境...")
    print(f"   Python版本: {sys.version}")
    print(f"   Python路径: {sys.executable}")
    return True

def test_dependencies():
    """测试依赖包"""
    print("📦 测试依赖包...")
    required_packages = [
        'flask', 'werkzeug', 'jinja2', 'markupsafe', 
        'itsdangerous', 'click', 'blinker', 'pygments'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"   缺少依赖: {', '.join(missing_packages)}")
        return False
    return True

def test_symbolicatecrash():
    """测试symbolicatecrash工具"""
    print("🔧 测试symbolicatecrash工具...")
    
    possible_paths = [
        '/Applications/Xcode.app/Contents/SharedFrameworks/DVTFoundation.framework/Versions/A/Resources/symbolicatecrash',
        '/Applications/Xcode.app/Contents/SharedFrameworks/AssetRuntime/DVTFoundation.framework/Versions/A/Resources/symbolicatecrash',
        '/usr/bin/symbolicatecrash',
        '/usr/local/bin/symbolicatecrash'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"   ✅ 找到工具: {path}")
            return True
    
    print("   ❌ 未找到symbolicatecrash工具")
    return False

def test_app_import():
    """测试应用导入"""
    print("🌐 测试Flask应用...")
    try:
        from app import app, find_symbolicatecrash
        print("   ✅ app.py导入成功")
        
        # 测试symbolicatecrash查找函数
        tool_path = find_symbolicatecrash()
        if tool_path:
            print(f"   ✅ symbolicatecrash路径: {tool_path}")
        else:
            print("   ❌ 未找到symbolicatecrash工具")
            return False
            
        return True
    except Exception as e:
        print(f"   ❌ 应用导入失败: {e}")
        return False

def test_cli_import():
    """测试命令行工具"""
    print("⚡ 测试命令行工具...")
    try:
        import cli
        print("   ✅ cli.py导入成功")
        return True
    except Exception as e:
        print(f"   ❌ 命令行工具导入失败: {e}")
        return False

def test_directories():
    """测试目录结构"""
    print("📁 测试目录结构...")
    required_dirs = ['templates']
    required_files = [
        'app.py', 'cli.py', 'requirements.txt', 
        'README.md', 'start.sh', 'config.py'
    ]
    
    all_good = True
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"   ✅ 目录: {directory}")
        else:
            print(f"   ❌ 缺少目录: {directory}")
            all_good = False
    
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ 文件: {file}")
        else:
            print(f"   ❌ 缺少文件: {file}")
            all_good = False
    
    return all_good

def main():
    """主测试函数"""
    print("🧪 iOS崩溃日志符号化工具 - 启动测试")
    print("=" * 50)
    
    tests = [
        ("Python环境", test_python_environment),
        ("依赖包", test_dependencies),
        ("symbolicatecrash工具", test_symbolicatecrash),
        ("Flask应用", test_app_import),
        ("命令行工具", test_cli_import),
        ("目录结构", test_directories),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！工具可以正常使用。")
        print("\n💡 下一步:")
        print("   - 启动Web服务: ./start.sh")
        print("   - 查看帮助: ./start.sh --help")
        print("   - 命令行工具: python3 cli.py --help")
        return True
    else:
        print("⚠️  部分测试失败，请检查环境配置。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 