#!/bin/bash

# TXT到CSV转换工具启动脚本 (PyQt6版本)

echo "======================================"
echo "    TXT到CSV转换工具"
echo "======================================"
echo ""

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3，请确保已安装Python 3"
    exit 1
fi

# 检查必要的文件是否存在
if [ ! -f "txt_to_csv_converter.py" ]; then
    echo "错误: 找不到主程序文件 txt_to_csv_converter.py"
    exit 1
fi

echo "正在启动转换工具..."
python3 txt_to_csv_converter.py

echo ""
echo "转换工具已关闭。"