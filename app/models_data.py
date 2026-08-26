"""Plain data structures for models and references."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict
import uuid

# social platforms shown in the Appearance tab and the profile editor
SOCIALS = [
    ("instagram", "Instagram"),
    ("telegram", "Telegram"),
    ("tiktok", "TikTok"),
    ("youtube", "YouTube"),
]


def _id() -> str:
    return uuid.uuid4().hex[:12]


def default_profile() -> dict:
    return {
        "bio": "",
        "personality": "",
        "notes": "",
        "socials": {key: "" for key, _label in SOCIALS},
    }


@dataclass
class Reference:
    id: str = field(default_factory=_id)
    url: str = ""
    title: str = ""
    note: str = ""
    thumb_seed: int = 0
    media_type: str = ""                 # "" (link only) | "reel" | "carousel"
    shortcode: str = ""
    video_path: str = ""
    image_paths: List[str] = field(default_factory=list)
    thumb_path: str = ""                 # local poster / first image
    caption: str = ""
    favorite: bool = False

    @staticmethod
    def from_dict(d: dict) -> "Reference":
        fields = Reference.__dataclass_fields__
        return Reference(**{k: v for k, v in d.items() if k in fields})


@dataclass
class Model:
    id: str = field(default_factory=_id)
    name: str = "New Model"
    niche: str = "unassigned"
    status: str = "draft"          # draft | ready
    avatar_seed: int = 0
    sheet_path: str = ""           # generated character sheet image (later)
    spec: Dict[str, str] = field(default_factory=dict)
    references: List[Reference] = field(default_factory=list)
    profile: Dict = field(default_factory=default_profile)
    portrait_path: str = ""              # main 9:16 face portrait
    body_path: str = ""                  # full-body 3:4 image (stage 2)
    appearance: Dict = field(default_factory=dict)   # structured appearance sheet from the casting agent
    detail_images: List[str] = field(default_factory=list)   # user refs: tattoos, prosthetics, wheelchair…
    brief: str = ""                      # the free-text brief this character was cast from
    casting_id: str = ""                 # the casting card in the library this model came from
    sheet_prompt: str = ""               # prompt that produced sheet_path
    description: str = ""                # casting director's full write-up

    def ensure_profile(self) -> dict:
        """Fill any missing profile keys (older saved models)."""
        base = default_profile()
        if not isinstance(self.profile, dict):
            self.profile = base
        for k, v in base.items():
            if k not in self.profile:
                self.profile[k] = v
        if not isinstance(self.profile.get("socials"), dict):
            self.profile["socials"] = base["socials"]
        for key, _label in SOCIALS:
            self.profile["socials"].setdefault(key, "")
        return self.profile

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Model":
        d = dict(d)
        d["references"] = [Reference.from_dict(r) for r in d.get("references", [])]
        m = Model(**d)
        m.ensure_profile()
        return m
