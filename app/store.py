"""App state + JSON persistence. A tiny QObject-backed store the widgets
subscribe to via signals."""

import json
from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Signal

from .models_data import Model, Reference

try:
    import keyring  # OS credential store (Windows Credential Manager)
except Exception:  # pragma: no cover
    keyring = None

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
STORE_FILE = DATA_DIR / "models.json"
REFS_FILE = DATA_DIR / "references.json"
WEB_PROFILE_DIR = DATA_DIR / "webprofile"
SETTINGS_FILE = DATA_DIR / "settings.json"
REELS_DIR = DATA_DIR / "reels"

REELS_URL = "https://www.instagram.com/reels/"
_OLD_HOME = ("https://www.instagram.com/", "https://www.instagram.com")

KEYRING_SERVICE = "ModelManager-Instagram"


def _seed_models() -> List[Model]:
    return [
        Model(name="Mia Vance", niche="streetwear · tomboy", status="ready", avatar_seed=0,
              spec={"Gender": "Female", "Ethnicity": "European", "Age": "24", "Body": "Slim", "Height": "170 cm"}),
        Model(name="Kira Snow", niche="soft glam · lifestyle", status="ready", avatar_seed=1,
              spec={"Gender": "Female", "Ethnicity": "Slavic", "Age": "22", "Body": "Petite", "Height": "165 cm"}),
        Model(name="Alex Reyes", niche="fitness · outdoor", status="draft", avatar_seed=2,
              spec={"Gender": "Male", "Ethnicity": "Latino", "Age": "28", "Body": "Athletic", "Height": "182 cm"}),
        Model(name="Noa Kim", niche="minimal · editorial", status="draft", avatar_seed=3,
              spec={"Gender": "Female", "Ethnicity": "Asian", "Age": "26", "Body": "Slim", "Height": "168 cm"}),
    ]


def _seed_references() -> List[Reference]:
    return [
        Reference(title="Golden-hour street set", note="@urban.muse · pose ref", thumb_seed=2),
        Reference(title="Mirror OOTD reel", note="@tomboy.fits · outfit", thumb_seed=3),
        Reference(title="Café candid grid", note="saved · lighting", thumb_seed=4),
        Reference(title="Soft window light", note="@kira.refs · lighting", thumb_seed=1),
    ]


class Store(QObject):
    modelsChanged = Signal()          # model list add/remove/edit
    selectionChanged = Signal(int)
    referencesChanged = Signal()      # global reference board changed

    def __init__(self):
        super().__init__()
        self.models: List[Model] = []
        self.references: List[Reference] = []   # global, shared across models
        self.current = 0
        self._settings = {"ig_url": REELS_URL, "ig_username": ""}
        self.load()
        # start on the Reels page (migrate an old home-page default)
        if self._settings.get("ig_url") in _OLD_HOME:
            self._settings["ig_url"] = REELS_URL
            self.save_settings()

    # ---- persistence ----
    def load(self):
        if STORE_FILE.exists():
            try:
                raw = json.loads(STORE_FILE.read_text(encoding="utf-8"))
                self.models = [Model.from_dict(m) for m in raw]
            except Exception:
                self.models = _seed_models()
        else:
            self.models = _seed_models()
            self.save()
        # global references
        if REFS_FILE.exists():
            try:
                raw = json.loads(REFS_FILE.read_text(encoding="utf-8"))
                self.references = [Reference.from_dict(r) for r in raw]
            except Exception:
                self.references = _seed_references()
        else:
            self.references = _seed_references()
            self.save_references()
        if SETTINGS_FILE.exists():
            try:
                self._settings.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
            except Exception:
                pass

    def save(self):
        STORE_FILE.write_text(
            json.dumps([m.to_dict() for m in self.models], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save_references(self):
        REFS_FILE.write_text(
            json.dumps([r.__dict__ for r in self.references], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save_settings(self):
        SETTINGS_FILE.write_text(json.dumps(self._settings, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- settings ----
    @property
    def ig_url(self) -> str:
        return self._settings.get("ig_url", "https://www.instagram.com/")

    @ig_url.setter
    def ig_url(self, v: str):
        self._settings["ig_url"] = v
        self.save_settings()

    # ---- model ops ----
    @property
    def selected_model(self):
        if 0 <= self.current < len(self.models):
            return self.models[self.current]
        return None

    def select(self, index: int):
        if 0 <= index < len(self.models) and index != self.current:
            self.current = index
            self.selectionChanged.emit(index)

    def add_model(self, model: Model):
        self.models.append(model)
        self.current = len(self.models) - 1
        self.save()
        self.modelsChanged.emit()
        self.selectionChanged.emit(self.current)

    def update_model(self, notify: bool = True):
        """Persist edits made in place to the current model (profile, name…)."""
        self.save()
        if notify:
            self.modelsChanged.emit()

    def delete_model(self, index: int):
        if 0 <= index < len(self.models):
            gone = self.models.pop(index)
            # drop only this model's own image files
            for path in (gone.sheet_path, getattr(gone, "portrait_path", ""),
                         getattr(gone, "body_path", "")):
                if path:
                    try:
                        Path(path).unlink(missing_ok=True)
                    except Exception:
                        pass
            self.current = max(0, min(self.current, len(self.models) - 1))
            self.save()
            self.modelsChanged.emit()
            self.selectionChanged.emit(self.current)

    # ---- reference ops (global board) ----
    def add_reference(self, ref: Reference):
        self.references.insert(0, ref)
        self.save_references()
        self.referencesChanged.emit()

    def delete_reference(self, ref_id: str):
        self.delete_references([ref_id])

    def delete_references(self, ref_ids):
        import shutil
        ids = set(ref_ids)
        gone = [r for r in self.references if r.id in ids]
        self.references = [r for r in self.references if r.id not in ids]
        # remove downloaded media folders
        for r in gone:
            if r.shortcode:
                folder = REELS_DIR / r.shortcode
                if folder.exists():
                    shutil.rmtree(folder, ignore_errors=True)
        self.save_references()
        self.referencesChanged.emit()

    def toggle_favorite(self, ref_ids):
        """If any selected ref is not a favorite, favorite them all; else unfavorite all."""
        ids = set(ref_ids)
        sel = [r for r in self.references if r.id in ids]
        if not sel:
            return
        make_fav = any(not r.favorite for r in sel)
        for r in sel:
            r.favorite = make_fav
        self.save_references()
        self.referencesChanged.emit()

    # ---- instagram credentials ----
    @property
    def ig_username(self) -> str:
        return self._settings.get("ig_username", "")

    def get_ig_password(self) -> str:
        if keyring is None:
            return ""
        try:
            return keyring.get_password(KEYRING_SERVICE, self.ig_username or "default") or ""
        except Exception:
            return ""

    def set_ig_credentials(self, username: str, password: str):
        """Username -> settings.json; password -> OS credential store (keyring)."""
        old_user = self.ig_username
        self._settings["ig_username"] = username
        self.save_settings()
        if keyring is not None:
            try:
                # move password if the account name changed
                if old_user and old_user != username:
                    keyring.delete_password(KEYRING_SERVICE, old_user)
            except Exception:
                pass
            try:
                keyring.set_password(KEYRING_SERVICE, username or "default", password or "")
            except Exception:
                pass

    @property
    def keyring_available(self) -> bool:
        return keyring is not None
