"""Dev helper: render the running window to a PNG so changes can be reviewed
without a display. Used after every frontend/backend edit.

Usage:
    set QT_QPA_PLATFORM=offscreen
    set PYTHONPATH=<repo>/model-manager
    python tools/snapshot.py <out.png> [tab_index]

tab_index: 0 Appearance (default) | 1 Content | 2 References
Note: offscreen render shows tofu glyphs + WebEngine GPU warnings — harmless,
the real windowed app on Windows renders Segoe UI correctly.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

from app import main


def run(out_path: str, tab: int = 0):
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(main.qss())
    w = main.MainWindow()
    w.resize(1440, 860)
    w.show()

    if tab:
        w.center.tabs.button(tab).click()
        w.center.stack.setCurrentIndex(tab)

    loop = QEventLoop()
    QTimer.singleShot(1500, loop.quit)  # let the webview settle
    loop.exec()

    w.grab().save(out_path)
    print("saved", out_path, "(tab", tab, ")")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "snapshot.png"
    tab = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    run(out, tab)
