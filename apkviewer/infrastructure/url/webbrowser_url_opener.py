"""
Default UrlOpener implementation, backed by the standard `webbrowser` module.
Used as-is on Windows/macOS (where the underlying `startfile` / `open`
already bring the browser to the front) and as a fallback on Linux.
"""

import webbrowser

from apkviewer.domain.interfaces import UrlOpener


class WebBrowserUrlOpener(UrlOpener):
    def open(self, url: str) -> None:
        # new=2 asks for a new tab; autoraise is only a hint that many
        # browsers ignore, which is why LinuxUrlOpener exists.
        if not webbrowser.open(url, new=2, autoraise=True):
            raise RuntimeError(f"Could not open a web browser for:\n{url}")
