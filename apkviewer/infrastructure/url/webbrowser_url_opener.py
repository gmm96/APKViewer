"""
Default UrlOpener implementation, backed by the standard `webbrowser` module.

Known limitation: whether an already-running browser window comes to the
foreground is decided by the window manager / compositor, not by this
application. On Wayland there is no way to force it without a native
activation token, so the browser may open in the background.
"""

import webbrowser

from apkviewer.domain.interfaces.url_opener import UrlOpener


class WebBrowserUrlOpener(UrlOpener):
    def open(self, url: str) -> None:
        # new=2 asks for a new tab; autoraise is only a hint that many
        # browsers ignore.
        if not webbrowser.open(url, new=2, autoraise=True):
            raise RuntimeError(f"Could not open a web browser for:\n{url}")
