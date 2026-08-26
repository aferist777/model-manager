"""Full-size image overlay. Click outside the image (or Esc) closes it.
Used for generated images (drafts, portraits, previews)."""

from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import QDialog, QLabel


class Lightbox(QDialog):
    def __init__(self, source, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self._pm = source if isinstance(source, QPixmap) else QPixmap(str(source))

        self.img = QLabel(self)
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # clicks go to the dialog

        win = parent.window() if parent else None
        if win is not None:
            self.setGeometry(win.geometry())
        else:
            self.resize(900, 700)

    def _rescale(self):
        if self._pm.isNull():
            return
        m = 48
        w = max(50, self.width() - m * 2)
        h = max(50, self.height() - m * 2)
        sc = self._pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.img.setPixmap(sc)
        self.img.resize(sc.size())
        self.img.move((self.width() - sc.width()) // 2, (self.height() - sc.height()) // 2)

    def showEvent(self, e):
        self._rescale()
        super().showEvent(e)

    def resizeEvent(self, e):
        self._rescale()
        super().resizeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 225))
        p.end()

    def mousePressEvent(self, e):
        if not self.img.geometry().contains(e.pos()):
            self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)


def open_lightbox(source, parent):
    """source: QPixmap or an image path."""
    pm = source if isinstance(source, QPixmap) else QPixmap(str(source))
    if pm.isNull():
        return None
    lb = Lightbox(pm, parent)
    lb.show()
    return lb


class _ClickToLightbox(QObject):
    def __init__(self, source_fn, parent):
        super().__init__(parent)
        self._source_fn = source_fn
        self._parent = parent

    def eventFilter(self, obj, e):
        if e.type() == QEvent.MouseButtonPress:
            src = self._source_fn()
            if src:
                open_lightbox(src, self._parent)
                return True
        return False


def enable_lightbox(label, source_fn, parent=None):
    """Open a Lightbox when `label` is clicked. source_fn() -> QPixmap/path/None."""
    label.setCursor(Qt.PointingHandCursor)
    filt = _ClickToLightbox(source_fn, parent or label.window())
    label.installEventFilter(filt)
    label._lb_filter = filt   # keep a reference alive
