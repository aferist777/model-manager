"""Create-post popup (shell). Order: platform -> publication type (depends on
platform) -> reference pick (optional). The rest of the flow comes later."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup,
    QWidget, QScrollArea, QFrame, QGridLayout
)

from ..avatar import has_image, solid_pixmap
from ..theme import qss, C

PLATFORMS = [("instagram", "Instagram"), ("telegram", "Telegram"),
             ("tiktok", "TikTok"), ("youtube", "YouTube")]

TYPES = {
    "instagram": ["Post", "Carousel", "Reel", "Story"],
    "telegram": ["Photo post", "Album", "Video", "Text post"],
    "tiktok": ["Video", "Photo mode"],
    "youtube": ["Short", "Video", "Community post"],
}


class PickerTile(QFrame):
    picked = Signal(str)   # ref_id

    def __init__(self, ref):
        super().__init__()
        self.ref = ref
        self.selected = False
        self.setFixedSize(84, 112)
        self.setCursor(Qt.PointingHandCursor)
        self._pm = QPixmap(ref.thumb_path) if has_image(ref.thumb_path) else solid_pixmap(ref.thumb_seed, 84, 8)

    def set_selected(self, v):
        self.selected = v
        self.update()

    def paintEvent(self, e):
        from PySide6.QtGui import QPainter, QColor, QPainterPath
        from PySide6.QtCore import QRectF
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        path = QPainterPath(); path.addRoundedRect(QRectF(0, 0, w, h), 7, 7); p.setClipPath(path)
        s = self._pm.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        p.drawPixmap((w - s.width()) // 2, (h - s.height()) // 2, s)
        if self.selected:
            p.setClipping(False)
            pen = p.pen(); pen.setColor(QColor(C['accent'])); pen.setWidth(3); p.setPen(pen)
            p.setBrush(Qt.NoBrush); p.drawRoundedRect(QRectF(1.5, 1.5, w - 3, h - 3), 6, 6)
        p.end()

    def mousePressEvent(self, e):
        self.picked.emit(self.ref.id)


class CreatePostDialog(QDialog):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.platform = None
        self.pub_type = None
        self.ref_id = None
        self._tiles = []
        self.setWindowTitle("Create post")
        self.setModal(True)
        self.setMinimumSize(560, 620)
        self.setStyleSheet(qss())

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(14)

        t = QLabel("Create post"); t.setObjectName("DlgTitle")
        root.addWidget(t)

        # 1) platform
        root.addWidget(self._head("PLATFORM"))
        self.platform_group = QButtonGroup(self); self.platform_group.setExclusive(True)
        prow = QHBoxLayout(); prow.setSpacing(8)
        for i, (key, name) in enumerate(PLATFORMS):
            b = QPushButton(name); b.setObjectName("Chip"); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            self.platform_group.addButton(b, i)
            prow.addWidget(b)
        prow.addStretch()
        self.platform_group.idClicked.connect(self._on_platform)
        root.addLayout(prow)

        # 2) type (depends on platform)
        root.addWidget(self._head("PUBLICATION TYPE"))
        self.type_host = QWidget()
        self.type_layout = QHBoxLayout(self.type_host); self.type_layout.setContentsMargins(0, 0, 0, 0)
        self.type_layout.setSpacing(8)
        self.type_hint = QLabel("Pick a platform first"); self.type_hint.setObjectName("Muted")
        self.type_layout.addWidget(self.type_hint); self.type_layout.addStretch()
        self.type_group = None
        root.addWidget(self.type_host)

        # 3) reference (optional)
        root.addWidget(self._head("REFERENCE  (optional)"))
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); scroll.setMinimumHeight(150)
        host = QWidget(); host.setObjectName("Pane")
        self.ref_grid = QGridLayout(host); self.ref_grid.setContentsMargins(0, 0, 8, 0)
        self.ref_grid.setSpacing(10); self.ref_grid.setAlignment(Qt.AlignTop)
        self._build_refs()
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        # footer
        foot = QHBoxLayout(); foot.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setCursor(Qt.PointingHandCursor); cancel.clicked.connect(self.reject)
        self.create_btn = QPushButton("Create"); self.create_btn.setObjectName("Primary")
        self.create_btn.setCursor(Qt.PointingHandCursor); self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self.accept)
        foot.addWidget(cancel); foot.addStretch(); foot.addWidget(self.create_btn)
        root.addLayout(foot)

    def _head(self, text):
        l = QLabel(text); l.setObjectName("SpecHead"); return l

    def _on_platform(self, idx):
        self.platform = PLATFORMS[idx][0]
        self.pub_type = None
        # rebuild type chips
        while self.type_layout.count():
            it = self.type_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        self.type_group = QButtonGroup(self); self.type_group.setExclusive(True)
        for i, name in enumerate(TYPES.get(self.platform, [])):
            b = QPushButton(name); b.setObjectName("Chip"); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            self.type_group.addButton(b, i)
            self.type_layout.addWidget(b)
        self.type_layout.addStretch()
        self.type_group.idClicked.connect(self._on_type)
        self._update_create()

    def _on_type(self, idx):
        self.pub_type = TYPES[self.platform][idx]
        self._update_create()

    def _build_refs(self):
        refs = sorted(self.store.references, key=lambda r: not r.favorite)
        for i, r in enumerate(refs):
            tile = PickerTile(r)
            tile.picked.connect(self._on_ref_picked)
            self.ref_grid.addWidget(tile, i // 5, i % 5)
            self._tiles.append(tile)
        if not refs:
            self.ref_grid.addWidget(QLabel("No references yet."), 0, 0)

    def _on_ref_picked(self, ref_id):
        # single-select toggle
        if self.ref_id == ref_id:
            self.ref_id = None
        else:
            self.ref_id = ref_id
        for t in self._tiles:
            t.set_selected(t.ref.id == self.ref_id)

    def _update_create(self):
        self.create_btn.setEnabled(bool(self.platform and self.pub_type))

    def get_selection(self):
        return {"platform": self.platform, "type": self.pub_type, "ref_id": self.ref_id}
