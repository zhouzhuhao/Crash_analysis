# iOS崩溃日志符号化工具

基于Python和Xcode symbolicatecrash工具构建的iOS崩溃日志可视化分析工具，支持Web界面和命令行两种使用方式。
大概长这样：
![image](https://github.com/user-attachments/assets/16a02e31-97e8-4203-8818-c3d974ca5659)


## 功能特性

- 🚀 **简单易用**: 支持拖拽上传，一键符号化
- 🔍 **可视化分析**: 清晰展示崩溃信息、线程堆栈和调用链
- 📱 **多格式支持**: 支持.ips、.crash文件和.dSYM符号文件
- 🔧 **命令行工具**: 支持批量处理和自动化集成
- 📊 **详细报告**: 生成JSON格式的分析结果
- 🌐 **Web界面**: 现代化的响应式Web界面
- 📁 **批量处理**: 支持多文件同时处理

## 系统要求

- macOS系统
- 已安装Xcode（包含symbolicatecrash工具）
- Python 3.7+

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd Crash_analysis
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 验证环境

确保symbolicatecrash工具可用：

```bash
xcrun --find symbolicatecrash
```

## 使用方法

### Web界面使用

1. 启动Web服务器：

```bash
# 推荐：智能启动（自动选择可用端口）
./start_smart.sh

# 或者：传统启动
./start.sh

# 或者：手动指定端口
python3 app.py --port 9000
```

2. 在浏览器中访问显示的地址（通常是 `http://localhost:9000`）

3. 上传IPS文件和dSYM文件，点击"开始分析"

4. 查看可视化的崩溃分析结果

### 命令行使用

#### 基本用法

```bash
# 处理单个文件
python cli.py -i crash.ips -d App.dSYM -o output/

# 处理多个文件
python cli.py -i "crashes/*.ips" -d "dsyms/*.dSYM" -o output/

# 使用ZIP压缩包中的dSYM
python cli.py -i crash.ips -d dsyms.zip -o output/

# 批量处理并显示详细信息
python cli.py -i "crashes/*.ips" -d dsyms/ -o output/ -v
```

#### 参数说明

- `-i, --input`: IPS文件路径，支持通配符模式
- `-d, --dsym`: dSYM文件或目录路径，可指定多个
- `-o, --output`: 输出目录路径
- `-v, --verbose`: 显示详细处理信息

### API接口

工具还提供RESTful API接口：

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ips_content": "崩溃日志内容",
    "dsym_paths": ["/path/to/app.dSYM"]
  }'
```

## 文件获取方式

### IPS文件获取

1. **Xcode Organizer**
   - 打开Xcode → Window → Organizer
   - 选择Crashes标签页
   - 选择对应的崩溃报告并导出

2. **设备设置**
   - 设置 → 隐私与安全 → 分析与改进 → 分析数据
   - 找到对应的崩溃文件

3. **App Store Connect**
   - 登录App Store Connect
   - 选择应用 → TestFlight → 崩溃

4. **TestFlight**
   - TestFlight应用内的崩溃报告

### dSYM文件获取

1. **Xcode Archive**
   - 在Xcode中Archive后
   - 右键Archive → Show in Finder
   - 进入.xcarchive包内容查找dSYMs文件夹

2. **App Store Connect**
   - 登录App Store Connect
   - 选择应用 → 构建版本
   - 下载dSYM文件

3. **CI/CD构建**
   - 从Jenkins、GitLab CI等构建系统获取
   - 通常在构建产物中

## 项目结构

```
Crash_analysis/
├── app.py                 # Flask Web应用主文件
├── cli.py                 # 命令行工具
├── requirements.txt       # Python依赖
├── README.md             # 项目文档
├── templates/            # HTML模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   └── result.html       # 结果页面
├── uploads/              # 上传文件临时目录
├── processed/            # 处理结果目录
└── static/               # 静态资源（如有）
```

## 输出结果

### 符号化日志
- 完整的符号化崩溃日志（.crash格式）
- 包含可读的函数名和行号信息

### 分析报告
- JSON格式的详细分析结果
- 包含应用信息、设备信息、异常类型等
- 结构化的线程堆栈信息

### 示例输出

```json
{
  "crash_info": {
    "app_name": "MyApp",
    "app_version": "1.0.0",
    "os_version": "iOS 15.0",
    "device_model": "iPhone13,2",
    "crash_time": "2024-01-15 10:30:00",
    "exception_type": "EXC_BAD_ACCESS",
    "exception_codes": "KERN_INVALID_ADDRESS",
    "crashed_thread": "0",
    "threads": [
      {
        "id": "0",
        "name": "Crashed",
        "crashed": true,
        "frames": [
          "0   MyApp    0x0000000104a8c000 -[ViewController viewDidLoad] + 64"
        ]
      }
    ]
  }
}
```

## 常见问题

### Q: 启动脚本报错怎么办？
A: 请按以下步骤排查：
```bash
# 1. 检查环境
./start.sh --check

# 2. 运行完整测试
python3 test_startup.py

# 3. 查看帮助信息
./start.sh --help
```

### Q: 符号化失败怎么办？
A: 请检查：
- dSYM文件与崩溃的应用版本是否匹配
- Xcode是否正确安装
- symbolicatecrash工具是否可用

### Q: 支持哪些文件格式？
A: 
- 崩溃文件：.ips、.crash
- 符号文件：.dSYM目录、.zip压缩包

### Q: 如何集成到CI/CD流程？
A: 使用命令行工具或API接口，可以轻松集成到自动化流程中。

### Q: 如何验证环境是否正确？
A: 运行以下命令进行全面检查：
```bash
# 快速环境检查
./start.sh --check

# 详细测试
python3 test_startup.py
```

## 技术实现

- **后端**: Python Flask框架
- **前端**: Bootstrap 5 + 原生JavaScript
- **符号化**: Xcode symbolicatecrash工具
- **文件处理**: Python标准库
- **可视化**: HTML/CSS/JavaScript

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本发布
- 支持Web界面和命令行工具
- 基本的符号化和可视化功能

---

**注意**: 确保dSYM文件与崩溃的应用版本完全匹配，这是符号化成功的关键。 
