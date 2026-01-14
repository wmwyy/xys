#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鼠标悬停 OCR 翻译覆盖层（macOS）

功能：
- 在鼠标悬停时截取光标附近屏幕区域并进行 OCR 识别（英文）
- 将识别到的英文文本翻译成中文并在光标旁显示
- 不拦截鼠标事件（点击仍传递到下方窗口）
- 若未安装 tesseract 或 OCR 失败，可回退到 labels.json 静态提示

依赖：
  brew install tesseract
  pip install -r requirements.txt  # 包含: pillow, pytesseract, googletrans==4.0.0-rc1
"""

import sys
import time
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageGrab
import pytesseract
from googletrans import Translator
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import logging

# setup logger
LOG_FILE = Path(__file__).parent / "ocr_debug.log"
logger = logging.getLogger("ocr_overlay")
if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    # also echo to stderr for convenience
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception:
    easyocr = None
    EASYOCR_AVAILABLE = False

# verify tesseract binary availability
try:
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

# easyocr reader placeholder (initialized lazily if needed)
easyocr_reader = None

from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QColor, QCursor


def ocr_and_translate(bbox, do_translate=True):
    """Function run in worker thread: returns (orig_text, zh_text)"""
    try:
        logger.debug(f"Worker start bbox={bbox} do_translate={do_translate}")
        img = ImageGrab.grab(bbox=bbox)
        img = img.convert("L")
        img = ImageOps.autocontrast(img)
        img = img.filter(ImageFilter.SHARPEN)
        text = pytesseract.image_to_string(img, lang="eng")
        text = text.strip()
        zh = ""
        if text and do_translate:
            try:
                translator = Translator()
                res = translator.translate(text, src="en", dest="zh-cn")
                zh = res.text
            except Exception:
                logger.exception("Translation failed in worker")
                zh = ""
        logger.debug(f"Worker result text={repr(text)} zh={repr(zh)}")
        return text, zh
    except Exception:
        logger.exception("OCR worker failed")
        return "", ""


class OCRTranslateOverlay(QWidget):
    """覆层窗口，负责显示翻译 tooltip"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.tooltip = QLabel("", self)
        self.tooltip.setStyleSheet("color: white; background-color: rgba(0,0,0,0.8); padding: 6px; border-radius: 6px;")
        self.tooltip.setFont(QFont("PingFang SC", 12))
        self.tooltip.hide()

        self.translator = Translator()
        self.last_text = ""
        self.worker = None
        self.lock = Lock()
        # cache original->translated
        self.translate_cache = {}
        self.ocr_enabled = True
        # if tesseract not available and easyocr exists, init reader
        global easyocr_reader
        if not TESSERACT_AVAILABLE and EASYOCR_AVAILABLE:
            try:
                # initialize reader once (may take time)
                easyocr_reader = easyocr.Reader(['en'], gpu=False)
            except Exception:
                easyocr_reader = None


        # fallback labels.json
        self.labels = []
        self.config_file = Path(__file__).parent / "labels.json"
        self.load_labels()
        logger.info("Overlay initialized")
        logger.info(f"TESSERACT_AVAILABLE={TESSERACT_AVAILABLE} EASYOCR_AVAILABLE={EASYOCR_AVAILABLE}")

        # timer for polling mouse (short interval, but OCR only when cursor stable)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_mouse)
        self.timer.start(60)  # 60ms for responsive feel
        self.last_pos = None
        self.last_move_time = 0.0
        self.stable_threshold_ms = 250  # require cursor to be stable this long before OCR
        # threadpool executor for OCR tasks
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.pending_future = None

    def load_labels(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.labels = cfg.get("labels", [])
                logger.debug(f"Loaded {len(self.labels)} labels from labels.json")
        except Exception:
            self.labels = []
            logger.exception("Failed to load labels.json")

    def poll_mouse(self):
        pos = QCursor.pos()
        x, y = pos.x(), pos.y()
        logger.debug(f"poll_mouse at {(x,y)}")

        # First try to match labels.json (quick local hit)
        for idx, lbl in enumerate(self.labels):
            rect = lbl.get("rect")
            if rect and len(rect) >= 4:
                lx, ly, w, h = rect
                if lx <= x <= lx + w and ly <= y <= ly + h:
                    text = lbl.get("tooltip", lbl.get("text", ""))
                    logger.debug(f"Label hit idx={idx} text={text}")
                    self.show_tooltip(text, x, y)
                    return

        # Otherwise do OCR on a small region near cursor
        if not self.ocr_enabled:
            logger.debug("OCR disabled, hiding tooltip")
            self.tooltip.hide()
            return

        # throttle: don't start new worker if one is running
        if self.pending_future and not self.pending_future.done():
            logger.debug("OCR pending, skipping new submit")
            return

        # check cursor stability: if moved, record time and wait until stable
        cur = (x, y)
        now = time.time()
        if self.last_pos is None or abs(cur[0] - self.last_pos[0]) > 2 or abs(cur[1] - self.last_pos[1]) > 2:
            self.last_pos = cur
            self.last_move_time = now
            # hide tooltip while moving (but labels.json still handled above)
            if self.tooltip.isVisible():
                self.tooltip.hide()
            return

        # if cursor not stable long enough, skip OCR
        if (now - self.last_move_time) * 1000.0 < self.stable_threshold_ms:
            return

        # capture region (width x height)
        w, h = 260, 100
        left = max(0, x - w // 2)
        top = max(0, y - h // 2)
        bbox = (left, top, left + w, top + h)

        # submit OCR task to executor
        try:
            # don't submit if there's already a pending future
            logger.debug(f"Submitting OCR task bbox={bbox}")
            self.pending_future = self.executor.submit(ocr_and_translate, bbox, True)
            # schedule handling on completion in main thread
            def _on_done(fut):
                try:
                    orig, zh = fut.result(timeout=0)
                except Exception:
                    try:
                        orig, zh = fut.result()
                    except Exception:
                        orig, zh = "", ""
                QTimer.singleShot(0, lambda: self.on_ocr_finished(orig, zh))
            self.pending_future.add_done_callback(_on_done)
        except Exception:
            logger.exception("Failed to submit OCR task")
            pass

    def closeEvent(self, event):
        """Ensure worker and timers are stopped cleanly to avoid thread warnings."""
        try:
            if self.timer and self.timer.isActive():
                self.timer.stop()
        except Exception:
            pass
        try:
            if self.worker and self.worker.isRunning():
                # force terminate worker thread (best-effort)
                try:
                    self.worker.terminate()
                except Exception:
                    pass
                try:
                    self.worker.wait(500)
                except Exception:
                    pass
        except Exception:
            pass
        event.accept()

    def on_ocr_finished(self, orig_text, zh_text):
        try:
            if not orig_text:
                # nothing recognized
                logger.debug("OCR finished: no text recognized")
                self.tooltip.hide()
                return

            # avoid repeating same tooltip
            if orig_text == self.last_text:
                logger.debug("OCR finished: same as last_text, skipping")
                return

            # use cached translation if available
            zh = ""
            with self.lock:
                if orig_text in self.translate_cache:
                    zh = self.translate_cache[orig_text]

            if not zh and zh_text:
                zh = zh_text

            if not zh:
                # empty translation, hide
                logger.debug(f"OCR finished: no translation for {repr(orig_text)}")
                self.tooltip.hide()
                return

            # cache translation
            with self.lock:
                self.translate_cache[orig_text] = zh

            self.last_text = orig_text
            pos = QCursor.pos()
            logger.info(f"Displaying tooltip: {repr(zh)} for orig={repr(orig_text)} at {pos.x(),pos.y()}")
            self.show_tooltip(zh, pos.x(), pos.y())
        finally:
            self.pending_future = None

    def closeEvent(self, event):
        """Ensure executor and timers are stopped cleanly to avoid thread warnings."""
        try:
            if self.timer and self.timer.isActive():
                self.timer.stop()
        except Exception:
            pass
        try:
            if self.pending_future and not self.pending_future.done():
                try:
                    self.pending_future.cancel()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if self.executor:
                try:
                    self.executor.shutdown(wait=False)
                except Exception:
                    pass
        except Exception:
            pass
        event.accept()

    def show_tooltip(self, text, x, y):
        self.tooltip.setText(text)
        self.tooltip.adjustSize()
        # place to right-bottom of cursor
        local = self.mapFromGlobal(QCursor.pos())
        tx = local.x() + 16
        ty = local.y() + 16
        max_x = self.width() - self.tooltip.width() - 8
        max_y = self.height() - self.tooltip.height() - 8
        tx = min(max(8, tx), max_x)
        ty = min(max(8, ty), max_y)
        self.tooltip.move(tx, ty)
        self.tooltip.show()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HEC-RAS OCR 翻译覆盖层")
    overlay = OCRTranslateOverlay()
    overlay.show()
    print("OCR 翻译覆盖层已启动（需要 tesseract 可用）")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

