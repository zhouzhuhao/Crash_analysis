#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS崩溃日志符号化工具配置文件
"""

import os

class Config:
    """基础配置"""
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = 'uploads'
    PROCESSED_FOLDER = 'processed'
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'ips', 'crash', 'dsym', 'zip'}
    
    # symbolicatecrash工具配置
    SYMBOLICATECRASH_TIMEOUT = 120  # 超时时间（秒）
    
    # 可能的symbolicatecrash路径
    SYMBOLICATECRASH_PATHS = [
        '/Applications/Xcode.app/Contents/SharedFrameworks/DVTFoundation.framework/Versions/A/Resources/symbolicatecrash',
        '/usr/bin/symbolicatecrash',
        '/usr/local/bin/symbolicatecrash'
    ]
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'crash_analysis.log'
    
    # Web服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 