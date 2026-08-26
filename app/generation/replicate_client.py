"""Replicate REST client.

Official models are called through /v1/models/{owner}/{name}/predictions, so no
version pinning is needed. Local reference images are sent as data URIs —
Replicate accepts them directly, which saves a round-trip through imgbb."""

import base64
import json
import mimetypes
import time
import urllib.request
import urllib.error
from pathlib import Path

from ..config import get_key

BASE = "https://api.replicate.com/v1"
UA = "ModelManager/0.12"
POLL = 1.5
TIMEOUT = 300


def _headers(key, json_body=True):
    h = {"Authorization": f"Bearer {key}", "User-Agent": UA}
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def _key():
    k = get_key("replicate")
    if not k:
        raise RuntimeError("No Replicate API key. Add it in Settings → API keys.")
    return k


def _request(url, key, body=None, method="GET"):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(key, body is not None),
                                 method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        raise RuntimeError(f"Replicate {e.code}: {detail}") from None


def to_data_uri(item) -> str:
    """http(s) URL passes through; a path or raw bytes becomes a data URI."""
    if isinstance(item, (bytes, bytearray)):
        return "data:image/png;base64," + base64.b64encode(bytes(item)).decode()
    s = str(item)
    if s.startswith(("http://", "https://", "data:")):
        return s
    p = Path(s)
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def run(model_ref: str, payload: dict, timeout: int = TIMEOUT):
    """Create a prediction, wait for it, return the raw `output`."""
    key = _key()
    pred = _request(f"{BASE}/models/{model_ref}/predictions", key, {"input": payload}, "POST")
    pred_id = pred.get("id")
    if not pred_id:
        raise RuntimeError(f"Replicate did not start a prediction: {pred}")

    deadline = time.time() + timeout
    while time.time() < deadline:
        status = pred.get("status")
        if status == "succeeded":
            return pred.get("output")
        if status in ("failed", "canceled"):
            raise RuntimeError(pred.get("error") or f"prediction {status}")
        time.sleep(POLL)
        pred = _request(f"{BASE}/predictions/{pred_id}", key)
    raise TimeoutError("Replicate prediction timed out")


def run_image(model_ref: str, payload: dict) -> str:
    """Run an image model and return the first output URL."""
    out = run(model_ref, payload)
    if isinstance(out, str):
        return out
    if isinstance(out, list) and out:
        first = out[0]
        return first if isinstance(first, str) else str(first)
    raise RuntimeError("model returned no image")


def run_text(model_ref: str, payload: dict) -> str:
    """Run a text model (the beautify agent) and return the joined text."""
    out = run(model_ref, payload, timeout=120)
    if isinstance(out, list):
        return "".join(str(x) for x in out).strip()
    return str(out or "").strip()


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()
