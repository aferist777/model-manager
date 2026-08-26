"""imgbb image hosting.

kie.ai's `image_input` only accepts public URLs, so local files (the mannequin,
the user's extra-detail references, a portrait restored from disk) have to be
hosted first. Uploads are cached by content hash in data/imgbb_cache.json and
reused until they expire, so the same file is uploaded once."""

import base64
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from ..config import get_key

API = "https://api.imgbb.com/1/upload"
EXPIRATION = 2592000          # 30 days — long enough to reuse, short enough to not litter

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CACHE_FILE = DATA_DIR / "imgbb_cache.json"


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def _save_cache(data: dict):
    try:
        DATA_DIR.mkdir(exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _cached(digest: str):
    rec = _load_cache().get(digest)
    if not rec:
        return None
    if rec.get("expires_at", 0) and rec["expires_at"] < time.time() + 300:
        return None       # about to expire — re-upload
    return rec.get("url")


def _remember(digest: str, url: str):
    data = _load_cache()
    data[digest] = {"url": url, "expires_at": time.time() + EXPIRATION}
    _save_cache(data)


def upload_bytes(data: bytes, name: str = "ref") -> str:
    """Upload raw image bytes, return a public URL. Cached by content hash."""
    digest = hashlib.sha1(data).hexdigest()
    hit = _cached(digest)
    if hit:
        return hit

    key = get_key("imgbb")
    if not key:
        raise RuntimeError("No imgbb API key. Add it in Settings → API keys.")

    body = urllib.parse.urlencode({
        "key": key,
        "image": base64.b64encode(data).decode(),
        "name": name,
        "expiration": str(EXPIRATION),
    }).encode()
    req = urllib.request.Request(API, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read().decode())
    if not res.get("success"):
        raise RuntimeError(f"imgbb upload failed: {res.get('error') or res}")
    url = (res.get("data") or {}).get("url")
    if not url:
        raise RuntimeError("imgbb returned no URL")
    _remember(digest, url)
    return url


def upload_path(path) -> str:
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"file not found: {p}")
    return upload_bytes(p.read_bytes(), name=p.stem)


def to_url(item) -> str:
    """Accepts an http(s) URL (returned as-is), a local path, or raw bytes."""
    if isinstance(item, (bytes, bytearray)):
        return upload_bytes(bytes(item))
    s = str(item)
    if s.startswith("http://") or s.startswith("https://"):
        return s
    return upload_path(s)
