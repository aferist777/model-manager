"""Reference viewer popup: plays a saved reel (WebView2 + local file, H.264
plays) or pages through a saved carousel/photoshoot."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)

from ..store import DATA_DIR
from ..webview2_native import WebView2Host, available
from ..theme import qss, C


class ReferenceViewer(QDialog):
    def __init__(self, ref, parent=None):
        super().__init__(parent)
        self.ref = ref
        self._view = None
        self.setWindowTitle(ref.title or "Reference")
        self.setModal(True)
        self.setMinimumSize(420, 720)
        self.setStyleSheet(qss())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        is_carousel = ref.media_type == "carousel" and ref.image_paths
        if ref.video_path and not is_carousel and available():
            self._build_video(root, ref.video_path)
        elif ref.image_paths:
            self._build_carousel(root, ref.image_paths)
        elif ref.thumb_path:
            self._build_carousel(root, [ref.thumb_path])
        else:
            lbl = QLabel("No downloaded media for this reference.")
            lbl.setObjectName("Muted"); lbl.setAlignment(Qt.AlignCenter)
            root.addWidget(lbl, 1)

        # caption
        if ref.caption:
            cap = QLabel(ref.caption)
            cap.setObjectName("Muted"); cap.setWordWrap(True)
            cap.setContentsMargins(14, 10, 14, 12)
            cap.setMaximumHeight(96)
            root.addWidget(cap)

    def _build_video(self, root, video_path):
        uri = Path(video_path).as_uri()
        udd = str(DATA_DIR / "webview2_viewer")
        self._view = WebView2Host(uri, udd)
        self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self._view, 1)

    def _stop_video(self):
        if self._view is not None:
            self._view.shutdown()
            self._view = None

    def done(self, r):
        self._stop_video()      # stop playback on any close (X / Esc / accept)
        super().done(r)

    def closeEvent(self, e):
        self._stop_video()
        super().closeEvent(e)

    def _build_carousel(self, root, images):
        self.images = images
        self.idx = 0

        self.pic = QLabel(); self.pic.setAlignment(Qt.AlignCenter)
        self.pic.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pic.setStyleSheet(f"background:{C['bg']};")
        root.addWidget(self.pic, 1)

        nav = QWidget(); nl = QHBoxLayout(nav); nl.setContentsMargins(12, 8, 12, 10)
        prev = QPushButton("‹"); prev.setCursor(Qt.PointingHandCursor); prev.clicked.connect(self._prev)
        nxt = QPushButton("›"); nxt.setCursor(Qt.PointingHandCursor); nxt.clicked.connect(self._next)
        self.counter = QLabel(); self.counter.setObjectName("Muted"); self.counter.setAlignment(Qt.AlignCenter)
        nl.addWidget(prev); nl.addStretch(); nl.addWidget(self.counter); nl.addStretch(); nl.addWidget(nxt)
        nav.setVisible(len(images) > 1)
        root.addWidget(nav)
        self._show_image()

    def _show_image(self):
        pm = QPixmap(self.images[self.idx])
        if not pm.isNull():
            self.pic.setPixmap(pm.scaled(self.pic.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.counter.setText(f"{self.idx + 1} / {len(self.images)}")

    def _prev(self):
        self.idx = (self.idx - 1) % len(self.images)
        self._show_image()

    def _next(self):
        self.idx = (self.idx + 1) % len(self.images)
        self._show_image()

    def resizeEvent(self, e):
        if hasattr(self, "images"):
            self._show_image()
        super().resizeEvent(e)

    def keyPressEvent(self, e):
        if hasattr(self, "images"):
            if e.key() == Qt.Key_Left:
                self._prev(); return
            if e.key() == Qt.Key_Right:
                self._next(); return
        super().keyPressEvent(e)
