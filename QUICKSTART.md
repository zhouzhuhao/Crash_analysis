# 快速开始指南

## 🚀 一分钟快速启动

### 1. 环境检查
```bash
./start_smart.sh --check
```

### 2. 启动服务器
```bash
./start_smart.sh
```

### 3. 访问Web界面
在浏览器中打开显示的地址，通常是：`http://localhost:9000`

## 📱 使用步骤

1. **上传IPS文件**：拖拽或点击选择您的崩溃日志文件
2. **上传dSYM文件**：拖拽或点击选择对应的符号文件
3. **点击分析**：等待符号化处理完成
4. **查看结果**：浏览可视化的崩溃分析报告

## ⚡ 命令行快速使用

```bash
# 基本用法
python3 cli.py -i crash.ips -d App.dSYM -o results/

# 查看帮助
python3 cli.py --help
```

## 🔧 常见问题解决

### 端口被占用
```bash
# 使用智能启动自动选择端口
./start_smart.sh

# 或手动指定端口
python3 app.py --port 8080
```

### 符号化失败
1. 确保dSYM文件版本与崩溃应用匹配
2. 检查Xcode是否正确安装
3. 运行环境检查：`./start_smart.sh --check`

### 文件上传问题
1. 确认文件格式：IPS/crash文件 + dSYM文件/ZIP包
2. 检查文件大小（限制100MB）
3. 确保网络连接正常

## 💡 提示

- **首次使用**：建议先运行 `./start_smart.sh --check` 检查环境
- **批量处理**：使用命令行工具处理多个文件
- **自动化集成**：使用API接口集成到CI/CD流程
- **测试功能**：运行 `python3 test_web.py` 测试Web功能

## 📞 获取帮助

```bash
# 启动脚本帮助
./start_smart.sh --help

# 命令行工具帮助
python3 cli.py --help

# 运行测试
python3 test_startup.py
```

---

**注意**：确保您的dSYM文件与崩溃的应用版本完全匹配，这是符号化成功的关键！ 