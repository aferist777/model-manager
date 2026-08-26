"""Model Manager — desktop entry point."""

import sys
from pathlib import Path

# allow running as `python app/main.py` or `python -m app.main`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter

from app.theme import qss
from app.store import Store, DATA_DIR
from app.models_data import Model
from app.version import APP_VERSION
from app.widgets.model_list import ModelListPane
from app.widgets.workspace import WorkspacePane
from app.widgets.instagram_pane import InstagramPane
from app.widgets.create_dialog import CreateModelDialog
from app.widgets.settings_dialog import SettingsDialog
from app.widgets.help_dialog import HelpDialog

# which appearance fields become the visible Appearance spec
SPEC_KEYS = [("gender", "Gender"), ("age", "Age"), ("ethnicity", "Ethnicity"),
             ("height_build", "Height & build"), ("body", "Body"), ("hair", "Hair")]


def spec_from_appearance(app: dict) -> dict:
    """Short, readable rows for the Appearance tab."""
    out = {}
    for key, label in SPEC_KEYS:
        v = (app or {}).get(key)
        if v:
            out[label] = v if len(str(v)) <= 60 else str(v)[:57].rstrip(" ,") + "…"
    return out


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Model Manager")
        self.resize(1440, 860)
        self.setMinimumSize(1040, 640)

        self.store = Store()
        self._build_menubar()

        central = QWidget(); central.setObjectName("Root")
        lay = QHBoxLayout(central); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)      # 1px was near-impossible to hit
        splitter.setChildrenCollapsible(False)

        self.left = ModelListPane(self.store)
        self.center = WorkspacePane(self.store)
        self.right = InstagramPane(self.store)

        splitter.addWidget(self.left)
        splitter.addWidget(self.center)
        splitter.addWidget(self.right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 3)
        splitter.setSizes([340, 700, 540])

        lay.addWidget(splitter)
        self.setCentralWidget(central)

        self.left.addRequested.connect(self.open_create_dialog)
        if hasattr(self.right, "download_url"):
            self.center.downloadRequested.connect(self.right.download_url)

    def _build_menubar(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        act_new = file_menu.addAction("New model…")
        act_new.triggered.connect(self.open_create_dialog)
        file_menu.addSeparator()
        act_exit = file_menu.addAction("Exit")
        act_exit.triggered.connect(self.close)

        settings_menu = mb.addMenu("Settings")
        act_keys = settings_menu.addAction("API keys…")
        act_keys.triggered.connect(self.open_settings)

        help_menu = mb.addMenu("Help")
        ver = help_menu.addAction(f"Version {APP_VERSION}")
        ver.setEnabled(False)
        help_menu.addSeparator()
        act_log = help_menu.addAction("Changelog…")
        act_log.triggered.connect(self.open_help)

    def open_create_dialog(self):
        dlg = CreateModelDialog(self)
        dlg.setStyleSheet(qss())
        if not dlg.exec():
            return
        res = dlg.get_result()
        if not res:
            return
        app = {"gender": res.get("gender", "")}
        model = Model(
            name=res.get("name") or "New Model",
            niche="unassigned",
            status="ready",
            spec=spec_from_appearance(app),
            appearance=app,
            sheet_prompt=res.get("prompt", ""),
            description=res.get("description", ""),
        )
        models_dir = DATA_DIR / "models"
        models_dir.mkdir(exist_ok=True)
        path = models_dir / f"{model.id}_sheet.png"
        path.write_bytes(res["image_bytes"])
        model.sheet_path = str(path)
        self.store.add_model(model)

    def open_settings(self):
        SettingsDialog(self).exec()

    def open_help(self):
        HelpDialog(self).exec()


def _install_crash_guard():
    """PySide6 aborts the process on an unhandled exception inside a slot, which
    looks to the user like the app just closing. Log it and keep running."""
    import faulthandler
    import traceback
    from PySide6.QtWidgets import QMessageBox

    log = DATA_DIR / "crash.log"
    try:
        faulthandler.enable(open(DATA_DIR / "faulthandler.log", "a", encoding="utf-8"))
    except Exception:
        pass

    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        try:
            with open(log, "a", encoding="utf-8") as f:
                f.write(text + "\n" + "-" * 70 + "\n")
        except Exception:
            pass
        sys.stderr.write(text)
        try:
            box = QMessageBox()
            box.setStyleSheet(qss())
            box.setWindowTitle("Ошибка")
            box.setText("Что-то сломалось, но приложение продолжит работу.")
            box.setDetailedText(text)
            box.setInformativeText(f"Подробности записаны в {log.name}")
            box.exec()
        except Exception:
            pass

    sys.excepthook = hook


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qss())
    _install_crash_guard()
    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
