#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鼠标坐标显示器 - HEC-RAS 界面覆盖层坐标辅助工具

功能：
- 实时显示鼠标在屏幕上的坐标
- 方便确定 labels.json 中的 rect 位置
- 快捷键 Ctrl+Shift+Q 退出
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont, QColor, QCursor, QKeySequence, QShortcut


class MousePosWindow(QWidget):
    """鼠标坐标显示窗口"""

    def __init__(self):
        super().__init__()
        self.pos_label = None
        self.timer = None

        self.init_window()
        self.setup_ui()
        self.setup_timer()
        self.setup_shortcuts()

    def init_window(self):
        """初始化窗口"""
        # 设置窗口大小和位置（右上角小窗口）
        self.setGeometry(1200, 50, 200, 80)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |  # 始终置顶
            Qt.FramelessWindowHint |   # 无边框
            Qt.Tool                    # 工具窗口
        )

        # 设置窗口透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("鼠标坐标显示器")

    def setup_ui(self):
        """设置UI"""
        # 创建坐标显示标签
        self.pos_label = QLabel("鼠标坐标: (0, 0)", self)
        self.pos_label.setGeometry(10, 10, 180, 30)

        # 设置字体和样式
        font = QFont("Menlo", 12)  # 等宽字体
        font.setBold(True)
        self.pos_label.setFont(font)

        # 设置标签样式（半透明背景）
        self.pos_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.8);
                border-radius: 5px;
                padding: 5px;
            }
        """)

        # 创建提示标签
        hint_label = QLabel("Ctrl+Shift+Q 退出", self)
        hint_label.setGeometry(10, 45, 180, 20)
        hint_label.setFont(QFont("PingFang SC", 10))
        hint_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                background-color: transparent;
            }
        """)

    def setup_timer(self):
        """设置定时器，实时更新坐标"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_mouse_pos)
        self.timer.start(50)  # 每50ms更新一次

    def update_mouse_pos(self):
        """更新鼠标位置显示"""
        # 获取全局鼠标位置
        global_pos = QCursor.pos()
        x, y = global_pos.x(), global_pos.y()

        # 更新显示
        self.pos_label.setText(f"鼠标坐标: ({x}, {y})")

    def setup_shortcuts(self):
        """设置快捷键"""
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Q"), self)
        quit_shortcut.activated.connect(self.quit_application)

    def quit_application(self):
        """退出应用"""
        print("鼠标坐标显示器已关闭")
        QApplication.quit()

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.timer:
            self.timer.stop()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("鼠标坐标显示器")
    app.setApplicationVersion("1.0.0")

    # 创建坐标显示窗口
    window = MousePosWindow()
    window.show()

    print("=" * 40)
    print("鼠标坐标显示器已启动")
    print("窗口将显示当前鼠标屏幕坐标")
    print("快捷键: Ctrl+Shift+Q 退出")
    print("使用此工具确定界面元素位置")
    print("=" * 40)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())