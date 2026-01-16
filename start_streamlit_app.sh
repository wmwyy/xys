#!/bin/bash

# Streamlit游戏中心启动脚本

echo "🎮 启动Streamlit游戏中心..."
echo "📱 支持电脑和手机端访问"
echo ""

# 检查Python和streamlit是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未找到，请先安装Python3"
    exit 1
fi

if ! python3 -c "import streamlit" &> /dev/null; then
    echo "❌ Streamlit未安装，正在尝试安装..."
    python3 -m pip install streamlit
fi

echo "✅ 环境检查完成"
echo ""

# 启动streamlit应用
echo "🚀 启动应用..."
echo "📍 应用将在浏览器中自动打开"
echo "📱 手机端访问：请在手机浏览器中输入显示的地址"
echo ""
echo "按 Ctrl+C 停止应用"
echo ""

python3 -m streamlit run streamlit_app.py --server.headless true --server.port 8501

echo ""
echo "👋 应用已停止"