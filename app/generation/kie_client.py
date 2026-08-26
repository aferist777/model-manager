"""kie.ai nano-banana-2-lite client: createTask -> poll recordInfo -> image URLs.
Driven by generation/engine.py, which owns the threading."""

import json
import time
import urllib.request
import urllib.error

from ..config import get_key

BASE = "https://api.kie.ai/api/v1/jobs"
MODEL = "nano-banana-2-lite"


def _headers(key):
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _post(path, body, key):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers=_headers(key), method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def _get(path, key):
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def generate_one(prompt, image_inputs=None, aspect_ratio="3:4",
                 resolution="1K", output_format="png", timeout=150) -> str:
    """Blocking single-image generation. Returns the result image URL."""
    key = get_key("kie")
    if not key:
        raise RuntimeError("No kie.ai API key. Add it in Settings → API keys.")
    inp = {"prompt": prompt, "aspect_ratio": aspect_ratio, "output_format": output_format}
    if resolution:
        inp["resolution"] = resolution
    if image_inputs:
        inp["image_input"] = list(image_inputs)

    res = _post("/createTask", {"model": MODEL, "input": inp}, key)
    task_id = (res.get("data") or {}).get("taskId")
    if not task_id:
        raise RuntimeError(f"createTask failed: {res.get('msg') or res}")

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(3)
        info = _get(f"/recordInfo?taskId={task_id}", key)
        d = info.get("data") or {}
        state = d.get("state")
        if state == "success":
            urls = json.loads(d.get("resultJson") or "{}").get("resultUrls") or []
            if not urls:
                raise RuntimeError("generation succeeded but returned no image")
            return urls[0]
        if state in ("fail", "failed"):
            raise RuntimeError(d.get("failMsg") or "generation failed")
    raise TimeoutError("generation timed out")


def _download(url) -> bytes:
    # the result CDN 403s the default urllib UA — send a browser UA
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


MAX_INPUTS = 14                  # kie.ai caps image_input at 14 references
