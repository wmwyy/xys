#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口级自动 OCR 翻译覆盖层（macOS）

功能：
- 定时对整个屏幕（或可配置区域）进行 OCR（非悬停），识别英文文本并在对应位置叠加中文翻译
- 不拦截鼠标事件（点击仍穿透）
- 使用 pytesseract 获取文本和位置，使用 googletrans 翻译
- 支持最小置信度过滤、翻译缓存、热更新

使用：
  python3 overlay_auto_translate.py

注意：
 - 需要 macOS 屏幕录制权限（System Settings -> Privacy & Security -> Screen Recording）
 - 需要 tesseract + Python 依赖（见 requirements.txt）
"""

import sys
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import ImageGrab, Image, ImageOps
import pytesseract
from pytesseract import Output
from googletrans import Translator
import logging

from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPainter, QBrush

# logging
LOG_FILE = Path(__file__).parent / "ocr_auto.log"
logger = logging.getLogger("overlay_auto")
if not logger.handlers:
    h = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)


def ocr_fullscreen_data(region=None):
    """
    Capture screen (region tuple left,top,right,bottom or None for full)
    Return pytesseract.image_to_data dict
    """
    try:
        if region:
            img = ImageGrab.grab(bbox=region)
        else:
            img = ImageGrab.grab()
        img = img.convert("RGB")
        # basic preprocessing: autocontrast to improve readability
        try:
            img = ImageOps.autocontrast(img)
        except Exception:
            pass
        data = pytesseract.image_to_data(img, output_type=Output.DICT, lang="eng")
        return data, img.size
    except Exception as e:
        logger.exception("ocr_fullscreen_data failed")
        return None, (0, 0)


class AutoOverlayWindow(QWidget):
    def __init__(self, interval_ms=1500, min_confidence=50, region=None):
        super().__init__()
        self.interval_ms = interval_ms
        self.min_confidence = min_confidence
        self.region = region  # screen bbox or None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.pending = None
        self.translate_cache = {}
        self.translator = Translator()

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        # container for overlay labels: map id -> QLabel
        self.overlays = {}

        # periodic timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.schedule_ocr)
        self.timer.start(self.interval_ms)

        logger.info(f"AutoOverlayWindow started interval={self.interval_ms}ms min_conf={self.min_confidence}")

    def schedule_ocr(self):
        try:
            if self.pending and not self.pending.done():
                logger.debug("OCR pending; skip this tick")
                return
            self.pending = self.executor.submit(ocr_fullscreen_data, self.region)
            def cb(fut):
                try:
                    data, size = fut.result()
                except Exception:
                    data, size = None, (0,0)
                QTimer.singleShot(0, lambda: self.handle_ocr_result(data, size))
            self.pending.add_done_callback(cb)
        except Exception:
            logger.exception("Failed to schedule ocr")

    def handle_ocr_result(self, data, size):
        if not data:
            logger.debug("No OCR data")
            return
        # Group words by (block_num, par_num, line_num) to form lines
        texts = data.get('text', [])
        n = len(texts)
        groups = {}
        for i in range(n):
            text = (texts[i] or "").strip()
            if not text:
                continue
            try:
                conf = int(float(data['conf'][i]))
            except Exception:
                conf = 0
            block = data.get('block_num', [None]*n)[i]
            par = data.get('par_num', [None]*n)[i]
            line = data.get('line_num', [None]*n)[i]
            key = (block, par, line)
            left = int(data.get('left', [0]*n)[i])
            top = int(data.get('top', [0]*n)[i])
            w = int(data.get('width', [0]*n)[i])
            h = int(data.get('height', [0]*n)[i])
            if key not in groups:
                groups[key] = {
                    'texts': [text],
                    'confs': [conf],
                    'left': left,
                    'top': top,
                    'right': left + w,
                    'bottom': top + h
                }
            else:
                g = groups[key]
                g['texts'].append(text)
                g['confs'].append(conf)
                g['left'] = min(g['left'], left)
                g['top'] = min(g['top'], top)
                g['right'] = max(g['right'], left + w)
                g['bottom'] = max(g['bottom'], top + h)

        seen_keys = set()
        for key, g in groups.items():
            avg_conf = int(sum(g['confs']) / max(1, len(g['confs'])))
            if avg_conf < self.min_confidence:
                continue
            text = " ".join(g['texts'])
            x = g['left']
            y = g['top']
            w = g['right'] - g['left']
            h = g['bottom'] - g['top']
            gkey = (x, y, w, h, text)
            seen_keys.add(gkey)

            if gkey in self.overlays:
                continue
            # translate (cache)
            zh = self.translate_cache.get(text)
            if zh is None:
                try:
                    zh = self.translator.translate(text, src="en", dest="zh-cn").text
                except Exception:
                    zh = ""
                self.translate_cache[text] = zh
            if not zh:
                continue
            lbl = QLabel(zh, self)
            lbl.setFont(QFont("PingFang SC", 12))
            lbl.setStyleSheet("color: white; background-color: rgba(0,0,0,0.6); padding:4px; border-radius:4px;")
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            # slightly expand bounding box for readability
            pad_w = max(8, int(w * 0.1))
            pad_h = max(4, int(h * 0.2))
            lbl.setGeometry(max(0, x - pad_w), max(0, y - pad_h), max(80, w + pad_w*2), max(20, h + pad_h*2))
            lbl.show()
            self.overlays[gkey] = lbl

        # remove overlays not in seen_keys
        for k in list(self.overlays.keys()):
            if k not in seen_keys:
                try:
                    self.overlays[k].hide()
                    self.overlays[k].deleteLater()
                except Exception:
                    pass
                del self.overlays[k]

    def closeEvent(self, event):
        try:
            if self.timer and self.timer.isActive():
                self.timer.stop()
        except Exception:
            pass
        try:
            if self.pending and not self.pending.done():
                try:
                    self.pending.cancel()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.executor.shutdown(wait=False)
        except Exception:
            pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    win = AutoOverlayWindow()
    win.show()
    print("Auto OCR overlay started")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

