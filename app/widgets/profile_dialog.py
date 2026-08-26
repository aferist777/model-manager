"""Character profile: name, niche, the casting write-up (read-only), the
appearance sheet and socials. Generate re-runs casting and rebinds the sheet.
Save bottom-right; closing with unsaved edits prompts Save / Discard / Cancel."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QWidget, QScrollArea, QFrame, QMessageBox
)

from ..models_data import SOCIALS
from ..avatar import has_image
from .lightbox import enable_lightbox
from ..theme import qss, C


class CharacterProfileDialog(QDialog):
    def __init__(self, model, store, parent=None):
        super().__init__(parent)
        self.model = model
        self.store = store
        self._dirty = False
        self.setWindowTitle("Character profile")
        self.setModal(True)
        self.setMinimumSize(1000, 560)
        self.resize(1080, 600)
        self.setStyleSheet(qss())

        model.ensure_profile()
        p = model.profile

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(12)

        t = QLabel("Character profile"); t.setObjectName("DlgTitle")
        root.addWidget(t)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget(); body.setObjectName("Pane")
        form = QVBoxLayout(body); form.setContentsMargins(0, 0, 8, 0); form.setSpacing(12)

        # one row: portrait · identity · texts · socials (three info columns)
        top = QHBoxLayout(); top.setSpacing(18)
        pcol = QVBoxLayout(); pcol.setSpacing(6)
        self.portrait = QLabel(); self.portrait.setFixedSize(258, 172); self.portrait.setAlignment(Qt.AlignCenter)
        self._show_sheet()
        enable_lightbox(self.portrait,
                        lambda: self.model.sheet_path if has_image(self.model.sheet_path) else None, self)
        gen = QPushButton("Generate"); gen.setCursor(Qt.PointingHandCursor)
        gen.setToolTip("Re-cast and rebuild the character sheet")
        gen.clicked.connect(self._generate_portrait)
        pcol.addWidget(self.portrait); pcol.addWidget(gen); pcol.addStretch()
        top.addLayout(pcol)

        # ---- column 1: identity + read-only appearance spec ----
        c1 = QVBoxLayout(); c1.setSpacing(12)
        self.name = QLineEdit(model.name)
        c1.addWidget(self._field("Name", self.name))
        self.niche = QLineEdit(model.niche)
        c1.addWidget(self._field("Niche / vibe", self.niche))

        spec_pairs = list((model.spec or {}).items()) or [("—", "no sheet yet")]
        spec_head = QLabel("APPEARANCE"); spec_head.setObjectName("SpecHead")
        c1.addWidget(spec_head)
        sgrid = QGridLayout(); sgrid.setContentsMargins(0, 0, 0, 0)
        sgrid.setHorizontalSpacing(10); sgrid.setVerticalSpacing(5)
        for i, (k, v) in enumerate(spec_pairs):
            kl = QLabel(k); kl.setObjectName("SpecKey")
            vl = QLabel(str(v)); vl.setObjectName("SpecVal")
            sgrid.addWidget(kl, i, 0); sgrid.addWidget(vl, i, 1)
        sgrid.setColumnStretch(1, 1)
        sw = QWidget(); sw.setLayout(sgrid)
        c1.addWidget(sw)
        c1.addStretch()
        top.addLayout(c1, 1)

        # ---- column 2: the casting director's write-up (read-only) ----
        c2 = QVBoxLayout(); c2.setSpacing(12)
        self.description = QTextEdit(model.description or "")
        self.description.setReadOnly(True)
        self.description.setMinimumHeight(280)
        c2.addWidget(self._field("Character", self.description))
        c2.addStretch()
        top.addLayout(c2, 1)

        # ---- column 3: socials ----
        c3 = QVBoxLayout(); c3.setSpacing(10)
        soc_head = QLabel("SOCIAL MEDIA"); soc_head.setObjectName("SpecHead")
        c3.addWidget(soc_head)
        self.socials = {}
        for key, label in SOCIALS:
            edit = QLineEdit(p.get("socials", {}).get(key, ""))
            edit.setPlaceholderText("@handle or link")
            c3.addWidget(self._field(label, edit))
            self.socials[key] = edit
        c3.addStretch()
        top.addLayout(c3, 1)

        topw = QWidget(); topw.setLayout(top)
        form.addWidget(topw)
        form.addStretch()

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # footer
        foot = QHBoxLayout(); foot.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setCursor(Qt.PointingHandCursor); cancel.clicked.connect(self.reject)
        save = QPushButton("Save"); save.setObjectName("Primary"); save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save)
        foot.addWidget(cancel); foot.addStretch(); foot.addWidget(save)
        root.addLayout(foot)

        # dirty tracking
        for w in [self.name, self.niche] + list(self.socials.values()):
            w.textEdited.connect(self._mark_dirty)

    def _show_sheet(self):
        if has_image(self.model.sheet_path):
            pm = QPixmap(self.model.sheet_path).scaled(258, 172, Qt.KeepAspectRatio,
                                                       Qt.SmoothTransformation)
            self.portrait.setPixmap(pm); self.portrait.setStyleSheet("border-radius:10px;")
        else:
            self.portrait.setPixmap(QPixmap())
            self.portrait.setText("character\nsheet")
            self.portrait.setStyleSheet(
                f"border:1px dashed {C['line']}; border-radius:10px; "
                f"color:{C['ink_mute']}; font-size:12px;")

    def _field(self, label, widget):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(6)
        lbl = QLabel(label); lbl.setObjectName("FieldLabel")
        v.addWidget(lbl); v.addWidget(widget)
        return w

    def _mark_dirty(self, *args):
        self._dirty = True

    def _save(self):
        self.model.name = self.name.text().strip() or self.model.name
        self.model.niche = self.niche.text().strip() or "unassigned"
        p = self.model.ensure_profile()
        for key, edit in self.socials.items():
            p["socials"][key] = edit.text().strip()
        self.store.update_model()   # save + notify (name/list refresh)
        self._dirty = False
        self.accept()

    def _generate_portrait(self):
        # re-runs the photo→generate flow on top of this popup and rebinds the image
        from .create_dialog import CreateModelDialog
        from ..store import DATA_DIR
        dlg = CreateModelDialog(self, model=self.model, store=self.store)
        dlg.setStyleSheet(qss())
        if not dlg.exec():
            return
        res = dlg.get_result()
        if not res:
            return
        path = DATA_DIR / "models" / f"{self.model.id}_sheet.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(res["image_bytes"])
        self.model.sheet_path = str(path)
        self.model.appearance = {"gender": res.get("gender", "")}
        self.model.sheet_prompt = res.get("prompt", "")
        self.model.description = res.get("description", "")
        self.description.setPlainText(self.model.description)
        if self.store is not None:
            self.store.update_model()
        self._show_sheet()

    # ---- unsaved-changes guard ----
    def _confirm_discard(self) -> bool:
        """Return True if it's OK to close (saved or discarded)."""
        if not self._dirty:
            return True
        box = QMessageBox(self)
        box.setStyleSheet(qss())
        box.setWindowTitle("Unsaved changes")
        box.setText("This character has unsaved changes.")
        box.setInformativeText("Save them before closing?")
        box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Save)
        choice = box.exec()
        if choice == QMessageBox.Save:
            self._save()
            return True
        if choice == QMessageBox.Discard:
            return True
        return False  # Cancel

    def reject(self):
        if self._confirm_discard():
            super().reject()

    def closeEvent(self, e):
        if self._confirm_discard():
            e.accept()
        else:
            e.ignore()
