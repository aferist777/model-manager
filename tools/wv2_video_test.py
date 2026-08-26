"""Diagnostic: play two sample videos (H.264 + AV1) inside the embedded
WebView2, in a REAL window, with on-screen status. Tells us whether video
works in the embedded window at all, isolating it from Instagram specifics.

    python tools/wv2_video_test.py

Report what you SEE for each: "PLAYING WxH" (good) or "ERROR n" (bad).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer
from app.webview2_native import WebView2Host, available

HTML = """
<html><body style="background:#141414;color:#eee;font:15px sans-serif;margin:12px">
<h3>H.264 sample</h3>
<video id=a src="https://www.w3schools.com/html/mov_bbb.mp4" muted autoplay loop playsinline width=320></video>
<div id=sa>loading...</div>
<h3 style="margin-top:16px">AV1 sample</h3>
<video id=b src="https://test-videos.co.uk/vids/bigbuckbunny/mp4/av1/360/Big_Buck_Bunny_360_10s_1MB.mp4" muted autoplay loop playsinline width=320></video>
<div id=sb>loading...</div>
<script>
function watch(v,s){
  v.addEventListener('playing',function(){s.textContent='PLAYING '+v.videoWidth+'x'+v.videoHeight; s.style.color='#7ad196';});
  v.addEventListener('error',function(){s.textContent='ERROR code '+(v.error&&v.error.code); s.style.color='#e8825f';});
  v.play().catch(function(e){s.textContent='play() rejected: '+e;});
}
watch(document.getElementById('a'),document.getElementById('sa'));
watch(document.getElementById('b'),document.getElementById('sb'));
</script>
</body></html>
"""


def main():
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("WebView2 video test — do the samples play?")
    win.resize(420, 720)
    if not available():
        win.show(); return sys.exit(app.exec())

    udd = str(Path(__file__).resolve().parent.parent / "data" / "webview2_edge")

    def on_ready(ok, msg):
        print("ready:", ok, msg)
        if ok:
            QTimer.singleShot(300, lambda: host._wv.CoreWebView2.NavigateToString(HTML))

    host = WebView2Host("about:blank", udd, on_ready=on_ready)
    win.setCentralWidget(host)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
