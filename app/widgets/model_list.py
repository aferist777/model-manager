"""Left pane: model list with add button."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame,
    QMessageBox
)

from ..avatar import avatar_pixmap, avatar_from_sheet, has_image
from ..theme import C, qss


class ModelCard(QFrame):
    clicked = Signal()
    deleteRequested = Signal()

    def __init__(self, model, seed, selected=False):
        super().__init__()
        self.setObjectName("ModelCard")
        self.setProperty("selected", "true" if selected else "false")
        self.setCursor(Qt.PointingHandCursor)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 5, 10, 5)
        row.setSpacing(10)

        av = QLabel()
        if has_image(model.sheet_path):
            av.setPixmap(avatar_from_sheet(model.sheet_path, size=32, radius=8))
        else:
            av.setPixmap(avatar_pixmap(model.name, seed, size=32, radius=8))
        av.setFixedSize(32, 32)
        row.addWidget(av)

        name = QLabel(model.name)
        name.setObjectName("ModelName")
        row.addWidget(name)
        row.addStretch()

        # delete — only shown while the pointer is over the row
        self.del_btn = QPushButton("×")
        self.del_btn.setObjectName("CardDel")
        self.del_btn.setFixedSize(20, 20)
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setToolTip(f"Delete “{model.name}”")
        self.del_btn.clicked.connect(self.deleteRequested.emit)
        self.del_btn.hide()
        row.addWidget(self.del_btn)

    def _show_del(self, on):
        # the list rebuilds under the pointer (every save fires modelsChanged), so
        # a hover event can land on a card whose C++ side is already gone
        try:
            self.del_btn.setVisible(on)
        except RuntimeError:
            pass

    def enterEvent(self, e):
        self._show_del(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._show_del(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self.clicked.emit()
        super().mousePressEvent(e)


class ModelListPane(QWidget):
    addRequested = Signal()

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.setObjectName("Pane")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # header
        head = QWidget()
        head.setObjectName("PaneHead")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(16, 7, 12, 7)
        title = QLabel("Models")
        title.setObjectName("PaneTitle")
        self.count = QLabel("0")
        self.count.setObjectName("PaneCount")
        hl.addWidget(title)
        hl.addWidget(self.count)
        hl.addStretch()
        root.addWidget(head)

        # scroll list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body = QWidget()
        self.body.setObjectName("Pane")
        self.list_layout = QVBoxLayout(self.body)
        self.list_layout.setContentsMargins(10, 10, 10, 10)
        self.list_layout.setSpacing(7)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.body)
        root.addWidget(self.scroll)

        store.modelsChanged.connect(self.rebuild)
        store.selectionChanged.connect(lambda _: self.rebuild())
        self.rebuild()

    def rebuild(self):
        # clear
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)      # detach now — deleteLater alone leaves it visible
                w.deleteLater()
        for i, m in enumerate(self.store.models):
            card = ModelCard(m, m.avatar_seed, selected=(i == self.store.current))
            card.clicked.connect(lambda idx=i: self.store.select(idx))
            card.deleteRequested.connect(lambda idx=i: self._confirm_delete(idx))
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)
        self.count.setText(str(len(self.store.models)))

    def _confirm_delete(self, index):
        """Deleting a model throws away its portrait and body too, so ask first."""
        if not (0 <= index < len(self.store.models)):
            return
        model = self.store.models[index]
        box = QMessageBox(self)
        box.setStyleSheet(qss())
        box.setWindowTitle("Delete model")
        box.setText(f"Delete model “{model.name}”?")
        box.setInformativeText("Its sheet, images and profile are removed for good.")
        box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
        box.setDefaultButton(QMessageBox.Cancel)
        if box.exec() == QMessageBox.Yes:
            self.store.delete_model(index)
