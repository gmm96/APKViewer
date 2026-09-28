"""
Fallback services for platforms with no native integration at all.
"""

from apkviewer.domain.interfaces import (
    ClipboardFileCopier,
    OsFileOpener,
    PlatformServices,
    UrlOpener
)
from apkviewer.infrastructure.clipboard.unsupported_clipboard_file_copier import UnsupportedClipboardFileCopier
from apkviewer.infrastructure.os_integration.unsupported_file_opener import UnsupportedFileOpener
from apkviewer.infrastructure.url.webbrowser_url_opener import WebBrowserUrlOpener


class UnsupportedPlatformServices(PlatformServices):
    def create_os_file_opener(self) -> OsFileOpener:
        return UnsupportedFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopier:
        return UnsupportedClipboardFileCopier()

    def create_url_opener(self) -> UrlOpener:
        return WebBrowserUrlOpener()
