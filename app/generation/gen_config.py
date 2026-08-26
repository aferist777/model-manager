"""Generation settings, split per mode.

    {
      "t2i": {"provider": "replicate", "model": "...", "params": {...}},
      "i2i": {"provider": "replicate", "model": "...", "params": {...}},
      "drafts": 2,
      "beautify": true
    }

t2i drives fresh generations (portrait, full body from scratch), i2i drives
everything that edits an existing image (per-param 'g', additional details,
face-onto-body). Persisted to data/gen_settings.json."""

import json
from pathlib import Path

from . import registry

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
FILE = DATA_DIR / "gen_settings.json"

MODES = [(registry.T2I, "T2I · generate"), (registry.I2I, "I2I · edit")]


def _slot(mode: str) -> dict:
    model_id = registry.DEFAULTS[mode]
    return {"provider": registry.provider_of(model_id), "model": model_id,
            "params": registry.param_defaults(model_id)}


def defaults() -> dict:
    return {registry.T2I: _slot(registry.T2I), registry.I2I: _slot(registry.I2I),
            "drafts": 2, "beautify": True}


def load() -> dict:
    cfg = defaults()
    if FILE.exists():
        try:
            raw = json.loads(FILE.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        if isinstance(raw, dict):
            for mode in (registry.T2I, registry.I2I):
                slot = raw.get(mode)
                if isinstance(slot, dict) and slot.get("model") in registry.MODEL_BY_ID:
                    merged = registry.param_defaults(slot["model"])
                    merged.update(slot.get("params") or {})
                    cfg[mode] = {"provider": registry.provider_of(slot["model"]),
                                 "model": slot["model"], "params": merged}
            if str(raw.get("drafts", "")).isdigit():
                cfg["drafts"] = int(raw["drafts"])
            if "beautify" in raw:
                cfg["beautify"] = bool(raw["beautify"])
    return cfg


def save(cfg: dict):
    FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def slot(mode: str) -> dict:
    return load()[mode]


def drafts() -> int:
    return max(1, min(4, int(load().get("drafts", 2))))
