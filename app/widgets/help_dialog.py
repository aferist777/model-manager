"""Help -> changelog popup: version + last update date + what was added."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QFrame
)

from ..version import APP_VERSION, CHANGELOG
from ..theme import qss, C


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setModal(True)
        self.setFixedWidth(440)
        self.setStyleSheet(qss())

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(6)

        title = QLabel("Model Manager"); title.setObjectName("DlgTitle")
        root.addWidget(title)
        last = CHANGELOG[0] if CHANGELOG else {"date": "—"}
        ver = QLabel(f"Version {APP_VERSION} · updated {last.get('date', '—')}")
        ver.setObjectName("Muted")
        root.addWidget(ver)
        root.addSpacing(10)

        head = QLabel("CHANGELOG"); head.setObjectName("SpecHead")
        root.addWidget(head)
        root.addSpacing(6)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(340)
        body = QWidget(); body.setObjectName("Pane")
        bl = QVBoxLayout(body); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(16)
        for entry in CHANGELOG:
            block = QVBoxLayout(); block.setSpacing(5)
            vrow = QLabel(f"v{entry['version']}  ·  {entry['date']}")
            vrow.setStyleSheet(f"color:{C['accent']}; font-weight:700; font-size:12px;")
            block.addWidget(vrow)
            for ch in entry["changes"]:
                item = QLabel(f"•  {ch}")
                item.setObjectName("Muted"); item.setWordWrap(True)
                block.addWidget(item)
            holder = QWidget(); holder.setLayout(block)
            bl.addWidget(holder)
        bl.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

        btns = QHBoxLayout()
        close = QPushButton("Close"); close.setObjectName("Primary"); close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        btns.addStretch(); btns.addWidget(close)
        root.addLayout(btns)
