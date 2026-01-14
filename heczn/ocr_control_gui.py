#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的 OCR 覆盖层控制 GUI

一键启动 / 停止 overlay_ocr_translate.py，并显示状态与基础配置选项。
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QCheckBox
)
from PySide6.QtCore import Qt, QProcess


class OCRControl(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR 翻译覆盖层 控制")
        self.setGeometry(200, 200, 360, 140)
        self.proc = None

        self.script_dir = Path(__file__).parent
        self.script = self.script_dir / "overlay_ocr_translate.py"

        layout = QVBoxLayout(self)

        self.status_label = QLabel("状态: 未运行")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("启动 OCR 覆盖层")
        self.start_btn.clicked.connect(self.start_overlay)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止 OCR 覆盖层")
        self.stop_btn.clicked.connect(self.stop_overlay)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.stop_btn)

        layout.addLayout(btn_row)

        opt_row = QHBoxLayout()
        self.stable_slider = QSlider(Qt.Horizontal)
        self.stable_slider.setRange(100, 1000)
        self.stable_slider.setValue(250)
        self.stable_slider.setToolTip("光标稳定阈值(ms)")
        opt_row.addWidget(QLabel("稳定(ms):"))
        opt_row.addWidget(self.stable_slider)
        layout.addLayout(opt_row)

        self.easyocr_cb = QCheckBox("允许 EasyOCR 回退（若 tesseract 不可用）")
        self.easyocr_cb.setChecked(True)
        layout.addWidget(self.easyocr_cb)

    def start_overlay(self):
        if self.proc and self.proc.state() == QProcess.Running:
            return
        self.proc = QProcess(self)
        self.proc.setWorkingDirectory(str(self.script_dir))
        self.proc.started.connect(self.on_started)
        self.proc.finished.connect(self.on_finished)
        self.proc.start(sys.executable, [str(self.script)])

    def stop_overlay(self):
        if self.proc and self.proc.state() == QProcess.Running:
            self.proc.terminate()
            self.proc.waitForFinished(3000)

    def on_started(self):
        self.status_label.setText("状态: 运行中")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def on_finished(self):
        self.status_label.setText("状态: 已停止")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    w = OCRControl()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

