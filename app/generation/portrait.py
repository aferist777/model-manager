"""Reference photo → Gemini description → generated character.

The user drops one or more photos of a character. Gemini 2.5 Flash looks at them
and writes one structured English prompt describing that person; the prompt then
goes to the configured T2I model, which renders a clean studio image of the same
character in neutral clothing (dressing happens in a separate pipeline)."""

import time

from PySide6.QtCore import QThread, Signal

from . import gen_config, registry, timing
from .prompt import SKIN, GRADE, AVOID_WORDS

VISION_MODEL = "google/gemini-2.5-flash"

ANALYZE_SYSTEM = (
    "You are a prompt engineer for photorealistic text-to-image models. You are given "
    "one or more reference photos of a single person. Study them and write ONE English "
    "prompt (90-150 words) that would let a text-to-image model recreate THAT SAME "
    "person as a believable photograph.\n"
    "Describe, in this order: apparent age, build and proportions, skin tone and texture, "
    "face shape, jaw, cheekbones, nose, lips, brows, eye shape and colour, hair colour, "
    "length, texture and how it is worn, and every distinctive mark (scars, moles, "
    "freckles, birthmarks, tattoos, asymmetries). Be specific and concrete.\n"
    "Rules: describe only the person, never the original background, clothing or pose. "
    "Use positive statements only, never say what is absent. "
    "Never use these words: " + ", ".join(AVOID_WORDS) + ". "
    "Output only the prompt paragraph: no preamble, no quotes, no markdown, no headings."
)

_REFUSAL = ("safety", "flagged", "content policy", "nsfw", "prohibited", "blocked",
            "moderation", "sensitive", "not allowed", "e005", "violat")

# a clean, neutral studio frame appended to whatever Gemini writes
FRAME = ("Full-length studio photograph of this person standing and facing the camera, "
         "wearing a plain matte dark-grey long-sleeve leotard with one uniform unbroken "
         "surface, barefoot, on a plain seamless light-grey studio backdrop, even soft "
         "lighting. Skin is " + SKIN + ". " + GRADE + ".")


def looks_like_refusal(msg: str) -> bool:
    low = (msg or "").lower()
    return any(m in low for m in _REFUSAL)


def _sanitize(text: str) -> str:
    out = text or ""
    low = out.lower()
    for w in AVOID_WORDS:
        i = low.find(w)
        while i >= 0:
            out = out[:i] + out[i + len(w):]
            low = out.lower()
            i = low.find(w)
    return " ".join(out.split())


def build_prompt(description: str, gender: str) -> str:
    g = {"Female": "a woman", "Male": "a man"}.get(gender, "an androgynous person")
    desc = _sanitize(description).rstrip(".")
    return f"A photorealistic character, {g}. {desc}. {FRAME}"


def _params_for(model_id):
    return dict(gen_config.slot(registry.T2I).get("params")
                or registry.param_defaults(model_id))


def _generate(model_id, prompt):
    provider = registry.provider_of(model_id)
    params = _params_for(model_id)
    payload = registry.build_payload(model_id, prompt, None, params, aspect=registry.CHAR_ASPECT)
    if provider == "replicate":
        from . import replicate_client as rc
        url = rc.run_image(model_id, payload)
        return url, rc.download(url)
    from .kie_client import generate_one, _download
    url = generate_one(prompt, None, aspect_ratio=registry.CHAR_ASPECT,
                       resolution=params.get("resolution", "1K"),
                       output_format=params.get("output_format", "png"))
    return url, _download(url)


class AnalyzeGenerateJob(QThread):
    """Photos → Gemini description → T2I render.
    Emits finished_ok(png_bytes, prompt, description) / refused / failed."""
    note = Signal(str)
    progress = Signal(int, int)
    finished_ok = Signal(bytes, str, str)
    refused = Signal(str)
    failed = Signal(str)

    def __init__(self, image_paths, gender, name="", parent=None):
        super().__init__(parent)
        self.image_paths = [p for p in (image_paths or []) if p]
        self.gender = gender
        self.name = name

    def run(self):
        try:
            from . import replicate_client as rc
            self.note.emit("Gemini is reading the photos…")
            hint = f"The character's name is {self.name}. " if self.name else ""
            hint += f"Treat the person as {self.gender.lower()}." if self.gender else ""
            description = rc.run_text(VISION_MODEL, {
                "prompt": (hint + " Describe this person for a text-to-image model.").strip(),
                "images": [rc.to_data_uri(p) for p in self.image_paths[:10]],
                "system_instruction": ANALYZE_SYSTEM,
                "temperature": 0.4,
                "thinking_budget": 0,
            })
            if not description.strip():
                self.failed.emit("Gemini returned an empty description")
                return
        except Exception as e:
            (self.refused if looks_like_refusal(str(e)) else self.failed).emit(str(e))
            return

        prompt = build_prompt(description, self.gender)
        try:
            model_id = gen_config.slot(registry.T2I)["model"]
            self.note.emit("")
            started = time.monotonic()
            _url, data = _generate(model_id, prompt)
            timing.record(timing.model_key(model_id), time.monotonic() - started, 1)
            self.progress.emit(1, 1)
            self.finished_ok.emit(data, prompt, description)
        except Exception as e:
            (self.refused if looks_like_refusal(str(e)) else self.failed).emit(str(e))
