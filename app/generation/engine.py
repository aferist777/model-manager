"""One worker for every generation, whatever the provider.

The dialog does not know which model is configured. It hands over:
  * the mode (t2i / i2i),
  * a prompt builder `prompt_fn(style, beautified_text) -> str`,
  * the reference images and what each one is,
  * whether the user's note + extra images should go through the beautify agent.

The worker resolves the configured model, optionally beautifies, builds the
model-specific payload and runs it `count` times, downloading the bytes."""

import time

from PySide6.QtCore import QThread, Signal

from . import gen_config, registry, timing
from .prompt import BEAUTIFY_SYSTEM, beautify_user_request, strip_banned


class GenJob(QThread):
    progress = Signal(int, int)      # done, total
    note = Signal(str)               # short status shown on the overlay
    finished_ok = Signal(list)       # [(url, bytes)]
    failed = Signal(str)

    def __init__(self, mode, prompt_fn, refs=None, beautify=None, count=1, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.prompt_fn = prompt_fn
        self.refs = list(refs or [])
        self.beautify = beautify or {}       # {"note": str, "images": [paths]}
        self.count = max(1, int(count))
        self.model_id = None

    # ---------- helpers ----------
    def _beautified(self) -> str:
        note = (self.beautify.get("note") or "").strip()
        images = [p for p in (self.beautify.get("images") or []) if p]
        if not note and not images:
            return ""
        if not gen_config.load().get("beautify", True) or not images:
            # no extra images → nothing to interpret, the note goes in as written
            return note
        self.note.emit("Beautifying prompt…")
        try:
            from . import replicate_client as rc
            text = rc.run_text(registry.BEAUTIFY_MODEL, {
                "prompt": beautify_user_request(note, len(images)),
                "images": [rc.to_data_uri(p) for p in images[:10]],
                "system_instruction": BEAUTIFY_SYSTEM,
                "temperature": 0.4,
                "thinking_budget": 0,
            })
            self.note.emit("")
            return strip_banned(text) or note
        except Exception:
            self.note.emit("")
            return note        # agent unavailable → fall back to the raw note

    def _refs_for(self, provider):
        if not self.refs:
            return None
        if provider == "replicate":
            from .replicate_client import to_data_uri
            return [to_data_uri(r) for r in self.refs]
        from .imgbb import to_url
        self.note.emit("Uploading references…")
        urls = [to_url(r) for r in self.refs]
        self.note.emit("")
        return urls

    def _run_one(self, provider, model_id, prompt, refs):
        if provider == "replicate":
            from . import replicate_client as rc
            payload = registry.build_payload(model_id, prompt, refs,
                                             gen_config.slot(self.mode)["params"])
            url = rc.run_image(model_id.split(":")[-1] if ":" in model_id else model_id, payload)
            return url, rc.download(url)
        # kie.ai
        from .kie_client import generate_one, _download
        p = gen_config.slot(self.mode)["params"]
        url = generate_one(prompt, refs, aspect_ratio=registry.CHAR_ASPECT,
                           resolution=p.get("resolution", "1K"),
                           output_format=p.get("output_format", "png"))
        return url, _download(url)

    # ---------- thread ----------
    def run(self):
        try:
            slot = gen_config.slot(self.mode)
            model_id = slot["model"]
            self.model_id = model_id
            provider = registry.provider_of(model_id)
            style = registry.style_of(model_id)

            extra = self._beautified()
            refs = self._refs_for(provider) if registry.supports_refs(model_id) else None
            # the prompt may only mention reference images the model can actually see
            prompt = self.prompt_fn(style, extra, bool(refs))

            out = []
            for i in range(self.count):
                started = time.monotonic()
                url, data = self._run_one(provider, model_id, prompt, refs)
                # per-model timing feeds the estimate shown in the settings popup
                timing.record(timing.model_key(model_id), time.monotonic() - started, 1)
                out.append((url, data))
                self.progress.emit(i + 1, self.count)
            self.finished_ok.emit(out)
        except Exception as e:
            self.failed.emit(str(e))
