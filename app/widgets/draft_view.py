"""One big image that fills its column, with ‹ › to page through the drafts.

Replaces the old "big picture + row of thumbnails": drafts are the same image
slot, flipped with the arrows, so the preview always gets the full width and
height of its column. Arrows appear only when there is more than one draft."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy

from .lightbox import open_lightbox


class DraftView(QWidget):
    changed = Signal(int)          # current index

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.items = []            # [QPixmap]
        self.index = -1
        self._base = None          # shown when there are no drafts (e.g. the mannequin)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0); row.setSpacing(6)

        self.prev_btn = QPushButton("‹"); self.next_btn = QPushButton("›")
        for b, tip in ((self.prev_btn, "Previous draft"), (self.next_btn, "Next draft")):
            b.setObjectName("NavBtn"); b.setCursor(Qt.PointingHandCursor)
            b.setFixedWidth(26); b.setToolTip(tip)
            b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            b.hide()

        self.image = QLabel(placeholder)
        self.image.setObjectName("DraftPh")
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image.setCursor(Qt.PointingHandCursor)
        self.image.mousePressEvent = self._on_click

        self.counter = QLabel("", self.image)
        self.counter.setObjectName("DraftCount")
        self.counter.setAlignment(Qt.AlignCenter)
        self.counter.hide()

        row.addWidget(self.prev_btn)
        row.addWidget(self.image, 1)
        row.addWidget(self.next_btn)

        self.prev_btn.clicked.connect(lambda: self.set_index(self.index - 1))
        self.next_btn.clicked.connect(lambda: self.set_index(self.index + 1))

    # ---------- content ----------
    def set_base(self, pixmap):
        """Image shown while there are no drafts (mannequin, saved portrait)."""
        self._base = pixmap
        if not self.items:
            self._render()

    def set_items(self, blobs, select=-1):
        self.items = [self._to_pixmap(b) for b in blobs]
        self.index = (len(self.items) - 1) if select < 0 else select
        self._render()
        if self.items:
            self.changed.emit(self.index)

    def clear(self):
        self.items = []; self.index = -1
        self._render()

    def set_index(self, i):
        if not self.items:
            return
        self.index = i % len(self.items)
        self._render()
        self.changed.emit(self.index)

    def current(self):
        return self.items[self.index] if 0 <= self.index < len(self.items) else self._base

    @staticmethod
    def _to_pixmap(blob):
        if isinstance(blob, QPixmap):
            return blob
        pm = QPixmap()
        pm.loadFromData(blob if isinstance(blob, (bytes, bytearray)) else bytes(blob))
        return pm

    # ---------- painting ----------
    def _render(self):
        pm = self.current()
        many = len(self.items) > 1
        self.prev_btn.setVisible(many); self.next_btn.setVisible(many)
        self.counter.setVisible(many)
        if many:
            self.counter.setText(f"{self.index + 1} / {len(self.items)}")
            self.counter.adjustSize()
            self._place_counter()
        if pm is None or pm.isNull():
            self.image.setPixmap(QPixmap())
            return
        self.rescale()

    def _place_counter(self):
        """Sit on the picture itself, not on the letterboxed label around it."""
        w, h = self.counter.width(), self.counter.height()
        pm = self.image.pixmap()
        drawn_h = pm.height() if (pm is not None and not pm.isNull()) else self.image.height()
        bottom = (self.image.height() + drawn_h) // 2
        self.counter.move(max(0, (self.image.width() - w) // 2),
                          max(0, min(bottom, self.image.height()) - h - 8))

    def rescale(self):
        pm = self.current()
        if pm is None or pm.isNull():
            return
        area = self.image.size()
        if area.width() < 40 or area.height() < 40:
            area = self.size()
        if area.width() < 40 or area.height() < 40:
            return
        self.image.setPixmap(pm.scaled(area, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if self.counter.isVisible():
            self._place_counter()

    def resizeEvent(self, e):
        self.rescale()
        super().resizeEvent(e)

    def _on_click(self, _e):
        pm = self.current()
        if pm is not None and not pm.isNull():
            open_lightbox(pm, self)
