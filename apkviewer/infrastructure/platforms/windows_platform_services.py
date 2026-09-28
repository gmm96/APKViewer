"""
Windows implementations of the OS-dependent services.
"""

from apkviewer.domain.interfaces import (
    ClipboardFileCopier,
    OsFileOpener,
    PlatformServices,
    UrlOpener
)
from apkviewer.infrastructure.clipboard.windows_clipboard_file_copier import WindowsClipboardFileCopier
from apkviewer.infrastructure.os_integration.windows_file_opener import WindowsFileOpener
from apkviewer.infrastructure.url.webbrowser_url_opener import WebBrowserUrlOpener


class WindowsPlatformServices(PlatformServices):
    def create_os_file_opener(self) -> OsFileOpener:
        return WindowsFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopier:
        return WindowsClipboardFileCopier()

    def create_url_opener(self) -> UrlOpener:
        return WebBrowserUrlOpener()
