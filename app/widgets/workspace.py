"""Center pane: workspace with Appearance / Content / References tabs."""

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QScrollArea, QFrame, QGridLayout, QSizePolicy, QButtonGroup, QLineEdit, QMessageBox
)

from ..avatar import avatar_pixmap, avatar_from_sheet, has_image, solid_pixmap
from ..models_data import Reference, SOCIALS
from .profile_dialog import CharacterProfileDialog
from .reference_viewer import ReferenceViewer
from .create_post_dialog import CreatePostDialog, PLATFORMS
from .lightbox import enable_lightbox
from ..theme import C, PALETTES, qss


class RefCard(QFrame):
    """3:4 reference tile. Single click toggles selection; double click opens
    the viewer. A gold star marks favorites; a type badge marks reels/carousels."""
    open_requested = Signal()
    download_requested = Signal()
    selection_toggled = Signal(str, bool)   # ref_id, selected

    def __init__(self, ref):
        super().__init__()
        self.ref = ref
        self.selected = False
        self.setObjectName("RefTile")
        self.setCursor(Qt.PointingHandCursor)
        self._pm = QPixmap(ref.thumb_path) if has_image(ref.thumb_path) else None

        self.title = QLabel(ref.title or ref.url or "", self)
        self.title.setStyleSheet("color:#fff; font-size:11px; background:transparent;")
        self.title.setToolTip(ref.url or ref.title)

        self.star = QLabel("★", self)
        self.star.setStyleSheet("color:#f6c454; font-size:14px; background:transparent;")
        self.star.setVisible(bool(ref.favorite))

        self.badge = None
        bt = "▶" if ref.media_type == "reel" else (f"🖼{len(ref.image_paths)}" if ref.media_type == "carousel" else None)
        if bt:
            self.badge = QLabel(bt, self)
            self.badge.setStyleSheet(
                "background:rgba(0,0,0,0.55); color:#fff; font-size:10px; border-radius:5px; padding:0 4px;")

        self.dl2 = None
        if not ref.media_type and ref.url:
            self.dl2 = QPushButton("Download", self)
            self.dl2.setCursor(Qt.PointingHandCursor)
            self.dl2.setToolTip("Fetch media for this link")
            self.dl2.clicked.connect(lambda: self.download_requested.emit())

    def set_selected(self, v):
        self.selected = v
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing); p.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        path = QPainterPath(); path.addRoundedRect(QRectF(0, 0, w, h), 9, 9)
        p.setClipPath(path)
        if self._pm and not self._pm.isNull():
            s = self._pm.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            p.drawPixmap((w - s.width()) // 2, (h - s.height()) // 2, s)
        else:
            c1, c2 = PALETTES[self.ref.thumb_seed % len(PALETTES)]
            g = QLinearGradient(0, 0, w, h); g.setColorAt(0, QColor(c1)); g.setColorAt(1, QColor(c2))
            p.fillRect(0, 0, w, h, QBrush(g))
        scrim = QLinearGradient(0, h - 44, 0, h)
        scrim.setColorAt(0, QColor(0, 0, 0, 0)); scrim.setColorAt(1, QColor(0, 0, 0, 195))
        p.fillRect(0, h - 44, w, 44, QBrush(scrim))
        if self.selected:
            p.setClipping(False)
            pen = p.pen(); pen.setColor(QColor(C['accent'])); pen.setWidth(3); p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(1.5, 1.5, w - 3, h - 3), 8, 8)
        p.end()

    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        self.star.adjustSize(); self.star.move(w - self.star.width() - 5, 3)
        if self.badge:
            self.badge.adjustSize(); self.badge.move(4, 4)
        fm = self.title.fontMetrics()
        self.title.setText(fm.elidedText(self.ref.title or self.ref.url or "", Qt.ElideRight, w - 12))
        self.title.setFixedWidth(w - 12); self.title.adjustSize()
        self.title.move(6, h - self.title.height() - 5)
        if self.dl2:
            self.dl2.adjustSize(); self.dl2.move((w - self.dl2.width()) // 2, (h - self.dl2.height()) // 2)
        super().resizeEvent(e)

    def mousePressEvent(self, e):
        self.set_selected(not self.selected)
        self.selection_toggled.emit(self.ref.id, self.selected)
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        # revert the toggle the preceding press applied, then open the viewer
        self.set_selected(not self.selected)
        self.selection_toggled.emit(self.ref.id, self.selected)
        self.open_requested.emit()
        super().mouseDoubleClickEvent(e)


class RefBoard(QWidget):
    """Responsive grid of 3:4 RefCards, COLS per row; tiles resize with width."""
    COLS = 5

    def __init__(self):
        super().__init__()
        self.setObjectName("Pane")
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(10)
        self.grid.setAlignment(Qt.AlignTop)
        self._cards = []
        self._empty = None

    def set_cards(self, cards):
        while self.grid.count():
            it = self.grid.takeAt(0)
            wdg = it.widget()
            if wdg:
                wdg.deleteLater()
        self._cards = cards
        self._empty = None
        if not cards:
            self._empty = QLabel("No references yet — save reels from Instagram or paste a link above.")
            self._empty.setObjectName("Muted"); self._empty.setWordWrap(True)
            self.grid.addWidget(self._empty, 0, 0, 1, self.COLS)
            return
        for i, c in enumerate(cards):
            self.grid.addWidget(c, i // self.COLS, i % self.COLS)
        self._resize_cards()

    def _resize_cards(self):
        if not self._cards:
            return
        spacing = self.grid.spacing()
        avail = self.width() - spacing * (self.COLS - 1) - 4   # 4px safety so col 5 never clips
        tw = max(56, avail // self.COLS)
        th = int(tw * 4 / 3)
        for c in self._cards:
            c.setFixedSize(tw, th)

    def resizeEvent(self, e):
        self._resize_cards()
        super().resizeEvent(e)


class PreviewLabel(QLabel):
    """Big preview of the model image, fitted whole and sized to the image's own
    aspect ratio; falls back to a gradient placeholder with a caption."""
    def __init__(self):
        super().__init__()
        self.seed = 0
        self.caption = "character image"
        self.image_path = ""
        self._aspect = 2 / 3          # width / height; portrait by default
        self._corner = None
        self.setMinimumWidth(280)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_corner(self, widget):
        self._corner = widget
        widget.setParent(self)
        widget.raise_()
        self._place_corner()

    def _place_corner(self):
        if self._corner is not None:
            self._corner.adjustSize()
            self._corner.move(self.width() - self._corner.width() - 8, 8)

    def resizeEvent(self, e):
        # frame follows the image's own aspect, capped so a tall portrait doesn't
        # push the data columns off-screen
        want = max(214, min(int(self.width() / max(self._aspect, 0.01)), 620))
        if abs(self.height() - want) > 1:
            self.setFixedHeight(want)
        self._place_corner()
        super().resizeEvent(e)

    def set_model(self, seed, caption, image_path=""):
        self.seed = seed
        self.caption = caption
        self.image_path = image_path
        if has_image(image_path):
            pm = QPixmap(image_path)
            if not pm.isNull() and pm.height():
                self._aspect = pm.width() / pm.height()
        else:
            self._aspect = 2 / 3
        want = max(214, min(int(self.width() / max(self._aspect, 0.01)), 620))
        self.setFixedHeight(want)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 14, 14)
        p.setClipPath(path)

        if has_image(self.image_path):
            # the whole sheet has to be readable, so fit it — cropping to fill
            # would show nothing but the centre column
            src = QPixmap(self.image_path)
            scaled = src.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawPixmap((w - scaled.width()) // 2, (h - scaled.height()) // 2, scaled)
            p.end()
            return

        c1, c2 = PALETTES[self.seed % len(PALETTES)]
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, QColor(c1))
        grad.setColorAt(1, QColor(c2))
        p.fillRect(0, 0, w, h, QBrush(grad))
        f = QFont("Segoe UI"); f.setBold(True); f.setPixelSize(16)
        p.setFont(f); p.setPen(QColor(255, 255, 255, 230))
        p.drawText(0, h // 2 - 12, w, 24, Qt.AlignCenter, "Character sheet")
        f2 = QFont("Segoe UI"); f2.setPixelSize(12)
        p.setFont(f2); p.setPen(QColor(255, 255, 255, 160))
        p.drawText(0, h // 2 + 12, w, 20, Qt.AlignCenter, self.caption)
        p.end()


class WorkspacePane(QWidget):
    downloadRequested = Signal(str)   # re-download media for an existing link reference

    def __init__(self, store):
        super().__init__()
        self.store = store
        self._selected = set()
        self.setObjectName("Pane")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- header ----
        head = QWidget()
        head.setObjectName("PaneHead")
        hl = QVBoxLayout(head)
        hl.setContentsMargins(20, 9, 20, 9)
        hl.setSpacing(10)

        titlerow = QHBoxLayout()
        titlerow.setSpacing(11)
        self.av = QLabel()
        self.av.setFixedSize(34, 34)
        titlerow.addWidget(self.av)
        tcol = QVBoxLayout(); tcol.setSpacing(1)
        self.title = QLabel("Select a model")
        self.title.setObjectName("WsTitle")
        self.niche = QLabel("—")
        self.niche.setObjectName("WsNiche")
        tcol.addWidget(self.title); tcol.addWidget(self.niche)
        titlerow.addLayout(tcol)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setToolTip("Edit full character profile")
        self.edit_btn.clicked.connect(self._open_profile)
        titlerow.addWidget(self.edit_btn)
        titlerow.addStretch()
        hl.addLayout(titlerow)

        # tabs
        tabrow = QHBoxLayout(); tabrow.setSpacing(2)
        self.tabs = QButtonGroup(self)
        for i, name in enumerate(["Appearance", "Content", "References"]):
            b = QPushButton(name)
            b.setObjectName("Tab")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            if i == 0:
                b.setChecked(True)
            self.tabs.addButton(b, i)
            tabrow.addWidget(b)
        tabrow.addStretch()
        hl.addLayout(tabrow)
        root.addWidget(head)
        self.tabs.idClicked.connect(lambda i: self.stack.setCurrentIndex(i))

        # ---- stacked body ----
        self.stack = QStackedWidget()
        self.stack.addWidget(self._appearance_tab())
        self.stack.addWidget(self._content_tab())
        self.stack.addWidget(self._references_tab())
        root.addWidget(self.stack, 1)

        store.selectionChanged.connect(lambda _: self.refresh())
        store.modelsChanged.connect(self.refresh)
        store.referencesChanged.connect(self.rebuild_references)
        self.refresh()
        self.rebuild_references()

    # ---------- tabs ----------
    def _appearance_tab(self):
        """Image on the left, its data (appearance then social) on the right."""
        wrap = QWidget(); wrap.setObjectName("Pane")
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer = QHBoxLayout(wrap)
        outer.setContentsMargins(22, 22, 22, 22)
        outer.setSpacing(24)

        # the generated character image, pinned top-left
        self.preview = PreviewLabel()
        self.preview.setMaximumWidth(420)
        enable_lightbox(self.preview, lambda: self.preview.image_path if self.preview.image_path else None, self)
        pcol = QVBoxLayout(); pcol.setContentsMargins(0, 0, 0, 0); pcol.setSpacing(0)
        pcol.addWidget(self.preview); pcol.addStretch()
        outer.addLayout(pcol, 3)

        # to its right: appearance, then social media, in one column
        data = QVBoxLayout(); data.setSpacing(0)
        sh = QLabel("APPEARANCE SPEC"); sh.setObjectName("SpecHead")
        data.addWidget(sh)
        data.addSpacing(10)
        self.spec_box = QVBoxLayout(); self.spec_box.setSpacing(0)
        data.addLayout(self.spec_box)

        data.addSpacing(20)
        soc_head = QLabel("SOCIAL MEDIA"); soc_head.setObjectName("SpecHead")
        data.addWidget(soc_head)
        data.addSpacing(10)
        self.social_edits = {}
        for key, label in SOCIALS:
            lbl = QLabel(label); lbl.setObjectName("SpecKey")
            edit_soc = QLineEdit(); edit_soc.setPlaceholderText("@handle or link")
            edit_soc.editingFinished.connect(lambda k=key, e=edit_soc: self._save_social(k, e.text()))
            data.addWidget(lbl)
            data.addSpacing(3)
            data.addWidget(edit_soc)
            data.addSpacing(8)
            self.social_edits[key] = edit_soc
        data.addStretch()
        dw = QWidget(); dw.setLayout(data)
        outer.addWidget(dw, 2)

        scroll.setWidget(wrap)
        return scroll

    def _content_tab(self):
        wrap = QWidget(); wrap.setObjectName("Pane")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(22, 20, 22, 22); lay.setSpacing(14)

        # top bar: Create post + platform filters (multi-select; none = all)
        top = QHBoxLayout(); top.setSpacing(8)
        create = QPushButton("＋  Create post"); create.setObjectName("Primary"); create.setCursor(Qt.PointingHandCursor)
        create.clicked.connect(self._open_create_post)
        top.addWidget(create); top.addStretch()
        self.post_filters = {}
        for key, name in PLATFORMS:
            b = QPushButton(name); b.setObjectName("Chip"); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(f"Filter: {name}")
            b.clicked.connect(self._rebuild_posts)
            top.addWidget(b); self.post_filters[key] = b
        lay.addLayout(top)

        # posts grid (empty until posts are saved)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.posts_host = QWidget(); self.posts_host.setObjectName("Pane")
        self.posts_grid = QGridLayout(self.posts_host)
        self.posts_grid.setContentsMargins(0, 0, 0, 0); self.posts_grid.setSpacing(12)
        self.posts_grid.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.posts_host)
        lay.addWidget(scroll, 1)
        self._rebuild_posts()
        return wrap

    def _open_create_post(self):
        CreatePostDialog(self.store, self).exec()

    def _rebuild_posts(self):
        while self.posts_grid.count():
            it = self.posts_grid.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        active = [k for k, b in self.post_filters.items() if b.isChecked()]  # empty = all
        posts = []  # no posts stored yet — filtering will apply here later
        if active:
            posts = [p for p in posts if p.get("platform") in active]
        if not posts:
            empty = QLabel("No posts yet." if not active else "No posts for the selected platforms.")
            empty.setObjectName("Muted")
            self.posts_grid.addWidget(empty, 0, 0)

    def _references_tab(self):
        wrap = QWidget(); wrap.setObjectName("Pane")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(22, 20, 22, 22)
        lay.setSpacing(16)

        # toolbar: add link + favorite/delete for the current selection
        addrow = QHBoxLayout(); addrow.setSpacing(9)
        self.ref_input = QLineEdit(); self.ref_input.setPlaceholderText("Paste post link…")
        self.ref_input.returnPressed.connect(self._add_reference)
        addbtn = QPushButton("Add reference"); addbtn.setObjectName("Primary"); addbtn.setCursor(Qt.PointingHandCursor)
        addbtn.clicked.connect(self._add_reference)
        self.fav_btn = QPushButton("★"); self.fav_btn.setObjectName("FavBtn")
        self.fav_btn.setToolTip("Favorite selected"); self.fav_btn.setCursor(Qt.PointingHandCursor)
        self.fav_btn.setEnabled(False); self.fav_btn.clicked.connect(self._favorite_selected)
        self.del_sel_btn = QPushButton("🗑"); self.del_sel_btn.setObjectName("DelBtn")
        self.del_sel_btn.setToolTip("Delete selected"); self.del_sel_btn.setCursor(Qt.PointingHandCursor)
        self.del_sel_btn.setEnabled(False); self.del_sel_btn.clicked.connect(self._delete_selected)
        addrow.addWidget(self.ref_input, 1); addrow.addWidget(addbtn)
        addrow.addSpacing(6); addrow.addWidget(self.fav_btn); addrow.addWidget(self.del_sel_btn)
        lay.addLayout(addrow)

        # scrollable board of 3:4 tiles (5 per row, vertical scroll)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ref_board = RefBoard()
        scroll.setWidget(self.ref_board)
        lay.addWidget(scroll, 1)
        return wrap

    def _add_reference(self):
        v = self.ref_input.text().strip()
        if not v:
            return
        title = v.replace("https://", "").replace("http://", "").rstrip("/")[:44] or "New reference"
        seed = len(self.store.references) % 6
        self.store.add_reference(Reference(url=v, title=title, note="added just now", thumb_seed=seed))
        self.ref_input.clear()

    def rebuild_references(self):
        self._selected = set()
        refs = sorted(self.store.references, key=lambda r: not r.favorite)  # favorites first
        cards = []
        for r in refs:
            card = RefCard(r)
            card.open_requested.connect(lambda ref=r: self._open_reference(ref))
            card.selection_toggled.connect(self._on_selection_toggled)
            card.download_requested.connect(lambda url=r.url: self.downloadRequested.emit(url))
            cards.append(card)
        self.ref_board.set_cards(cards)
        self._update_sel_buttons()

    def _on_selection_toggled(self, ref_id, selected):
        if selected:
            self._selected.add(ref_id)
        else:
            self._selected.discard(ref_id)
        self._update_sel_buttons()

    def _update_sel_buttons(self):
        has = bool(self._selected)
        self.fav_btn.setEnabled(has)
        self.del_sel_btn.setEnabled(has)

    def _favorite_selected(self):
        if self._selected:
            self.store.toggle_favorite(list(self._selected))

    def _delete_selected(self):
        if not self._selected:
            return
        n = len(self._selected)
        box = QMessageBox(self); box.setStyleSheet(qss())
        box.setWindowTitle("Delete references")
        box.setText(f"Delete {n} reference{'s' if n > 1 else ''}?")
        box.setInformativeText("Downloaded media files will be removed too.")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Cancel)
        if box.exec() == QMessageBox.Yes:
            self.store.delete_references(list(self._selected))

    def _open_reference(self, ref):
        ReferenceViewer(ref, self).exec()

    # ---------- profile / socials ----------
    def _open_profile(self):
        m = self.store.selected_model
        if not m:
            return
        CharacterProfileDialog(m, self.store, self).exec()

    def _save_social(self, key, value):
        m = self.store.selected_model
        if not m:
            return
        m.ensure_profile()["socials"][key] = value.strip()
        self.store.update_model(notify=False)   # save silently

    # ---------- refresh ----------
    def refresh(self):
        m = self.store.selected_model
        if m is None:
            self.title.setText("No models")
            self.niche.setText("Create one with ＋")
            self.av.clear()
            self.edit_btn.setEnabled(False)
            for e in self.social_edits.values():
                e.blockSignals(True); e.clear(); e.setEnabled(False); e.blockSignals(False)
            return
        self.edit_btn.setEnabled(True)
        self.title.setText(m.name)
        self.niche.setText(m.niche)
        if has_image(m.sheet_path):
            self.av.setPixmap(avatar_from_sheet(m.sheet_path, size=34, radius=9))
        else:
            self.av.setPixmap(avatar_pixmap(m.name, m.avatar_seed, size=34, radius=9))
        img = m.sheet_path if has_image(m.sheet_path) else ""
        self.preview.set_model(m.avatar_seed, "character sheet" if img else "no sheet yet", img)

        # spec rows
        while self.spec_box.count():
            it = self.spec_box.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        for k, v in m.spec.items():
            row = QFrame(); row.setObjectName("SpecRow")
            rl = QHBoxLayout(row); rl.setContentsMargins(0, 9, 0, 9)
            kl = QLabel(k); kl.setObjectName("SpecKey")
            vl = QLabel(str(v)); vl.setObjectName("SpecVal")
            rl.addWidget(kl); rl.addStretch(); rl.addWidget(vl)
            self.spec_box.addWidget(row)

        # socials (Appearance tab)
        socials = m.ensure_profile()["socials"]
        for key, edit_soc in self.social_edits.items():
            edit_soc.blockSignals(True)
            edit_soc.setEnabled(True)
            edit_soc.setText(socials.get(key, ""))
            edit_soc.blockSignals(False)
