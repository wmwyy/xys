#!/bin/bash

echo "打地鼠游戏启动中..."
echo ""
echo "请选择启动方式:"
echo "1. 使用Python HTTP服务器 (推荐)"
echo "2. 直接打开HTML文件"
echo ""

read -p "请选择 (1或2): " choice

case $choice in
    1)
        echo "正在启动Python HTTP服务器..."
        echo "服务器将在 http://localhost:8000 启动"
        echo "在浏览器中打开上述地址即可开始游戏"
        echo "按 Ctrl+C 停止服务器"
        echo ""
        cd "$(dirname "$0")"
        python3 -m http.server 8000
        ;;
    2)
        echo "正在打开HTML文件..."
        open index.html
        ;;
    *)
        echo "无效选择，请重新运行脚本"
        ;;
esac