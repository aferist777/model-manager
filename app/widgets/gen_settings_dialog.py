"""Generation settings: one column per mode.

Left  — T2I, used when an image is generated from scratch (portrait, body).
Right — I2I, used for everything that edits an existing image.

Each column: aggregator → model → the model's description, its price and the
average generation time actually measured in this app → that model's own
parameters, each with a one-line explanation."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QWidget,
    QCheckBox, QFrame, QScrollArea
)

from ..generation import gen_config, registry, timing
from ..theme import qss, C


class ModeColumn(QWidget):
    def __init__(self, mode, title, cfg, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.cfg = cfg
        self.param_widgets = {}

        col = QVBoxLayout(self); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(8)
        head = QLabel(title.upper()); head.setObjectName("SpecHead")
        col.addWidget(head)

        col.addWidget(self._label("Aggregator"))
        self.provider = QComboBox()
        for key, name in registry.PROVIDERS:
            self.provider.addItem(name, key)
        idx = self.provider.findData(cfg.get("provider", "replicate"))
        self.provider.setCurrentIndex(max(0, idx))
        self.provider.currentIndexChanged.connect(self._rebuild_models)
        col.addWidget(self.provider)

        col.addWidget(self._label("Model"))
        self.model = QComboBox()
        self.model.currentIndexChanged.connect(self._on_model)
        col.addWidget(self.model)

        self.info = QLabel(); self.info.setObjectName("Muted"); self.info.setWordWrap(True)
        col.addWidget(self.info)
        self.price = QLabel(); self.price.setObjectName("PriceLine"); self.price.setWordWrap(True)
        col.addWidget(self.price)
        self.eta = QLabel(); self.eta.setObjectName("EtaLine"); self.eta.setWordWrap(True)
        col.addWidget(self.eta)

        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setObjectName("Sep")
        col.addWidget(line)

        self.params_host = QWidget()
        self.params_layout = QVBoxLayout(self.params_host)
        self.params_layout.setContentsMargins(0, 0, 0, 0); self.params_layout.setSpacing(9)
        col.addWidget(self.params_host)
        col.addStretch()

        self._rebuild_models()

    def _label(self, text):
        l = QLabel(text); l.setObjectName("FieldLabel"); return l

    def _rebuild_models(self):
        provider = self.provider.currentData()
        self.model.blockSignals(True)
        self.model.clear()
        for m in registry.models_for(self.mode, provider):
            self.model.addItem(m["label"], m["id"])
        idx = self.model.findData(self.cfg.get("model"))
        self.model.setCurrentIndex(idx if idx >= 0 else 0)
        self.model.blockSignals(False)
        self._on_model()

    def _on_model(self):
        model_id = self.model.currentData()
        if not model_id:
            return
        m = registry.MODEL_BY_ID[model_id]
        refs = f"up to {m['max_refs']} refs" if m["max_refs"] else "no refs"
        self.info.setText(f"{m['desc']}  ({refs})")
        self.price.setText(f"Price: {m['price']}")
        avg, n = timing.stats(timing.model_key(model_id))
        self.eta.setText(f"Time: ~{timing.human(avg)} per image ({n} runs measured)" if avg
                         else "Time: measured after the first run")
        self._rebuild_params(model_id)

    def _rebuild_params(self, model_id):
        while self.params_layout.count():
            it = self.params_layout.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None); w.deleteLater()
        self.param_widgets = {}
        saved = self.cfg.get("params", {}) if self.cfg.get("model") == model_id else {}
        for p in registry.MODEL_BY_ID[model_id]["params"]:
            self.params_layout.addWidget(self._label(p["label"]))
            combo = QComboBox()
            combo.addItems([str(o) for o in p["options"]])
            combo.setCurrentText(str(saved.get(p["key"], p["default"])))
            self.params_layout.addWidget(combo)
            hint = QLabel(p["desc"]); hint.setObjectName("ParamHint"); hint.setWordWrap(True)
            self.params_layout.addWidget(hint)
            self.param_widgets[p["key"]] = combo

    def result(self) -> dict:
        return {
            "provider": self.provider.currentData(),
            "model": self.model.currentData(),
            "params": {k: w.currentText() for k, w in self.param_widgets.items()},
        }


class GenSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generation settings")
        self.setModal(True)
        self.setMinimumSize(760, 620)
        self.setStyleSheet(qss())

        self.cfg = gen_config.load()

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16); root.setSpacing(12)
        t = QLabel("Generation settings"); t.setObjectName("DlgTitle")
        root.addWidget(t)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget(); body.setObjectName("Pane")
        cols = QHBoxLayout(body); cols.setContentsMargins(0, 0, 8, 0); cols.setSpacing(22)
        self.columns = {}
        for mode, title in gen_config.MODES:
            c = ModeColumn(mode, title, self.cfg[mode])
            self.columns[mode] = c
            cols.addWidget(c, 1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # shared options
        bottom = QHBoxLayout(); bottom.setSpacing(10)
        bottom.addWidget(self._label("Drafts per run"))
        self.drafts = QComboBox(); self.drafts.addItems(["1", "2", "3", "4"])
        self.drafts.setCurrentText(str(self.cfg.get("drafts", 2)))
        self.drafts.setFixedWidth(70)
        bottom.addWidget(self.drafts)
        self.beautify = QCheckBox("Beautify: let Gemini describe extra reference images before generating")
        self.beautify.setChecked(bool(self.cfg.get("beautify", True)))
        bottom.addSpacing(16); bottom.addWidget(self.beautify); bottom.addStretch()
        root.addLayout(bottom)

        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setCursor(Qt.PointingHandCursor); cancel.clicked.connect(self.reject)
        save = QPushButton("Save"); save.setObjectName("Primary"); save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(save)
        root.addLayout(btns)

    def _label(self, text):
        l = QLabel(text); l.setObjectName("FieldLabel"); return l

    def _save(self):
        cfg = {"drafts": int(self.drafts.currentText()),
               "beautify": self.beautify.isChecked()}
        for mode, col in self.columns.items():
            cfg[mode] = col.result()
        gen_config.save(cfg)
        self.accept()
