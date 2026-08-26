"""Embed Microsoft Edge WebView2 (system Chromium, has H.264) inside a Qt
widget via native HWND reparenting. Used for the Instagram panel so reels play
(Qt WebEngine lacks proprietary codecs).

Requires: pythonnet, the .NET 9 desktop runtime, and the WebView2 runtime
(preinstalled on Windows 11). DLLs live in model-manager/libs/webview2/.
"""

import os
import ctypes
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QSizePolicy

LIB = Path(__file__).resolve().parent.parent / "libs" / "webview2"

_loaded = False


def available() -> bool:
    return LIB.exists() and (LIB / "Microsoft.Web.WebView2.Core.dll").exists()


def _ensure_clr():
    global _loaded
    if _loaded:
        return
    native = str(LIB)
    os.add_dll_directory(native)
    os.environ["PATH"] = native + os.pathsep + os.environ.get("PATH", "")
    from pythonnet import load
    load("coreclr", runtime_config=str(LIB / "webview2.runtimeconfig.json"))
    import clr  # noqa: F401
    from System.Reflection import Assembly
    Assembly.LoadFile(str(LIB / "Microsoft.Web.WebView2.Core.dll"))
    Assembly.LoadFile(str(LIB / "Microsoft.Web.WebView2.WinForms.dll"))
    clr.AddReference("System.Windows.Forms")
    # give WebView2's async continuations a context Qt's message loop will pump
    from System.Windows.Forms import WindowsFormsSynchronizationContext
    from System.Threading import SynchronizationContext
    SynchronizationContext.SetSynchronizationContext(WindowsFormsSynchronizationContext())
    _loaded = True


class WebView2Host(QWidget):
    def __init__(self, url: str, user_data_dir, parent=None, on_ready=None,
                 on_url_changed=None, zoom=1.0, init_script=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NativeWindow, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)
        self._url = url
        self._udd = str(user_data_dir)
        self._on_ready = on_ready
        self._on_url_changed = on_url_changed
        self._zoom = zoom
        self._init_script = init_script
        self._hwnd = None
        self._wv = None
        self._error = None
        QTimer.singleShot(0, self._init)  # after winId() exists

    def _init(self):
        try:
            # WebView2 needs the thread in a COM single-threaded apartment (STA).
            # S_OK(0)/S_FALSE(1) both fine; ignore "already initialized".
            ctypes.windll.ole32.CoInitializeEx(None, 0x2)  # COINIT_APARTMENTTHREADED

            _ensure_clr()
            from Microsoft.Web.WebView2.WinForms import WebView2, CoreWebView2CreationProperties
            from System import Uri

            os.makedirs(self._udd, exist_ok=True)
            wv = WebView2()
            props = CoreWebView2CreationProperties()
            props.UserDataFolder = self._udd
            wv.CreationProperties = props

            wv.CoreWebView2InitializationCompleted += self._on_init_completed
            wv.SourceChanged += self._on_source_changed

            wv.Source = Uri(self._url)
            hwnd = int(wv.Handle.ToInt64())   # forces native window creation
            self._wv = wv
            self._hwnd = hwnd

            u = ctypes.windll.user32
            GWL_STYLE = -16
            WS_CHILD = 0x40000000
            WS_VISIBLE = 0x10000000
            u.SetWindowLongW(hwnd, GWL_STYLE, WS_CHILD | WS_VISIBLE)
            u.SetParent(hwnd, int(self.winId()))
            self._resize_child()
            # re-sync once the window/splitter has settled (maximize, initial layout)
            QTimer.singleShot(200, self._resize_child)
            QTimer.singleShot(600, self._resize_child)
        except Exception as e:  # surface but don't crash the app
            self._error = str(e)
            if self._on_ready is not None:
                self._on_ready(False, str(e))

    def _on_init_completed(self, sender, args):
        ok = bool(getattr(args, "IsSuccess", True))
        msg = ""
        if not ok:
            exc = getattr(args, "InitializationException", None)
            msg = str(getattr(exc, "Message", exc)) if exc is not None else "CoreWebView2 init failed"
        if ok and self._zoom and self._zoom != 1.0:
            try:
                self._wv.ZoomFactor = float(self._zoom)
            except Exception:
                pass
        if ok and self._init_script:
            try:
                self._wv.CoreWebView2.AddScriptToExecuteOnDocumentCreatedAsync(self._init_script)
                # also run after each page finishes (DOM ready) — most reliable
                self._wv.CoreWebView2.NavigationCompleted += self._on_nav_completed
            except Exception:
                pass
        if self._on_ready is not None:
            self._on_ready(ok, msg)

    def _on_nav_completed(self, sender, args):
        try:
            if self._init_script and self._wv is not None and self._wv.CoreWebView2 is not None:
                self._wv.CoreWebView2.ExecuteScriptAsync(self._init_script)
        except Exception:
            pass

    def set_zoom(self, factor):
        self._zoom = factor
        try:
            if self._wv is not None:
                self._wv.ZoomFactor = float(factor)
        except Exception:
            pass

    def shutdown(self):
        """Stop media and tear down the webview (call when the host closes so
        video/audio doesn't keep playing in the background)."""
        try:
            if self._wv is not None and self._wv.CoreWebView2 is not None:
                self._wv.CoreWebView2.Navigate("about:blank")  # stops playback now
        except Exception:
            pass
        try:
            if self._wv is not None:
                self._wv.Dispose()
        except Exception:
            pass
        self._wv = None
        self._hwnd = None

    def _on_source_changed(self, sender, args):
        if self._on_url_changed is not None:
            self._on_url_changed(self.current_url())

    def current_url(self) -> str:
        try:
            if self._wv is not None and self._wv.Source is not None:
                return str(self._wv.Source.AbsoluteUri)
        except Exception:
            pass
        return ""

    def export_cookies(self, url: str, out_path: str, callback):
        """Write the WebView2 cookies for `url` as a Netscape cookies.txt that
        yt-dlp can use. callback(ok: bool, err: str)."""
        try:
            cm = self._wv.CoreWebView2.CookieManager
            task = cm.GetCookiesAsync(url)
        except Exception as e:
            callback(False, str(e))
            return

        def check():
            if not task.IsCompleted:
                QTimer.singleShot(150, check)
                return
            try:
                cookies = task.Result
                lines = ["# Netscape HTTP Cookie File\n"]
                for i in range(cookies.Count):
                    c = cookies[i]
                    domain = c.Domain
                    flag = "TRUE" if domain.startswith(".") else "FALSE"
                    secure = "TRUE" if c.IsSecure else "FALSE"
                    try:
                        exp = int(c.Expires) if c.Expires and c.Expires > 0 else 0
                    except Exception:
                        exp = 0
                    lines.append("\t".join([domain, flag, c.Path or "/", secure,
                                            str(exp), c.Name, c.Value]) + "\n")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                callback(True, "")
            except Exception as e:
                callback(False, str(e))

        QTimer.singleShot(50, check)

    def _resize_child(self):
        if self._hwnd:
            # the reparented child HWND is in physical pixels; Qt geometry is
            # logical — scale by the device pixel ratio or it leaves a gap on
            # the right/bottom on scaled (125%/150%) displays.
            r = self.devicePixelRatioF()
            w = max(1, int(round(self.width() * r)))
            h = max(1, int(round(self.height() * r)))
            ctypes.windll.user32.MoveWindow(self._hwnd, 0, 0, w, h, True)

    def resizeEvent(self, e):
        self._resize_child()
        super().resizeEvent(e)

    def showEvent(self, e):
        self._resize_child()
        super().showEvent(e)

    def navigate(self, url: str):
        if self._wv:
            from System import Uri
            self._wv.Source = Uri(url)
