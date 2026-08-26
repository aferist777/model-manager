"""Standalone spike: embed Edge WebView2 in a Qt window loading Instagram.
Run this to confirm reels PLAY inside an embedded browser before we swap the
Instagram panel over to WebView2.

    python tools/wv2_spike.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from app.webview2_native import WebView2Host, available


def main():
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("WebView2 spike — Instagram (test reels here)")
    win.resize(460, 820)

    if not available():
        win.setCentralWidget(QLabel("WebView2 DLLs not found in libs/webview2/"))
        win.show()
        return sys.exit(app.exec())

    udd = str(Path(__file__).resolve().parent.parent / "data" / "webview2_edge")

    def on_ready(ok, msg):
        print("CoreWebView2 ready:", ok, msg)

    host = WebView2Host("https://www.instagram.com/", udd, on_ready=on_ready)
    win.setCentralWidget(host)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
