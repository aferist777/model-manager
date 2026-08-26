"""Adaptive generation-time estimates.

Every finished generation records how long ONE image took for a given kind
("portrait", "portrait_edit", "body", "video", …). The stored value is an
exponential moving average, so the estimate tracks the current API speed.

`predict()` returns None until at least one sample exists — the very first
generation of a kind runs without a countdown (it counts up instead)."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
TIMING_FILE = DATA_DIR / "gen_timing.json"

ALPHA = 0.4          # weight of the newest sample
MIN_SAMPLE = 1.0     # ignore absurdly fast results (cached / errored)
MAX_SAMPLE = 900.0


def _load() -> dict:
    if TIMING_FILE.exists():
        try:
            data = json.loads(TIMING_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def _save(data: dict):
    try:
        DATA_DIR.mkdir(exist_ok=True)
        TIMING_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def predict(kind: str, count: int = 1):
    """Expected seconds for `count` images, or None if never measured."""
    rec = _load().get(kind)
    if not rec or not rec.get("avg"):
        return None
    return float(rec["avg"]) * max(1, int(count))


def stats(kind: str):
    """(avg_seconds_per_image, samples) or (None, 0)."""
    rec = _load().get(kind) or {}
    return (float(rec["avg"]), int(rec.get("n", 0))) if rec.get("avg") else (None, 0)


def model_key(model_id: str) -> str:
    return f"model:{model_id}"


def human(seconds) -> str:
    if not seconds:
        return ""
    s = int(round(seconds))
    return f"{s} s" if s < 60 else f"{s // 60} min {s % 60:02d} s"


def record(kind: str, seconds: float, count: int = 1):
    """Fold one measurement (total seconds for `count` images) into the average."""
    count = max(1, int(count))
    per_image = float(seconds) / count
    if not (MIN_SAMPLE <= per_image <= MAX_SAMPLE):
        return
    data = _load()
    rec = data.get(kind) or {}
    avg = rec.get("avg")
    rec["avg"] = per_image if not avg else (ALPHA * per_image + (1 - ALPHA) * float(avg))
    rec["n"] = int(rec.get("n", 0)) + 1
    data[kind] = rec
    _save(data)
