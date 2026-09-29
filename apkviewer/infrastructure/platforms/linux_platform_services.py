"""
Linux implementations of the OS-dependent services.
"""

from apkviewer.domain.interfaces.clipboard_file_copier import ClipboardFileCopier
from apkviewer.domain.interfaces.os_file_opener import OsFileOpener
from apkviewer.domain.interfaces.platform_services import PlatformServices
from apkviewer.domain.interfaces.url_opener import UrlOpener
from apkviewer.infrastructure.clipboard.linux_clipboard_file_copier import LinuxClipboardFileCopier
from apkviewer.infrastructure.os_integration.linux_file_opener import LinuxFileOpener
from apkviewer.infrastructure.url.webbrowser_url_opener import WebBrowserUrlOpener


class LinuxPlatformServices(PlatformServices):
    def create_os_file_opener(self) -> OsFileOpener:
        return LinuxFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopier:
        return LinuxClipboardFileCopier()

    def create_url_opener(self) -> UrlOpener:
        return WebBrowserUrlOpener()
