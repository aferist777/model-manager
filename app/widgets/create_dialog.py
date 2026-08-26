"""New model: reference photo → Gemini description → generated character.

Top: name + gender. Left: the user's reference photos. Right: the generated
image. One button in the middle runs Gemini analysis then the configured T2I
model. Generation settings live behind the gear (unchanged)."""

from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QWidget, QGridLayout, QFileDialog, QMessageBox, QSizePolicy
)

from ..generation.portrait import AnalyzeGenerateJob
from .draft_view import DraftView
from .gen_overlay import GenOverlay
from .gen_settings_dialog import GenSettingsDialog
from ..theme import qss, C

GENDERS = ["Female", "Male", "Androgynous"]
SLOTS = 4          # reference photo slots


class CreateModelDialog(QDialog):
    def __init__(self, parent=None, model=None, store=None):
        super().__init__(parent)
        self.model = model            # regenerating an existing model, or None
        self.store = store
        self.setWindowTitle("Regenerate" if model else "New model")
        self.setModal(True)
        self.setMinimumSize(920, 660)

        self.sources = [""] * SLOTS   # reference photo paths
        self.slot_btns = []
        self.result_bytes = None
        self.result_prompt = ""
        self.result_desc = ""
        self.job = None
        self._locked = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14); root.setSpacing(14)

        root.addLayout(self._build_header())
        root.addLayout(self._build_columns(), 1)
        root.addLayout(self._build_center())
        root.addLayout(self._build_footer())

        # overlay on the generated side
        self.overlay = GenOverlay(self.generated)

        if model is not None:
            self.name_input.setText(model.name)
            g = (model.appearance or {}).get("gender", "")
            i = self.gender.findText(str(g).capitalize())
            if i >= 0:
                self.gender.setCurrentIndex(i)
        self._update_buttons()

    # ---------- header ----------
    def _build_header(self):
        row = QHBoxLayout(); row.setSpacing(12)
        nl = QVBoxLayout(); nl.setSpacing(5)
        nl.addWidget(self._label("Character name"))
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("e.g. Mia Vance")
        self.name_input.textChanged.connect(self._update_buttons)
        nl.addWidget(self.name_input)
        row.addLayout(nl, 1)

        gl = QVBoxLayout(); gl.setSpacing(5)
        gl.addWidget(self._label("Gender"))
        self.gender = QComboBox(); self.gender.addItems(GENDERS); self.gender.setFixedWidth(160)
        gl.addWidget(self.gender)
        row.addLayout(gl)
        return row

    # ---------- two columns ----------
    def _build_columns(self):
        cols = QHBoxLayout(); cols.setSpacing(16)

        # left — reference photos
        left = QVBoxLayout(); left.setSpacing(8)
        left.addWidget(self._label("Reference photos"))
        hint = QLabel("Upload one or more photos of the character.")
        hint.setObjectName("Muted"); hint.setWordWrap(True)
        left.addWidget(hint)
        grid = QGridLayout(); grid.setSpacing(10)
        for i in range(SLOTS):
            b = QPushButton("+"); b.setObjectName("PhotoSlot")
            b.setCursor(Qt.PointingHandCursor)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            b.setToolTip("Add a reference photo. Right-click to clear.")
            b.clicked.connect(lambda _=False, idx=i: self._pick(idx))
            b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda _p, idx=i: self._clear(idx))
            grid.addWidget(b, i // 2, i % 2)
            self.slot_btns.append(b)
        gh = QWidget(); gh.setLayout(grid)
        left.addWidget(gh, 1)
        lw = QWidget(); lw.setLayout(left)
        cols.addWidget(lw, 1)

        # right — generated image
        right = QVBoxLayout(); right.setSpacing(8)
        right.addWidget(self._label("Generated"))
        self.generated = DraftView("no image yet")
        right.addWidget(self.generated, 1)
        rw = QWidget(); rw.setLayout(right)
        cols.addWidget(rw, 1)
        return cols

    # ---------- center button ----------
    def _build_center(self):
        row = QHBoxLayout()
        self.gen_btn = QPushButton("Analyze && Generate"); self.gen_btn.setObjectName("Primary")
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.clicked.connect(self._run)
        self.status = QLabel(""); self.status.setObjectName("Muted"); self.status.setWordWrap(True)
        row.addStretch(); row.addWidget(self.gen_btn); row.addStretch()
        wrap = QVBoxLayout(); wrap.addLayout(row)
        srow = QHBoxLayout(); srow.addStretch(); srow.addWidget(self.status); srow.addStretch()
        wrap.addLayout(srow)
        return wrap

    def _build_footer(self):
        foot = QHBoxLayout(); foot.setSpacing(10)
        self.cancel_btn = QPushButton("Cancel"); self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        self.gear_btn = QPushButton("⚙"); self.gear_btn.setObjectName("IconBtn")
        self.gear_btn.setCursor(Qt.PointingHandCursor); self.gear_btn.setToolTip("Generation settings")
        self.gear_btn.clicked.connect(lambda: GenSettingsDialog(self).exec())
        self.create_btn = QPushButton("Save" if self.model else "Create model")
        self.create_btn.setObjectName("Primary"); self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.clicked.connect(self.accept)
        foot.addWidget(self.cancel_btn); foot.addStretch()
        foot.addWidget(self.gear_btn); foot.addWidget(self.create_btn)
        return foot

    def _label(self, text):
        l = QLabel(text); l.setObjectName("FieldLabel"); return l

    # ---------- reference photos ----------
    def _pick(self, idx):
        path, _ = QFileDialog.getOpenFileName(self, "Reference photo", "",
                                              "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            self.sources[idx] = path
            self._refresh_slot(idx)
            self._update_buttons()

    def _clear(self, idx):
        self.sources[idx] = ""
        self._refresh_slot(idx)
        self._update_buttons()

    def _refresh_slot(self, idx):
        b = self.slot_btns[idx]
        p = self.sources[idx]
        if p and Path(p).exists():
            b.setIcon(QIcon(QPixmap(p).scaled(220, 220, Qt.KeepAspectRatioByExpanding,
                                              Qt.SmoothTransformation)))
            b.setIconSize(QSize(b.width() - 8, b.height() - 8)); b.setText("")
        else:
            b.setIcon(QIcon()); b.setText("+")

    def resizeEvent(self, e):
        for i in range(SLOTS):
            self._refresh_slot(i)
        super().resizeEvent(e)

    def _uploaded(self):
        return [p for p in self.sources if p and Path(p).exists()]

    # ---------- run ----------
    def _run(self):
        imgs = self._uploaded()
        if not imgs:
            return
        self._lock(True)
        self.status.setText("")
        self.overlay.start("portrait", 1)
        self.job = AnalyzeGenerateJob(imgs, self.gender.currentText(),
                                      self.name_input.text().strip(), parent=self)
        self.job.note.connect(self.overlay.set_note)
        self.job.progress.connect(self.overlay.set_progress)
        self.job.finished_ok.connect(self._on_ok)
        self.job.refused.connect(self._on_refused)
        self.job.failed.connect(self._on_failed)
        self.job.start()

    def _on_ok(self, data, prompt, desc):
        self.job = None
        self.overlay.stop(True)
        self.result_bytes = bytes(data)
        self.result_prompt = prompt
        self.result_desc = desc
        self.generated.set_items([self.result_bytes])
        self._lock(False)
        self._update_buttons()
        self.status.setText("Done. Create model to keep it, or Analyze & Generate again.")

    def _on_failed(self, msg):
        self.job = None
        self.overlay.stop(False)
        self._lock(False)
        self._update_buttons()
        self.status.setText(f"⚠ {msg}")

    def _on_refused(self, msg):
        self.job = None
        self.overlay.stop(False)
        self._lock(False)
        self._update_buttons()
        box = QMessageBox(self); box.setStyleSheet(qss())
        box.setWindowTitle("Model refused")
        box.setText("The model would not generate this character.")
        box.setInformativeText("Try a different T2I model in the ⚙ settings, or edit the photos.")
        box.setDetailedText(msg)
        box.exec()
        self.status.setText("⚠ refused")

    # ---------- enabling ----------
    def _lock(self, on):
        if on:
            ws = [self.name_input, self.gender, self.gen_btn, self.create_btn,
                  self.gear_btn] + list(self.slot_btns)
            self._locked = [(w, w.isEnabled()) for w in ws]
            for w, _ in self._locked:
                w.setEnabled(False)
        else:
            for w, was in self._locked:
                try:
                    w.setEnabled(was)
                except RuntimeError:
                    pass
            self._locked = []

    def _update_buttons(self):
        if self._locked:
            return
        self.gen_btn.setEnabled(bool(self._uploaded()))
        self.create_btn.setEnabled(self.result_bytes is not None)

    # ---------- result ----------
    def get_result(self):
        if self.result_bytes is None:
            return None
        return {
            "name": self.name_input.text().strip() or "New Model",
            "gender": self.gender.currentText(),
            "image_bytes": self.result_bytes,
            "prompt": self.result_prompt,
            "description": self.result_desc,
            "source_images": self._uploaded(),
        }
