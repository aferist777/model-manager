"""Placeholder avatar generator: rounded gradient tile + initials.
This is the seam where real generated character images will plug in later
(swap the painted pixmap for a loaded image path)."""

import os

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QBrush, QFont, QPainterPath

from .theme import PALETTES


def initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    return ("".join(p[0] for p in parts[:2]).upper()) or "?"


def avatar_pixmap(name: str, seed: int = 0, size: int = 42, radius: int = 10) -> QPixmap:
    dpr = 2
    s = size * dpr
    pm = QPixmap(s, s)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    c1, c2 = PALETTES[seed % len(PALETTES)]
    grad = QLinearGradient(0, 0, s, s)
    grad.setColorAt(0.0, QColor(c1))
    grad.setColorAt(1.0, QColor(c2))

    rect = QRectF(0, 0, s, s)
    path = QPainterPath()
    path.addRoundedRect(rect, radius * dpr, radius * dpr)
    p.setClipPath(path)
    p.fillRect(rect, QBrush(grad))
    # subtle darkening for depth
    dark = QLinearGradient(0, 0, s, s)
    dark.setColorAt(0.0, QColor(0, 0, 0, 0))
    dark.setColorAt(1.0, QColor(0, 0, 0, 60))
    p.fillRect(rect, QBrush(dark))

    f = QFont("Segoe UI")
    f.setBold(True)
    f.setPixelSize(int(s * 0.36))
    p.setFont(f)
    p.setPen(QColor(255, 255, 255, 235))
    p.drawText(rect, Qt.AlignCenter, initials(name))
    p.end()
    return pm


def avatar_from_file(path: str, size: int = 42, radius: int = 10) -> QPixmap:
    """Rounded, center-cropped avatar from a real image file."""
    dpr = 2
    s = size * dpr
    src = QPixmap(path)
    pm = QPixmap(s, s)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    path_clip = QPainterPath()
    path_clip.addRoundedRect(QRectF(0, 0, s, s), radius * dpr, radius * dpr)
    p.setClipPath(path_clip)
    scaled = src.scaled(s, s, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    x = (s - scaled.width()) // 2
    y = (s - scaled.height()) // 2
    p.drawPixmap(x, y, scaled)
    p.end()
    return pm


def avatar_from_sheet(path: str, size: int = 42, radius: int = 10) -> QPixmap:
    """Avatar cut from a character image: a square around the face.

    Generated characters are portrait/full-length shots with the face centred
    horizontally near the top, so crop a square there instead of the middle
    (which would land on the torso)."""
    src = QPixmap(path)
    if src.isNull():
        return avatar_from_file(path, size, radius)
    w, h = src.width(), src.height()
    side = min(w, int(h * 0.5))           # a headshot-sized square
    if side <= 0:
        return avatar_from_file(path, size, radius)
    x = max(0, (w - side) // 2)
    y = max(0, int(h * 0.14))             # centred on the face, not the crown
    face = src.copy(x, y, side, min(side, h - y))

    dpr = 2
    s = size * dpr
    pm = QPixmap(s, s)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, s, s), radius * dpr, radius * dpr)
    p.setClipPath(clip)
    scaled = face.scaled(s, s, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    p.drawPixmap((s - scaled.width()) // 2, (s - scaled.height()) // 2, scaled)
    p.end()
    return pm


def has_image(path: str) -> bool:
    return bool(path) and os.path.exists(path)


def solid_pixmap(seed: int = 0, size: int = 44, radius: int = 8) -> QPixmap:
    """Gradient tile without initials (reference thumbnails)."""
    dpr = 2
    s = size * dpr
    pm = QPixmap(s, s)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    c1, c2 = PALETTES[seed % len(PALETTES)]
    grad = QLinearGradient(0, 0, s, s)
    grad.setColorAt(0.0, QColor(c1))
    grad.setColorAt(1.0, QColor(c2))
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, s, s), radius * dpr, radius * dpr)
    p.fillPath(path, QBrush(grad))
    p.end()
    return pm
