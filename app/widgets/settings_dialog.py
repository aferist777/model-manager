"""Settings dialog. For now: API keys for neural-net aggregators.
Keys are saved to the OS credential store (keyring). Add more sections later."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QWidget
)

from ..config import PROVIDERS, get_key, set_key
from ..theme import qss


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setFixedWidth(460)
        self.setStyleSheet(qss())

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        t = QLabel("API keys"); t.setObjectName("DlgTitle")
        root.addWidget(t)
        sub = QLabel("Keys for AI aggregators. Stored in Windows Credential Manager, not in project files.")
        sub.setObjectName("Muted"); sub.setWordWrap(True)
        root.addWidget(sub)

        self.inputs = {}
        for provider, title in PROVIDERS:
            lbl = QLabel(title); lbl.setObjectName("FieldLabel")
            root.addWidget(lbl)
            row = QHBoxLayout(); row.setSpacing(8)
            edit = QLineEdit(get_key(provider))
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText("not set")
            row.addWidget(edit, 1)
            self.inputs[provider] = edit
            root.addLayout(row)

        show = QCheckBox("Show keys")
        show.toggled.connect(self._toggle_echo)
        root.addWidget(show)

        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setCursor(Qt.PointingHandCursor); cancel.clicked.connect(self.reject)
        save = QPushButton("Save keys"); save.setObjectName("Primary"); save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(save)
        root.addLayout(btns)

    def _toggle_echo(self, on):
        mode = QLineEdit.Normal if on else QLineEdit.Password
        for e in self.inputs.values():
            e.setEchoMode(mode)

    def _save(self):
        for provider, edit in self.inputs.items():
            val = edit.text().strip()
            # only overwrite when the field is non-empty so we don't wipe an existing key by accident
            if val:
                set_key(provider, val)
        self.accept()
