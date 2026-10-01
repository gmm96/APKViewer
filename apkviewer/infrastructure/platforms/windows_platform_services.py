"""
Windows implementations of the OS-dependent services.
"""

from apkviewer.domain.interfaces.clipboard_file_copier import ClipboardFileCopier
from apkviewer.domain.interfaces.os_file_opener import OsFileOpener
from apkviewer.domain.interfaces.platform_services import PlatformServices
from apkviewer.domain.interfaces.system_color_scheme_detector import SystemColorSchemeDetector
from apkviewer.domain.interfaces.url_opener import UrlOpener
from apkviewer.infrastructure.appearance.windows_color_scheme_detector import WindowsColorSchemeDetector
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

    def create_system_color_scheme_detector(self) -> SystemColorSchemeDetector:
        return WindowsColorSchemeDetector()
