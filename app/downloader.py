"""Download an Instagram reel or carousel with yt-dlp (authenticated by a
cookies.txt exported from the WebView2 login). Runs in a background thread."""

import re
import sys
import json
import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .store import REELS_DIR

_SHORTCODE_RE = re.compile(r"instagram\.com/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)")

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def parse_shortcode(url: str):
    m = _SHORTCODE_RE.search(url or "")
    return m.group(1) if m else None


def _read_caption(folder: Path) -> str:
    for j in sorted(folder.glob("*.info.json")):
        try:
            d = json.loads(j.read_text(encoding="utf-8"))
            return (d.get("description") or d.get("title") or "").strip()
        except Exception:
            continue
    return ""


def _natkey(p: Path):
    """Order CODE_1, CODE_2, … CODE_10 numerically, not as strings."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.stem)]


def _collect(folder: Path, shortcode: str, url: str) -> dict:
    files = [p for p in folder.iterdir() if p.is_file()]
    videos = sorted((p for p in files if p.suffix.lower() in VIDEO_EXT), key=_natkey)
    images = sorted((p for p in files if p.suffix.lower() in IMAGE_EXT), key=_natkey)
    video_stems = {v.stem for v in videos}
    posters = [im for im in images if im.stem in video_stems]
    content_images = [im for im in images if im.stem not in video_stems]

    caption = _read_caption(folder)

    if videos and not content_images:
        # single/again reel
        return {
            "media_type": "reel",
            "shortcode": shortcode,
            "url": url,
            "video_path": str(videos[0]),
            "image_paths": [],
            "thumb_path": str(posters[0]) if posters else "",
            "caption": caption,
        }
    # carousel / photoshoot (may include videos as extra items)
    imgs = content_images or images
    return {
        "media_type": "carousel",
        "shortcode": shortcode,
        "url": url,
        "video_path": str(videos[0]) if videos else "",
        "image_paths": [str(p) for p in imgs] + [str(v) for v in videos if content_images],
        "thumb_path": str(imgs[0]) if imgs else (str(posters[0]) if posters else ""),
        "caption": caption,
    }


class DownloadWorker(QThread):
    finished_ok = Signal(dict)     # collected media dict
    failed = Signal(str)

    def __init__(self, url: str, cookies_path: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.cookies_path = cookies_path

    def run(self):
        shortcode = parse_shortcode(self.url)
        if not shortcode:
            self.failed.emit("Not an Instagram reel or post URL.")
            return
        folder = REELS_DIR / shortcode
        folder.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-warnings", "--ignore-config",
            "--ignore-errors",                       # one bad slide shouldn't kill the carousel
            "--cookies", self.cookies_path,
            "--write-info-json", "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            # a carousel's slides share the post id — the playlist index keeps
            # each one a distinct file instead of overwriting the first
            "-o", str(folder / "%(id)s_%(playlist_index|0)s.%(ext)s"),
            self.url,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            self.failed.emit("Download timed out.")
            return
        except Exception as e:
            self.failed.emit(f"yt-dlp failed to launch: {e}")
            return

        try:
            media = _collect(folder, shortcode, self.url)
        except Exception as e:
            self.failed.emit(f"Could not read downloaded files: {e}")
            return
        if not media["video_path"] and not media["image_paths"]:
            err = (proc.stderr or proc.stdout or "").strip().splitlines()
            tail = err[-1] if err else "no media downloaded"
            self.failed.emit(f"Download failed: {tail}")
            return
        self.finished_ok.emit(media)
