"""Right pane: live Instagram via embedded Edge WebView2 (reels/H.264 play).
Address bar on top shows the current URL; the Save button downloads the open
reel/carousel (yt-dlp, authenticated by the WebView2 login) into the global
References board. The webview fills the rest of the pane."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

from ..store import DATA_DIR, REELS_DIR
from ..models_data import Reference
from ..downloader import parse_shortcode, DownloadWorker
from ..webview2_native import WebView2Host, available


class InstagramPane(QWidget):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.setObjectName("Pane")
        self._worker = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        if not available():
            msg = QLabel(
                "Edge WebView2 is not available.\n\n"
                "Needs the WebView2 runtime (preinstalled on Windows 11) and\n"
                "`pip install pythonnet` plus the .NET desktop runtime."
            )
            msg.setObjectName("Muted"); msg.setAlignment(Qt.AlignCenter); msg.setWordWrap(True)
            root.addWidget(msg)
            self.view = None
            return

        # ---- address bar + save ----
        bar = QWidget(); bar.setObjectName("PaneHead")
        bl = QHBoxLayout(bar); bl.setContentsMargins(8, 6, 8, 6); bl.setSpacing(7)
        self.address = QLineEdit()
        self.address.setPlaceholderText("instagram.com/…")
        self.address.returnPressed.connect(self._go)
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("Primary"); self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setToolTip("Save this reel / carousel to References")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save)
        bl.addWidget(self.address, 1)
        bl.addWidget(self.save_btn)
        root.addWidget(bar)

        # ---- webview ----
        hide_scrollbar = (
            "(function(){if(document.getElementById('__nosb'))return;"
            "var c='::-webkit-scrollbar{width:0!important;height:0!important;display:none!important}"
            "*{scrollbar-width:none!important;-ms-overflow-style:none!important}';"
            "var s=document.createElement('style');s.id='__nosb';s.textContent=c;"
            "(document.head||document.documentElement).appendChild(s);})();"
        )
        udd = str(DATA_DIR / "webview2_edge")
        self.view = WebView2Host(self.store.ig_url, udd,
                                 on_ready=self._on_ready, on_url_changed=self._on_url,
                                 init_script=hide_scrollbar)
        root.addWidget(self.view, 1)

    # ---- navigation / address bar ----
    def _on_ready(self, ok, message):
        if not ok:
            print("[Instagram] WebView2 init failed:", message)

    def _on_url(self, url):
        if not self.address.hasFocus():
            self.address.setText(url)
        self.save_btn.setEnabled(bool(parse_shortcode(url)) and self._worker is None)

    def _go(self):
        url = self.address.text().strip()
        if url and self.view:
            if not url.startswith("http"):
                url = "https://" + url
            self.view.navigate(url)

    # ---- save (download) ----
    def _save(self):
        url = self.address.text().strip() or (self.view.current_url() if self.view else "")
        self.download_url(url)

    def download_url(self, url):
        """Public: download `url`'s media into References (used by Save and by
        the 're-download' button on old link references)."""
        if self._worker is not None or not self.view:
            return
        if not parse_shortcode(url):
            self._reset_save("Open a reel first")
            return
        REELS_DIR.mkdir(parents=True, exist_ok=True)
        cookies_path = str(REELS_DIR / "cookies.txt")
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving…")
        self.view.export_cookies("https://www.instagram.com", cookies_path,
                                 lambda ok, err: self._after_cookies(ok, err, url, cookies_path))

    def _after_cookies(self, ok, err, url, cookies_path):
        if not ok:
            self._reset_save("Cookie error")
            print("[Instagram] cookie export:", err)
            return
        self._worker = DownloadWorker(url, cookies_path)
        self._worker.finished_ok.connect(self._on_downloaded)
        self._worker.failed.connect(self._on_download_failed)
        self._worker.start()

    def _on_downloaded(self, media):
        cap = (media.get("caption") or "").strip().splitlines()
        title = (cap[0][:44] if cap else "") or media.get("shortcode", "reel")
        n_imgs = len(media.get("image_paths") or [])
        note = "reel" if media["media_type"] == "reel" else f"{n_imgs} photos"
        self.store.add_reference(Reference(
            url=media["url"], title=title, note=note,
            media_type=media["media_type"], shortcode=media["shortcode"],
            video_path=media["video_path"], image_paths=media["image_paths"],
            thumb_path=media["thumb_path"], caption=media["caption"],
        ))
        self._reset_save("Saved ✓")

    def _on_download_failed(self, msg):
        self._reset_save("Save failed")
        print("[Instagram] download failed:", msg)

    def _reset_save(self, status=None):
        self._worker = None
        self.save_btn.setEnabled(bool(parse_shortcode(self.address.text())))
        if status:
            self.save_btn.setText(status)
            QTimer.singleShot(1600, lambda: self.save_btn.setText("Save"))
        else:
            self.save_btn.setText("Save")
