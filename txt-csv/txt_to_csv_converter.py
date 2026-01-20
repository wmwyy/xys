#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT to CSV Converter for Geographic Survey Data (PyQt6 Version)

This script converts TXT files containing geographic survey data to CSV format.
The input TXT format contains milestone markers (K0+, K1+, K2+) followed by
coordinate points (distance, elevation).

Output CSV format: LZ,XSG,negative_milestone,distance,elevation
"""

import os
import sys
import csv
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QListWidget,
                             QLineEdit, QProgressBar, QTextEdit, QFileDialog,
                             QMessageBox, QGroupBox, QSplitter, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor


class ConversionWorker(QThread):
    """后台转换工作线程"""
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    conversion_finished = pyqtSignal(int, int)  # success_count, total_count

    def __init__(self, files, output_dir, converter, a_header='A', b_header='B', a_value='LZ', b_value='XSG'):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.converter = converter
        self.a_header = a_header
        self.b_header = b_header
        self.a_value = a_value
        self.b_value = b_value
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        success_count = 0
        total_files = len(self.files)

        for i, txt_file in enumerate(self.files):
            if self.is_cancelled:
                break
            # 生成CSV文件名
            base_name = os.path.splitext(os.path.basename(txt_file))[0]
            csv_file = os.path.join(self.output_dir, base_name + '.csv')

            if self.converter.convert_txt_to_csv(txt_file, csv_file, self.a_header, self.b_header, self.a_value, self.b_value):
                success_count += 1

            # 更新进度
            progress = int((i + 1) / total_files * 100)
            self.progress_updated.emit(progress)

        self.conversion_finished.emit(success_count, total_files)


class TxtToCsvConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.files = []
        self.worker = None

        self.init_ui()
        self.setup_styling()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("TXT转CSV转换工具")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 500)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 文件选择区域
        self.create_file_selection_group()
        main_layout.addWidget(self.file_group)

        # 输出目录选择
        self.create_output_group()
        main_layout.addWidget(self.output_group)

        # 控制按钮区域
        self.create_control_group()
        main_layout.addWidget(self.control_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 日志区域
        self.create_log_group()
        main_layout.addWidget(self.log_group, 1)  # 伸缩因子为1

        # 设置菜单栏
        self.create_menu_bar()

    def create_file_selection_group(self):
        """创建文件选择组"""
        self.file_group = QGroupBox("文件选择")
        layout = QVBoxLayout(self.file_group)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(120)
        layout.addWidget(self.file_list)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.add_files_btn = QPushButton("添加TXT文件")
        self.add_files_btn.clicked.connect(self.add_files)
        button_layout.addWidget(self.add_files_btn)

        self.remove_file_btn = QPushButton("移除选中")
        self.remove_file_btn.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.remove_file_btn)

        self.clear_list_btn = QPushButton("清空列表")
        self.clear_list_btn.clicked.connect(self.clear_list)
        button_layout.addWidget(self.clear_list_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def create_output_group(self):
        """创建输出目录组"""
        self.output_group = QGroupBox("输出目录")
        layout = QHBoxLayout(self.output_group)

        # 输出目录输入
        self.output_edit = QLineEdit(os.getcwd())
        layout.addWidget(self.output_edit)

        self.select_dir_btn = QPushButton("选择目录")
        self.select_dir_btn.clicked.connect(self.select_output_dir)
        layout.addWidget(self.select_dir_btn)

        # A/B 列单元值设置（例如 LZ / XSG）
        self.a_value_edit = QLineEdit("LZ")
        self.a_value_edit.setMaximumWidth(120)
        self.a_value_edit.setToolTip("设置CSV中A列的单元值 (默认: LZ)")
        layout.addWidget(self.a_value_edit)

        self.b_value_edit = QLineEdit("XSG")
        self.b_value_edit.setMaximumWidth(120)
        self.b_value_edit.setToolTip("设置CSV中B列的单元值 (默认: XSG)")
        layout.addWidget(self.b_value_edit)

    def create_control_group(self):
        """创建控制按钮组"""
        self.control_group = QWidget()
        layout = QHBoxLayout(self.control_group)

        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setMinimumHeight(35)
        self.convert_btn.clicked.connect(self.convert_files)
        layout.addWidget(self.convert_btn)

        self.cancel_btn = QPushButton("取消转换")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        self.cancel_btn.setEnabled(False)
        layout.addWidget(self.cancel_btn)

        # 提取 D 列按钮（去重，倒序）
        self.extract_d_btn = QPushButton("提取D列")
        self.extract_d_btn.setMinimumHeight(35)
        self.extract_d_btn.clicked.connect(self.extract_d_values)
        layout.addWidget(self.extract_d_btn)

        layout.addStretch()

    def create_log_group(self):
        """创建日志组"""
        self.log_group = QGroupBox("转换日志")
        layout = QVBoxLayout(self.log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        layout.addWidget(self.log_text)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        add_files_action = file_menu.addAction("添加TXT文件")
        add_files_action.triggered.connect(self.add_files)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def setup_styling(self):
        """设置样式"""
        # 设置应用程序样式
        self.setStyleSheet("""
            /* 全局背景与文字颜色 */
            QMainWindow {
                background-color: #f5f5f5;
                color: #222222; /* 主文本颜色，增强可读性 */
            }

            /* 分组框（标题、边框、背景） */
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                background-color: white;
                color: #222222;
            }

            /* 分组标题颜色稍微深一点 */
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #111111;
            }

            /* 按钮样式与文字颜色 */
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                color: #222222;
            }

            QPushButton:hover {
                background-color: #e6f3ff;
                border-color: #0078d4;
            }

            QPushButton:pressed {
                background-color: #c7e4f7;
            }

            QPushButton:disabled {
                background-color: #f3f2f1;
                color: #8f8f8f;
                border-color: #edebe9;
            }

            /* 单行输入框文字颜色 */
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                font-size: 13px;
                color: #222222;
            }

            QLineEdit:focus {
                border-color: #0078d4;
            }

            /* 列表项与替代背景色 */
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                color: #222222;
            }

            QListWidget::item {
                color: #222222;
            }

            QListWidget::item:selected {
                background: #e6f3ff;
                color: #071325;
            }

            /* 进度条 */
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: white;
                color: #222222;
            }

            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }

            /* 文本日志区域 */
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                color: #222222;
            }

            /* 菜单与弹窗文字颜色 */
            QMenuBar, QMenu, QLabel {
                color: #222222;
            }

            /* 对话框与消息框使用浅背景和深色文字，避免深色系统主题导致不可见 */
            QDialog, QMessageBox, QMessageBox QLabel {
                background-color: #ffffff;
                color: #111111;
            }
        """)

    def add_files(self):
        """添加TXT文件到列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择TXT文件",
            "",
            "TXT files (*.txt);;All files (*.*)"
        )

        for file_path in files:
            if file_path not in self.files:
                self.files.append(file_path)
                self.file_list.addItem(os.path.basename(file_path))

        self.update_convert_button()

    def remove_selected(self):
        """移除选中的文件"""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            self.file_list.takeItem(current_row)
            del self.files[current_row]

        self.update_convert_button()

    def clear_list(self):
        """清空文件列表"""
        self.file_list.clear()
        self.files.clear()
        self.update_convert_button()

    def select_output_dir(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_edit.setText(directory)

    def log(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

        # 强制更新界面
        QApplication.processEvents()

    def log_html(self, html):
        """以 HTML 格式添加日志消息（用于强调成功/错误）"""
        try:
            self.log_text.insertHtml(html + "<br>")
            # 移动到末尾
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
        except Exception:
            # 回退到纯文本输出
            self.log(str(html))
        QApplication.processEvents()

    def update_convert_button(self):
        """更新转换按钮状态"""
        enabled = len(self.files) > 0
        self.convert_btn.setEnabled(enabled)
        self.convert_btn.setText(f"开始转换 ({len(self.files)} 个文件)" if enabled else "开始转换")

    def extract_d_values(self):
        """从选中的TXT文件中提取 D 列（去重，倒序）并保存到输出目录的文件中"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先选择要提取的TXT文件")
            return

        output_dir = self.output_edit.text()
        if not os.path.exists(output_dir):
            QMessageBox.critical(self, "错误", "输出目录不存在")
            return

        unique_d = set()

        for txt_file in self.files:
            try:
                # 尝试多种编码读取
                encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin1']
                lines = None
                for encoding in encodings:
                    try:
                        with open(txt_file, 'r', encoding=encoding) as f:
                            lines = f.readlines()
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue

                if lines is None:
                    self.log(f"警告: 无法读取文件 {os.path.basename(txt_file)} 的内容")
                    continue

                current_milestone = 0.0
                for line in lines[1:]:
                    sline = line.strip().replace('\u00A0', ' ').replace('\u3000', ' ')
                    if not sline:
                        continue
                    # 规范全角数字与符号
                    trans_map = {ord('０')+i: ord('0')+i for i in range(10)}
                    trans_map.update({ord('＋'): ord('+'), ord('－'): ord('-'), ord('．'): ord('.'), ord('，'): ord(',')})
                    sline = sline.translate(trans_map)
                    if re.match(r'^[Kk]?\d+\+\d', sline):
                        current_milestone = self.parse_milestone(sline)
                    else:
                        parts = re.split(r'[\t,;，；\s]+', sline)
                        nums = []
                        for p in parts:
                            pclean = p.replace(',', '').replace(' ', '')
                            try:
                                nums.append(float(pclean))
                            except Exception:
                                continue
                            if len(nums) >= 2:
                                break
                        if len(nums) >= 2:
                            unique_d.add(round(-current_milestone, 6))
            except Exception as e:
                self.log(f"错误读取 {os.path.basename(txt_file)}: {e}")

        if not unique_d:
            QMessageBox.information(self, "结果", "未找到任何 D 值")
            return

        # 倒序排序并写入文件
        sorted_d = sorted(unique_d, reverse=True)
        out_path = os.path.join(output_dir, "D_values_unique.txt")
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                for v in sorted_d:
                    f.write(f"{v}\n")
            self.log(f"已提取 {len(sorted_d)} 个唯一 D 值，保存到 {out_path}")
            # 弹窗展示前 50 个值
            preview = "\\n".join(str(x) for x in sorted_d[:50])
            QMessageBox.information(self, "提取完成", f"共提取 {len(sorted_d)} 个唯一 D 值，已保存为:\n{out_path}\n\n前50个值:\n{preview}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法保存文件: {e}")

    def parse_milestone(self, milestone_str):
        """解析里程桩号，返回数值"""
        # 匹配 K0+042.55 或 0+001 等格式，支持可选的前缀 K 或 k
        s = milestone_str.strip()
        # 支持半角或全角加号
        s = s.replace('＋', '+')
        match = re.search(r'^[Kk]?(\d+)\+(\d+\.?\d*)', s)
        if match:
            km = int(match.group(1))
            meters = float(match.group(2))
            return km * 1000 + meters
        return 0.0

    def convert_txt_to_csv(self, txt_file, csv_file, a_header='A', b_header='B', a_value='LZ', b_value='XSG'):
        """将单个TXT文件转换为CSV文件"""
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin1']
            lines = None

            for encoding in encodings:
                try:
                    with open(txt_file, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    break
                except (UnicodeDecodeError, UnicodeError, ValueError):
                    # 有些编码（例如 utf-16）在没有 BOM 时会抛出 ValueError/UnicodeError
                    continue

            if lines is None:
                raise Exception("无法用任何支持的编码读取文件")

            # 清理编码问题的数据
            cleaned_lines = []
            for line in lines:
                # 将无法解码的字符替换为问号
                cleaned_line = line.encode('utf-8', errors='replace').decode('utf-8')
                cleaned_lines.append(cleaned_line)

            csv_data = []
            current_milestone = 0.0

            # 跳过第一行标题
            for line in cleaned_lines[1:]:
                line = line.strip()
                if not line:
                    continue

                if re.match(r'^[Kk]?\d+\+\d', line):
                    # 里程桩号行
                    current_milestone = self.parse_milestone(line)
                else:
                    # 坐标数据行
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            distance = float(parts[0])
                            elevation = float(parts[1])
                            # 转换为CSV格式：A_value,B_value,K, D(=-K), C(distance), Y(elevation)
                            csv_data.append([a_value, b_value, current_milestone, -current_milestone, distance, elevation])
                        except ValueError:
                            self.log(f"警告: 无法解析数据行 '{line}'")

            # 写入CSV文件
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 写入标题，增加K列；使用实际写入的数据值作为列头
                writer.writerow([a_value, b_value, 'K', 'D', 'C', 'Y'])
                # 写入数据：A,B为配置值；K为里程数值，D为-里程，C为distance，Y为elevation
                writer.writerows(csv_data)

            # 使用明显样式记录成功（更深更明显的颜色）
            self.log_html(f"<span style='color:#002b00; font-weight:bold; font-size:13px;'>成功转换: {os.path.basename(txt_file)} -> {os.path.basename(csv_file)}</span>")
            return True

        except Exception as e:
            self.log_html(f"<span style='color:#a80000; font-weight:bold;'>错误转换 {os.path.basename(txt_file)}: {str(e)}</span>")
            return False

    def convert_files(self):
        """开始转换文件"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先选择要转换的TXT文件")
            return

        output_dir = self.output_edit.text()
        if not os.path.exists(output_dir):
            QMessageBox.critical(self, "错误", "输出目录不存在")
            return

        # 禁用按钮，显示进度条
        self.set_conversion_state(True)

        # 清空日志
        self.log_text.clear()

        # 创建并启动工作线程，传入当前 A/B 列 名称与 单元值（默认使用 a_value/b_value 作为列名）
        a_value = self.a_value_edit.text().strip() or 'LZ'
        b_value = self.b_value_edit.text().strip() or 'XSG'
        # 使用 A/B 单元值同时作为列头（方便用户期望的行为）
        a_header = a_value
        b_header = b_value
        self.worker = ConversionWorker(self.files.copy(), output_dir, self, a_header, b_header, a_value, b_value)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.log_updated.connect(self.log)
        self.worker.conversion_finished.connect(self.on_conversion_finished)
        self.worker.start()

    def cancel_conversion(self):
        """取消转换"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log("正在取消转换...")
            self.cancel_btn.setEnabled(False)

    def on_conversion_finished(self, success_count, total_count):
        """转换完成处理"""
        self.set_conversion_state(False)
        self.worker = None
        # 更醒目的完成提示
        self.log_html(f"<div style='font-weight:bold; color:#004085;'>\\n转换完成! 成功: {success_count}/{total_count}</div>")

        # 显示结果对话框
        if success_count == total_count:
            QMessageBox.information(self, "完成",
                                  f"转换完成!\n成功转换了 {success_count} 个文件")
        else:
            QMessageBox.warning(self, "完成",
                              f"转换完成!\n成功: {success_count}/{total_count} 个文件")
        # 自动提取已禁用：仅保留手动触发（避免非预期弹窗）

    def set_conversion_state(self, converting):
        """设置转换状态"""
        self.convert_btn.setEnabled(not converting)
        self.cancel_btn.setEnabled(converting)
        self.progress_bar.setVisible(converting)

        if not converting:
            self.progress_bar.setValue(0)

        # 禁用/启用其他控件
        self.add_files_btn.setEnabled(not converting)
        self.remove_file_btn.setEnabled(not converting)
        self.clear_list_btn.setEnabled(not converting)
        self.select_dir_btn.setEnabled(not converting)
        self.file_list.setEnabled(not converting)
        self.output_edit.setEnabled(not converting)

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>TXT转CSV转换工具</h2>
        <p>版本: 2.0 (PyQt6)</p>
        <p>用于将地理测量数据从TXT格式转换为CSV格式</p>
        <p>支持批量转换，自动编码检测</p>
        <br>
        <p>© 2024 TXT to CSV Converter</p>
        """
        QMessageBox.about(self, "关于", about_text)

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "转换正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.worker.wait()  # 等待线程结束
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class TestConverter:
    """独立的测试转换器，不依赖GUI"""

    def parse_milestone(self, milestone_str):
        """解析里程桩号，返回数值"""
        # 匹配 K0+042.55 这样的格式（TestConverter 版本） - 支持可选 K/k 和全角加号
        s = milestone_str.strip()
        s = s.replace('＋', '+')
        match = re.search(r'^[Kk]?(\d+)\+(\d+\.?\d*)', s)
        if match:
            km = int(match.group(1))
            meters = float(match.group(2))
            return km * 1000 + meters
        return 0.0

    def convert_txt_to_csv(self, txt_file, csv_file, a_header='A', b_header='B', a_value='LZ', b_value='XSG'):
        """将单个TXT文件转换为CSV文件"""
        try:
            # 尝试不同的编码（回退为原始列表）
            encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin1']
            lines = None

            for encoding in encodings:
                try:
                    with open(txt_file, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue

            if lines is None:
                raise Exception("无法用任何支持的编码读取文件")

            # 清理编码问题的数据
            cleaned_lines = []
            for line in lines:
                # 将无法解码的字符替换为问号
                cleaned_line = line.encode('utf-8', errors='replace').decode('utf-8')
                cleaned_lines.append(cleaned_line)

            csv_data = []
            current_milestone = 0.0

            # 跳过第一行标题
            for line in cleaned_lines[1:]:
                line = line.strip()
                if not line:
                    continue

                if re.match(r'^[Kk]?\d+\+\d', line):
                    current_milestone = self.parse_milestone(line)
                else:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            distance = float(parts[0])
                            elevation = float(parts[1])
                            csv_data.append([a_value, b_value, current_milestone, -current_milestone, distance, elevation])
                        except ValueError:
                            print(f"警告: 无法解析数据行 '{line}'")

            # 写入CSV文件
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([a_value, b_value, 'K', 'D', 'C', 'Y'])
                writer.writerows(csv_data)

            print(f"成功转换: {os.path.basename(txt_file)} -> {os.path.basename(csv_file)}")
            return True

        except Exception as e:
            print(f"错误转换 {os.path.basename(txt_file)}: {str(e)}")
            return False


def test_conversion():
    """命令行测试函数"""
    converter = TestConverter()
    # 修改为更灵活的测试：如果存在下游/下(1)文件则优先测试，否则使用上.txt
    if os.path.exists("2026.1.13小砂沟下(1).txt"):
        txt_file = "2026.1.13小砂沟下(1).txt"
    else:
        txt_file = "2026.1.13小砂沟上.txt"
    csv_file = "test_output_pyqt6.csv"

    print("开始测试TXT到CSV转换 (PyQt6版本)...")

    if os.path.exists(txt_file):
        success = converter.convert_txt_to_csv(txt_file, csv_file)
        if success:
            print(f"转换成功! 输出文件: {csv_file}")

            # 读取并显示前几行结果
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:10]
                print("输出文件前10行:")
                for line in lines:
                    print(line.strip())
            except Exception as e:
                print(f"读取输出文件失败: {e}")
        else:
            print("转换失败")
    else:
        print(f"测试文件不存在: {txt_file}")


def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_conversion()
    else:
        app = QApplication(sys.argv)

        # 设置应用程序信息
        app.setApplicationName("TXT转CSV转换工具")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("Converter Tools")

        # 创建主窗口
        window = TxtToCsvConverter()
        window.show()

        # 运行应用程序
        sys.exit(app.exec())


if __name__ == "__main__":
    main()