"""Generation overlay — the app-wide "something is being generated here" state.

RULE: wherever a generated image or video will appear, cover that exact widget
with a GenOverlay while the job runs. It blurs whatever is already there, spins
a ring, shows a slim progress bar and an adaptive countdown (the first run of a
kind has no history, so it counts up instead).

    self.ov = GenOverlay(self.body_view)
    self.ov.start("body", count=2)
    self.ov.set_progress(done, total)     # optional, from the worker
    self.ov.stop()                        # stop(success=False) on failure
"""

from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QEvent, QRect, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
from PySide6.QtWidgets import QWidget

from ..theme import C
from ..generation import timing

RING_R = 17          # spinner radius
RING_W = 3
BAR_W = 150
BAR_H = 4
GAP = 12             # ring → bar → text spacing


def _fmt(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 60}:{seconds % 60:02d}"


class GenOverlay(QWidget):
    def __init__(self, target: QWidget):
        super().__init__(target)
        self.target = target
        self.kind = ""
        self.count = 1
        self.note = ""
        self._predicted = None
        self._angle = 0
        self._done = 0
        self._blur = None
        self._clock = QElapsedTimer()
        self._tick = QTimer(self)
        self._tick.setInterval(33)
        self._tick.timeout.connect(self._on_tick)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setCursor(Qt.BusyCursor)
        target.installEventFilter(self)
        self.hide()

    # ---------- lifecycle ----------
    @property
    def active(self) -> bool:
        return self._tick.isActive()

    def start(self, kind: str, count: int = 1, note: str = ""):
        self.kind = kind
        self.count = max(1, int(count))
        self.note = note
        self._done = 0
        self._angle = 0
        self._predicted = timing.predict(kind, self.count)
        self._blur = self._snapshot()
        self._sync_geometry()
        self._clock.restart()
        self.show(); self.raise_()
        self._tick.start()

    def set_note(self, text: str):
        self.note = text
        self.update()

    def set_progress(self, done: int, total: int):
        self._done = max(0, int(done))
        self.count = max(1, int(total))
        self.update()

    def stop(self, success: bool = True):
        if not self._tick.isActive():
            self.hide()
            return
        elapsed = self._clock.elapsed() / 1000.0
        self._tick.stop()
        self.hide()
        self._blur = None
        if success and self.kind:
            timing.record(self.kind, elapsed, self.count)

    # ---------- geometry / snapshot ----------
    def eventFilter(self, obj, e):
        if obj is self.target and e.type() in (QEvent.Resize, QEvent.Move, QEvent.Show):
            self._sync_geometry()
        return False

    def _sync_geometry(self):
        self.setGeometry(self.target.rect())

    def _snapshot(self):
        """Blurred copy of what the target currently shows (cheap downscale blur)."""
        if self.target.width() < 8 or self.target.height() < 8:
            return None
        try:
            pm = self.target.grab()
        except Exception:
            return None
        if pm.isNull():
            return None
        small = pm.scaled(max(1, pm.width() // 14), max(1, pm.height() // 14),
                          Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        return small.scaled(pm.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def _on_tick(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    # ---------- painting ----------
    def _fraction(self):
        """0..1 progress, or None when there is nothing to base it on."""
        frac = None
        if self._predicted:
            frac = min(0.985, self._clock.elapsed() / 1000.0 / self._predicted)
        if self.count > 1 and self._done:
            frac = max(frac or 0.0, self._done / self.count)
        return frac

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()

        clip = QPainterPath()
        clip.addRoundedRect(QRectF(r), 10, 10)
        p.setClipPath(clip)

        if self._blur is not None and not self._blur.isNull():
            p.drawPixmap(r, self._blur)
            p.fillRect(r, QColor(20, 16, 13, 165))
        else:
            p.fillRect(r, QColor(20, 16, 13, 225))

        elapsed = self._clock.elapsed() / 1000.0
        frac = self._fraction()

        block_h = RING_R * 2 + GAP + BAR_H + GAP + 14
        top = r.center().y() - block_h // 2
        cx = r.center().x()

        # ---- spinner ring ----
        ring = QRect(cx - RING_R, top, RING_R * 2, RING_R * 2)
        p.setPen(QPen(QColor(C["line"]), RING_W, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(ring, 0, 360 * 16)
        p.setPen(QPen(QColor(C["accent"]), RING_W, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(ring, int((90 - self._angle) * 16), -100 * 16)

        # ---- progress bar ----
        bw = min(BAR_W, max(60, r.width() - 40))
        bar = QRectF(cx - bw / 2, top + RING_R * 2 + GAP, bw, BAR_H)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(C["line"]))
        p.drawRoundedRect(bar, BAR_H / 2, BAR_H / 2)
        p.setBrush(QColor(C["accent"]))
        if frac is None:
            # unknown duration → a sliding segment
            seg = bw * 0.32
            travel = (elapsed % 1.8) / 1.8
            x = bar.left() + (bw + seg) * travel - seg
            fill = QRectF(max(bar.left(), x), bar.top(),
                          min(seg, bar.right() - max(bar.left(), x)), BAR_H)
            if fill.width() > 0:
                p.drawRoundedRect(fill, BAR_H / 2, BAR_H / 2)
        else:
            p.drawRoundedRect(QRectF(bar.left(), bar.top(), bw * frac, BAR_H), BAR_H / 2, BAR_H / 2)

        # ---- caption ----
        if self._predicted:
            left = self._predicted - elapsed
            label = f"≈ {_fmt(left)} left" if left > 0.5 else "finishing…"
        else:
            label = _fmt(elapsed)
        if self.count > 1:
            label += f"   ·   {min(self._done + 1, self.count)}/{self.count}"
        if self.note:
            label = self.note

        f = QFont(); f.setPointSizeF(8.5); f.setWeight(QFont.DemiBold)
        p.setFont(f)
        p.setPen(QColor(C["ink_dim"]))
        p.drawText(QRect(r.left(), int(bar.bottom() + GAP - 4), r.width(), 18),
                   Qt.AlignHCenter | Qt.AlignTop, label)
        p.end()
