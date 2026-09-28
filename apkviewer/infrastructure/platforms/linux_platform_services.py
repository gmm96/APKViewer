"""
Linux implementations of the OS-dependent services.
"""

from apkviewer.domain.interfaces import (
    ClipboardFileCopier,
    OsFileOpener,
    PlatformServices,
    UrlOpener,
    WindowHandleProvider,
)
from apkviewer.infrastructure.clipboard.linux_clipboard_file_copier import LinuxClipboardFileCopier
from apkviewer.infrastructure.os_integration.linux_file_opener import LinuxFileOpener
from apkviewer.infrastructure.url.linux_url_opener import LinuxUrlOpener


class LinuxPlatformServices(PlatformServices):
    def __init__(self, window_handle_provider: WindowHandleProvider | None = None) -> None:
        self._window_handle_provider: WindowHandleProvider | None = window_handle_provider

    def create_os_file_opener(self) -> OsFileOpener:
        return LinuxFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopier:
        return LinuxClipboardFileCopier()

    def create_url_opener(self) -> UrlOpener:
        return LinuxUrlOpener(self._window_handle_provider)
