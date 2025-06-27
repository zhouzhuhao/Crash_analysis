#!/usr/bin/env python3
"""测试崩溃日志解析功能"""

import json
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import parse_crash_log

def test_parsing():
    """测试解析功能"""
    print("🧪 测试崩溃日志解析功能...")
    
    # 读取之前保存的分析结果
    result_file = None
    processed_dir = 'processed'
    
    if os.path.exists(processed_dir):
        files = [f for f in os.listdir(processed_dir) if f.endswith('.json')]
        if files:
            result_file = os.path.join(processed_dir, sorted(files)[-1])  # 最新的文件
    
    if not result_file:
        print("❌ 未找到分析结果文件")
        return
    
    print(f"📁 读取文件: {result_file}")
    
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取原始日志
    raw_log = data.get('symbolicated_log', '')
    if not raw_log:
        print("❌ 未找到原始日志数据")
        return
    
    print(f"📋 原始日志长度: {len(raw_log)} 字符")
    
    # 使用新的解析函数
    print("🔍 开始解析...")
    crash_info = parse_crash_log(raw_log)
    
    # 显示解析结果
    print("\n✅ 解析结果:")
    print(f"应用名称: {crash_info['app_name']}")
    print(f"应用版本: {crash_info['app_version']}")
    print(f"系统版本: {crash_info['os_version']}")
    print(f"设备型号: {crash_info['device_model']}")
    print(f"崩溃时间: {crash_info['crash_time']}")
    print(f"异常类型: {crash_info['exception_type']}")
    print(f"异常代码: {crash_info['exception_codes']}")
    print(f"崩溃线程: {crash_info['crashed_thread']}")
    print(f"线程数量: {len(crash_info['threads'])}")
    print(f"二进制镜像数量: {len(crash_info['binary_images'])}")
    
    # 显示崩溃线程的堆栈
    print("\n💥 崩溃线程堆栈:")
    for thread in crash_info['threads']:
        if thread['crashed']:
            print(f"线程 {thread['id']}: {thread['name']}")
            for i, frame in enumerate(thread['frames'][:10]):  # 显示前10帧
                print(f"  {i}: {frame}")
            break
    
    # 显示关键库信息
    print("\n📚 关键二进制镜像:")
    for i, image in enumerate(crash_info['binary_images'][:5]):  # 显示前5个
        print(f"  {i}: {image}")
    
    print("\n🎉 解析测试完成！")

if __name__ == '__main__':
    test_parsing() 