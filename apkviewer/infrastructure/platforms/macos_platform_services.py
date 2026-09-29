"""
macOS implementations of the OS-dependent services. There is no native
file-clipboard integration on macOS yet, so that one is the unsupported
fallback.
"""

from apkviewer.domain.interfaces.clipboard_file_copier import ClipboardFileCopier
from apkviewer.domain.interfaces.os_file_opener import OsFileOpener
from apkviewer.domain.interfaces.platform_services import PlatformServices
from apkviewer.domain.interfaces.url_opener import UrlOpener
from apkviewer.infrastructure.clipboard.unsupported_clipboard_file_copier import UnsupportedClipboardFileCopier
from apkviewer.infrastructure.os_integration.macos_file_opener import MacFileOpener
from apkviewer.infrastructure.url.webbrowser_url_opener import WebBrowserUrlOpener


class MacPlatformServices(PlatformServices):
    def create_os_file_opener(self) -> OsFileOpener:
        return MacFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopier:
        return UnsupportedClipboardFileCopier()

    def create_url_opener(self) -> UrlOpener:
        return WebBrowserUrlOpener()
