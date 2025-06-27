#!/bin/bash

# iOS崩溃日志符号化工具启动脚本

# 检查参数
CHECK_ONLY=false
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "iOS崩溃日志符号化工具启动脚本"
    echo ""
    echo "用法: ./start.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -c, --check    仅检查环境，不启动服务器"
    echo "  -h, --help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./start.sh         # 启动Web服务器"
    echo "  ./start.sh --check # 仅检查环境"
    exit 0
elif [ "$1" = "--check" ] || [ "$1" = "-c" ]; then
    CHECK_ONLY=true
    echo "🔍 仅进行环境检查..."
else
    echo "🚀 启动iOS崩溃日志符号化工具..."
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查是否在macOS上运行
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  警告：此工具需要在macOS上运行，因为需要使用Xcode的symbolicatecrash工具"
fi

# 检查Xcode工具
if ! command -v xcrun &> /dev/null; then
    echo "❌ 未找到Xcode命令行工具，请先安装Xcode"
    exit 1
fi

# 检查symbolicatecrash工具
SYMBOLICATECRASH_PATH=""
POSSIBLE_PATHS=(
    "/Applications/Xcode.app/Contents/SharedFrameworks/DVTFoundation.framework/Versions/A/Resources/symbolicatecrash"
    "/Applications/Xcode.app/Contents/SharedFrameworks/AssetRuntime/DVTFoundation.framework/Versions/A/Resources/symbolicatecrash"
    "/usr/bin/symbolicatecrash"
    "/usr/local/bin/symbolicatecrash"
)

for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -f "$path" ]; then
        SYMBOLICATECRASH_PATH="$path"
        break
    fi
done

if [ -z "$SYMBOLICATECRASH_PATH" ]; then
    echo "❌ 未找到symbolicatecrash工具，请确保Xcode正确安装"
    echo "   尝试的路径："
    for path in "${POSSIBLE_PATHS[@]}"; do
        echo "   - $path"
    done
    exit 1
else
    echo "✅ 找到symbolicatecrash工具: $SYMBOLICATECRASH_PATH"
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 未找到requirements.txt文件"
    exit 1
fi

# 安装依赖（如果需要）
echo "📦 检查Python依赖..."
pip3 install -r requirements.txt --quiet

# 创建必要的目录
mkdir -p uploads processed

# 设置权限
chmod +x cli.py

echo "✅ 环境检查完成"

# 如果只是检查环境，则退出
if [ "$CHECK_ONLY" = true ]; then
    echo ""
    echo "🎉 环境检查通过！可以正常使用工具。"
    echo ""
    echo "💡 使用方法:"
    echo "   - 启动Web服务: ./start.sh"
    echo "   - 命令行工具: python3 cli.py --help"
    echo "   - 查看文档: cat README.md"
    exit 0
fi

echo ""
echo "🌐 启动Web服务器..."
echo "📱 请在浏览器中访问: http://localhost:9000"
echo ""
echo "💡 使用提示:"
echo "   - Web界面: 访问 http://localhost:9000"
echo "   - 命令行工具: python3 cli.py --help"
echo "   - API文档: 查看README.md"
echo "   - 自定义端口: python3 app.py --port 8000"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=================================="

# 启动Flask应用
python3 app.py 