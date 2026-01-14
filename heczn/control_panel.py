#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HEC-RAS 中文覆盖层控制面板

提供图形界面来控制覆盖层程序
- 启动/停止覆盖层
- 运行鼠标坐标显示器
- 编辑配置文件
- 查看状态信息
"""

import sys
import json
import os
import subprocess
import signal
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QMessageBox,
    QStatusBar, QSplitter, QFrame
)
from PySide6.QtWidgets import QComboBox, QSpinBox
from PySide6.QtCore import Qt, QTimer, QProcess, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor


class ProcessMonitor(QThread):
    """进程监控线程"""
    status_updated = Signal(str, bool)  # 进程名, 是否运行中

    def __init__(self, processes):
        super().__init__()
        self.processes = processes
        self.running = True

    def run(self):
        while self.running:
            for name, process in self.processes.items():
                if process and process.state() == QProcess.Running:
                    self.status_updated.emit(name, True)
                else:
                    self.status_updated.emit(name, False)
            self.sleep(1)

    def stop(self):
        self.running = False


class ControlPanel(QMainWindow):
    """控制面板主窗口"""

    def __init__(self):
        super().__init__()
        self.overlay_process = None
        self.ocr_process = None
        self.auto_process = None
        self.mouse_process = None
        self.process_monitor = None

        self.config_file = Path(__file__).parent / "labels.json"
        self.overlay_script = Path(__file__).parent / "overlay_macos.py"
        self.mouse_script = Path(__file__).parent / "mouse_pos_macos.py"

        self.init_ui()
        self.setup_monitor()
        self.load_config_info()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("HEC-RAS 中文覆盖层控制面板")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # 始终置顶

        # 设置窗口图标和样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QLabel {
                font-size: 11px;
            }
        """)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("HEC-RAS 中文界面覆盖层控制面板")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin: 10px;
            }
        """)
        main_layout.addWidget(title_label)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧控制面板
        control_widget = self.create_control_panel()
        splitter.addWidget(control_widget)

        # 右侧信息面板
        info_widget = self.create_info_panel()
        splitter.addWidget(info_widget)

        splitter.setSizes([400, 400])
        main_layout.addWidget(splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 设置菜单栏
        self.create_menu_bar()

    def create_control_panel(self):
        """创建控制面板"""
        control_group = QGroupBox("控制操作")
        layout = QVBoxLayout(control_group)

        # 覆盖层控制
        overlay_group = QGroupBox("覆盖层控制")
        overlay_layout = QVBoxLayout(overlay_group)

        self.overlay_status_label = QLabel("状态: 未运行")
        self.overlay_status_label.setStyleSheet("color: red;")
        overlay_layout.addWidget(self.overlay_status_label)

        overlay_buttons_layout = QHBoxLayout()
        self.start_overlay_btn = QPushButton("启动覆盖层")
        self.start_overlay_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.start_overlay_btn.clicked.connect(self.start_overlay)

        self.stop_overlay_btn = QPushButton("停止覆盖层")
        self.stop_overlay_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.stop_overlay_btn.clicked.connect(self.stop_overlay)
        self.stop_overlay_btn.setEnabled(False)

        overlay_buttons_layout.addWidget(self.start_overlay_btn)
        overlay_buttons_layout.addWidget(self.stop_overlay_btn)
        overlay_layout.addLayout(overlay_buttons_layout)

        layout.addWidget(overlay_group)

        # 鼠标坐标显示器控制
        mouse_group = QGroupBox("鼠标坐标显示器")
        mouse_layout = QVBoxLayout(mouse_group)

        self.mouse_status_label = QLabel("状态: 未运行")
        self.mouse_status_label.setStyleSheet("color: red;")
        mouse_layout.addWidget(self.mouse_status_label)

        mouse_buttons_layout = QHBoxLayout()
        self.start_mouse_btn = QPushButton("启动坐标显示器")
        self.start_mouse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.start_mouse_btn.clicked.connect(self.start_mouse_pos)

        self.stop_mouse_btn = QPushButton("停止坐标显示器")
        self.stop_mouse_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        self.stop_mouse_btn.clicked.connect(self.stop_mouse_pos)
        self.stop_mouse_btn.setEnabled(False)

        mouse_buttons_layout.addWidget(self.start_mouse_btn)
        mouse_buttons_layout.addWidget(self.stop_mouse_btn)
        mouse_layout.addLayout(mouse_buttons_layout)

        layout.addWidget(mouse_group)

        # 配置文件操作
        config_group = QGroupBox("配置文件操作")
        config_layout = QVBoxLayout(config_group)

        edit_config_btn = QPushButton("编辑配置文件")
        edit_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        edit_config_btn.clicked.connect(self.edit_config)
        config_layout.addWidget(edit_config_btn)

        reload_config_btn = QPushButton("重新加载配置")
        reload_config_btn.clicked.connect(self.reload_config)
        config_layout.addWidget(reload_config_btn)

        layout.addWidget(config_group)
        # OCR 覆盖层控制
        ocr_group = QGroupBox("OCR 翻译覆盖层")
        ocr_layout = QVBoxLayout(ocr_group)

        self.ocr_status_label = QLabel("状态: 未运行")
        self.ocr_status_label.setStyleSheet("color: red;")
        ocr_layout.addWidget(self.ocr_status_label)

        ocr_buttons = QHBoxLayout()
        self.start_ocr_btn = QPushButton("启动 OCR 覆盖层")
        self.start_ocr_btn.setStyleSheet("background-color: #16a085; color: white;")
        self.start_ocr_btn.clicked.connect(self.start_ocr_overlay)
        ocr_buttons.addWidget(self.start_ocr_btn)

        self.stop_ocr_btn = QPushButton("停止 OCR 覆盖层")
        self.stop_ocr_btn.setStyleSheet("background-color: #c0392b; color: white;")
        self.stop_ocr_btn.clicked.connect(self.stop_ocr_overlay)
        self.stop_ocr_btn.setEnabled(False)
        ocr_buttons.addWidget(self.stop_ocr_btn)

        ocr_layout.addLayout(ocr_buttons)
        layout.addWidget(ocr_group)
        # 自动翻译覆盖层控制
        auto_group = QGroupBox("自动翻译覆盖层")
        auto_layout = QVBoxLayout(auto_group)

        self.auto_status_label = QLabel("状态: 未运行")
        self.auto_status_label.setStyleSheet("color: red;")
        auto_layout.addWidget(self.auto_status_label)

        auto_btns = QHBoxLayout()
        self.start_auto_btn = QPushButton("启动自动覆盖")
        self.start_auto_btn.setStyleSheet("background-color: #8e44ad; color: white;")
        self.start_auto_btn.clicked.connect(self.start_auto_overlay)
        auto_btns.addWidget(self.start_auto_btn)

        self.stop_auto_btn = QPushButton("停止自动覆盖")
        self.stop_auto_btn.setEnabled(False)
        self.stop_auto_btn.setStyleSheet("background-color: #7f8c8d; color: white;")
        self.stop_auto_btn.clicked.connect(self.stop_auto_overlay)
        auto_btns.addWidget(self.stop_auto_btn)

        auto_layout.addLayout(auto_btns)
        layout.addWidget(auto_group)
        # 标签定位与高亮
        locate_group = QGroupBox("标签定位")
        locate_layout = QVBoxLayout(locate_group)

        hl_row = QHBoxLayout()
        self.label_combo = QComboBox()
        self.label_combo.setEditable(False)
        hl_row.addWidget(self.label_combo)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(200, 10000)
        self.duration_spin.setValue(2000)
        self.duration_spin.setSuffix(" ms")
        hl_row.addWidget(self.duration_spin)

        locate_layout.addLayout(hl_row)

        hl_btn_row = QHBoxLayout()
        self.highlight_btn = QPushButton("高亮并定位")
        self.highlight_btn.setStyleSheet("background-color: #f39c12; color: white;")
        self.highlight_btn.clicked.connect(self.highlight_selected_label)
        hl_btn_row.addWidget(self.highlight_btn)

        locate_layout.addLayout(hl_btn_row)
        layout.addWidget(locate_group)

        # 退出按钮
        exit_btn = QPushButton("退出控制面板")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)

        layout.addStretch()
        return control_group

    def create_info_panel(self):
        """创建信息面板"""
        info_group = QGroupBox("信息面板")
        layout = QVBoxLayout(info_group)

        # 配置信息
        config_info_group = QGroupBox("配置文件信息")
        config_info_layout = QVBoxLayout(config_info_group)

        self.config_info_text = QTextEdit()
        self.config_info_text.setReadOnly(True)
        self.config_info_text.setMaximumHeight(150)
        config_info_layout.addWidget(self.config_info_text)

        layout.addWidget(config_info_group)

        # 日志信息
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        return info_group

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件')

        exit_action = file_menu.addAction('退出')
        exit_action.triggered.connect(self.close)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')

        about_action = help_menu.addAction('关于')
        about_action.triggered.connect(self.show_about)

        usage_action = help_menu.addAction('使用说明')
        usage_action.triggered.connect(self.show_usage)

    def setup_monitor(self):
        """设置进程监控"""
        self.process_monitor = ProcessMonitor({
            'overlay': self.overlay_process,
            'mouse_pos': self.mouse_process,
            'ocr': self.ocr_process,
            'auto': self.auto_process
        })
        self.process_monitor.status_updated.connect(self.update_status)
        self.process_monitor.start()

    def update_status(self, process_name, is_running):
        """更新进程状态显示"""
        if process_name == 'overlay':
            if is_running:
                self.overlay_status_label.setText("状态: 运行中")
                self.overlay_status_label.setStyleSheet("color: green;")
                self.start_overlay_btn.setEnabled(False)
                self.stop_overlay_btn.setEnabled(True)
            else:
                self.overlay_status_label.setText("状态: 未运行")
                self.overlay_status_label.setStyleSheet("color: red;")
                self.start_overlay_btn.setEnabled(True)
                self.stop_overlay_btn.setEnabled(False)

        elif process_name == 'mouse_pos':
            if is_running:
                self.mouse_status_label.setText("状态: 运行中")
                self.mouse_status_label.setStyleSheet("color: green;")
                self.start_mouse_btn.setEnabled(False)
                self.stop_mouse_btn.setEnabled(True)
            else:
                self.mouse_status_label.setText("状态: 未运行")
                self.mouse_status_label.setStyleSheet("color: red;")
                self.start_mouse_btn.setEnabled(True)
                self.stop_mouse_btn.setEnabled(False)
        elif process_name == 'ocr':
            if is_running:
                self.ocr_status_label.setText("状态: 运行中")
                self.ocr_status_label.setStyleSheet("color: green;")
                self.start_ocr_btn.setEnabled(False)
                self.stop_ocr_btn.setEnabled(True)
            else:
                self.ocr_status_label.setText("状态: 未运行")
                self.ocr_status_label.setStyleSheet("color: red;")
                self.start_ocr_btn.setEnabled(True)
                self.stop_ocr_btn.setEnabled(False)
        elif process_name == 'auto':
            if is_running:
                self.auto_status_label.setText("状态: 运行中")
                self.auto_status_label.setStyleSheet("color: green;")
                self.start_auto_btn.setEnabled(False)
                self.stop_auto_btn.setEnabled(True)
            else:
                self.auto_status_label.setText("状态: 未运行")
                self.auto_status_label.setStyleSheet("color: red;")
                self.start_auto_btn.setEnabled(True)
                self.stop_auto_btn.setEnabled(False)

    def start_overlay(self):
        """启动覆盖层"""
        try:
            if self.overlay_process and self.overlay_process.state() == QProcess.Running:
                QMessageBox.warning(self, "警告", "覆盖层已在运行中！")
                return

            self.overlay_process = QProcess()
            self.overlay_process.setWorkingDirectory(str(self.overlay_script.parent))
            self.overlay_process.start(sys.executable, [str(self.overlay_script)])

            if self.overlay_process.waitForStarted(3000):
                self.log_message("覆盖层已启动")
                self.status_bar.showMessage("覆盖层启动成功")
                # 重新启动监控
                self.restart_monitor()
            else:
                error = self.overlay_process.errorString()
                QMessageBox.critical(self, "错误", f"启动覆盖层失败: {error}")
                self.log_message(f"启动覆盖层失败: {error}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动覆盖层时发生异常: {str(e)}")
            self.log_message(f"启动覆盖层异常: {str(e)}")

    def stop_overlay(self):
        """停止覆盖层"""
        try:
            if self.overlay_process and self.overlay_process.state() == QProcess.Running:
                self.overlay_process.terminate()
                if self.overlay_process.waitForFinished(3000):
                    self.log_message("覆盖层已停止")
                    self.status_bar.showMessage("覆盖层已停止")
                else:
                    self.overlay_process.kill()
                    self.log_message("覆盖层已被强制终止")
                # 重新启动监控
                self.restart_monitor()
            else:
                QMessageBox.information(self, "提示", "覆盖层未在运行")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止覆盖层时发生异常: {str(e)}")

    def start_mouse_pos(self):
        """启动鼠标坐标显示器"""
        try:
            if self.mouse_process and self.mouse_process.state() == QProcess.Running:
                QMessageBox.warning(self, "警告", "鼠标坐标显示器已在运行中！")
                return

            self.mouse_process = QProcess()
            self.mouse_process.setWorkingDirectory(str(self.mouse_script.parent))
            self.mouse_process.start(sys.executable, [str(self.mouse_script)])

            if self.mouse_process.waitForStarted(3000):
                self.log_message("鼠标坐标显示器已启动")
                self.status_bar.showMessage("坐标显示器启动成功")
                # 重新启动监控
                self.restart_monitor()
            else:
                error = self.mouse_process.errorString()
                QMessageBox.critical(self, "错误", f"启动坐标显示器失败: {error}")
                self.log_message(f"启动坐标显示器失败: {error}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动坐标显示器时发生异常: {str(e)}")
            self.log_message(f"启动坐标显示器异常: {str(e)}")

    def stop_mouse_pos(self):
        """停止鼠标坐标显示器"""
        try:
            if self.mouse_process and self.mouse_process.state() == QProcess.Running:
                self.mouse_process.terminate()
                if self.mouse_process.waitForFinished(3000):
                    self.log_message("鼠标坐标显示器已停止")
                    self.status_bar.showMessage("坐标显示器已停止")
                else:
                    self.mouse_process.kill()
                    self.log_message("鼠标坐标显示器已被强制终止")
                # 重新启动监控
                self.restart_monitor()
            else:
                QMessageBox.information(self, "提示", "鼠标坐标显示器未在运行")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止坐标显示器时发生异常: {str(e)}")

    def start_ocr_overlay(self):
        """启动 OCR 翻译覆盖层"""
        try:
            if self.ocr_process and self.ocr_process.state() == QProcess.Running:
                QMessageBox.warning(self, "警告", "OCR 覆盖层已在运行中！")
                return

            self.ocr_process = QProcess()
            self.ocr_process.setWorkingDirectory(str(self.overlay_script.parent))
            self.ocr_process.start(sys.executable, [str(self.overlay_script.parent / "overlay_ocr_translate.py")])

            if self.ocr_process.waitForStarted(3000):
                self.log_message("OCR 覆盖层已启动")
                self.status_bar.showMessage("OCR 覆盖层启动成功")
                # 重新启动监控
                self.restart_monitor()
            else:
                error = self.ocr_process.errorString()
                QMessageBox.critical(self, "错误", f"启动 OCR 覆盖层失败: {error}")
                self.log_message(f"启动 OCR 覆盖层失败: {error}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动 OCR 覆盖层时发生异常: {str(e)}")
            self.log_message(f"启动 OCR 覆盖层异常: {str(e)}")

    def stop_ocr_overlay(self):
        """停止 OCR 覆盖层"""
        try:
            if self.ocr_process and self.ocr_process.state() == QProcess.Running:
                self.ocr_process.terminate()
                if self.ocr_process.waitForFinished(3000):
                    self.log_message("OCR 覆盖层已停止")
                    self.status_bar.showMessage("OCR 覆盖层已停止")
                else:
                    self.ocr_process.kill()
                    self.log_message("OCR 覆盖层已被强制终止")
                # 重新启动监控
                self.restart_monitor()
            else:
                QMessageBox.information(self, "提示", "OCR 覆盖层未在运行")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止 OCR 覆盖层时发生异常: {str(e)}")
            self.log_message(f"停止 OCR 覆盖层异常: {str(e)}")

    def start_auto_overlay(self):
        """启动 自动翻译覆盖层"""
        try:
            if self.auto_process and self.auto_process.state() == QProcess.Running:
                QMessageBox.warning(self, "警告", "自动覆盖层已在运行中！")
                return

            self.auto_process = QProcess()
            self.auto_process.setWorkingDirectory(str(self.overlay_script.parent))
            self.auto_process.start(sys.executable, [str(self.overlay_script.parent / "overlay_auto_translate.py")])

            if self.auto_process.waitForStarted(3000):
                self.log_message("自动覆盖层已启动")
                self.status_bar.showMessage("自动覆盖层启动成功")
                # 重新启动监控
                self.restart_monitor()
            else:
                error = self.auto_process.errorString()
                QMessageBox.critical(self, "错误", f"启动自动覆盖层失败: {error}")
                self.log_message(f"启动自动覆盖层失败: {error}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动自动覆盖层时发生异常: {str(e)}")
            self.log_message(f"启动自动覆盖层异常: {str(e)}")

    def stop_auto_overlay(self):
        """停止 自动翻译覆盖层"""
        try:
            if self.auto_process and self.auto_process.state() == QProcess.Running:
                self.auto_process.terminate()
                if self.auto_process.waitForFinished(3000):
                    self.log_message("自动覆盖层已停止")
                    self.status_bar.showMessage("自动覆盖层已停止")
                else:
                    self.auto_process.kill()
                    self.log_message("自动覆盖层已被强制终止")
                # 重新启动监控
                self.restart_monitor()
            else:
                QMessageBox.information(self, "提示", "自动覆盖层未在运行")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止自动覆盖层时发生异常: {str(e)}")
            self.log_message(f"停止自动覆盖层异常: {str(e)}")

    def restart_monitor(self):
        """重启进程监控"""
        if self.process_monitor:
            self.process_monitor.stop()
            self.process_monitor.wait()

        self.process_monitor = ProcessMonitor({
            'overlay': self.overlay_process,
            'mouse_pos': self.mouse_process,
            'ocr': self.ocr_process,
            'auto': self.auto_process
        })
        self.process_monitor.status_updated.connect(self.update_status)
        self.process_monitor.start()

    def edit_config(self):
        """编辑配置文件"""
        try:
            # 尝试使用系统默认编辑器打开文件
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(self.config_file)])
            elif sys.platform == "linux":
                subprocess.run(["xdg-open", str(self.config_file)])
            else:
                # Windows或其他系统
                os.startfile(str(self.config_file))

            self.log_message("已打开配置文件进行编辑")
            self.status_bar.showMessage("配置文件已打开")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开配置文件: {str(e)}")
            self.log_message(f"打开配置文件失败: {str(e)}")

    def reload_config(self):
        """重新加载配置信息"""
        self.load_config_info()
        self.log_message("配置信息已重新加载")
        self.status_bar.showMessage("配置已重新加载")

    def highlight_selected_label(self):
        """写入 highlight.json 请求 overlay 高亮并定位指定标签"""
        try:
            idx = self.label_combo.currentData()
            if idx is None:
                QMessageBox.information(self, "提示", "请先选择一个标签")
                return

            duration = int(self.duration_spin.value())
            highlight_file = Path(__file__).parent / "highlight.json"
            payload = {"index": int(idx), "duration_ms": duration}
            with open(highlight_file, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            self.log_message(f"已写入 highlight.json: index={idx} duration={duration}ms")
            self.status_bar.showMessage("高亮请求已发送")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发送高亮请求失败: {e}")
            self.log_message(f"高亮请求失败: {e}")

    def load_config_info(self):
        """加载配置文件信息"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                info = f"配置文件: {self.config_file.name}\n"
                info += f"描述: {config.get('description', '无')}\n"
                info += f"版本: {config.get('version', '无')}\n"
                labels = config.get('labels', [])
                info += f"标签数量: {len(labels)}\n\n"

                # 显示前5个标签信息
                for i, label in enumerate(labels[:5]):
                    info += f"标签 {i+1}: {label.get('text', '')} "
                    rect = label.get('rect', [])
                    if rect:
                        info += f"位置: ({rect[0]}, {rect[1]}) 大小: {rect[2]}x{rect[3]}\n"
                    else:
                        info += "位置: 未设置\n"

                if len(labels) > 5:
                    info += f"\n... 还有 {len(labels) - 5} 个标签"

                self.config_info_text.setPlainText(info)
                # 填充标签下拉以供高亮选择
                try:
                    self.label_combo.clear()
                    for i, label in enumerate(labels):
                        text = label.get('text', f'标签 {i}')
                        self.label_combo.addItem(f"{i}: {text}", i)
                except Exception:
                    pass
            else:
                self.config_info_text.setPlainText("配置文件不存在")

        except Exception as e:
            self.config_info_text.setPlainText(f"加载配置信息失败: {str(e)}")

    def log_message(self, message):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "HEC-RAS 中文界面覆盖层控制面板 v1.0\n\n"
            "为运行在 Parallels 虚拟机中的 HEC-RAS 提供中文界面标注\n\n"
            "技术栈: Python + PySide6\n"
            "作者: AI Assistant"
        )

    def show_usage(self):
        """显示使用说明"""
        usage_text = """
        使用说明：

        1. 启动覆盖层：点击"启动覆盖层"按钮启动中文界面覆盖
        2. 获取坐标：点击"启动坐标显示器"获取鼠标位置坐标
        3. 编辑配置：点击"编辑配置文件"修改中文标签设置
        4. 重新加载：修改配置后点击"重新加载配置"刷新显示

        快捷键：
        - 覆盖层程序: Ctrl+Shift+Q 退出
        - 坐标显示器: Ctrl+Shift+Q 退出
        - 控制面板: 点击退出按钮或关闭窗口

        注意事项：
        - 确保 HEC-RAS 在覆盖层下方运行
        - 配置文件修改后会自动热更新
        - 鼠标操作完全穿透到底层程序
        """
        QMessageBox.information(self, "使用说明", usage_text)

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止所有进程
        try:
            if self.overlay_process and self.overlay_process.state() == QProcess.Running:
                self.overlay_process.terminate()
                self.overlay_process.waitForFinished(3000)

            if self.mouse_process and self.mouse_process.state() == QProcess.Running:
                self.mouse_process.terminate()
                self.mouse_process.waitForFinished(3000)
        except:
            pass

        # 停止监控线程
        if self.process_monitor:
            self.process_monitor.stop()
            self.process_monitor.wait()

        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("HEC-RAS 覆盖层控制面板")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("YYKF")

    # 创建控制面板
    panel = ControlPanel()
    panel.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())