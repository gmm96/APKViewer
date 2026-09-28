"""
The single place in the code base that inspects the running platform.
"""

import sys

from apkviewer.domain.interfaces import PlatformServices, WindowHandleProvider

from .linux_platform_services import LinuxPlatformServices
from .macos_platform_services import MacPlatformServices
from .unsupported_platform_services import UnsupportedPlatformServices
from .windows_platform_services import WindowsPlatformServices


class PlatformServicesResolver:
    def __init__(self, platform: str | None = None) -> None:
        # Injectable so it can be tested for every platform from any machine.
        self._platform: str = platform if platform is not None else sys.platform

    def resolve(self, window_handle_provider: WindowHandleProvider | None = None) -> PlatformServices:
        if self._platform == "win32":
            return WindowsPlatformServices()
        if self._platform == "darwin":
            return MacPlatformServices()
        if self._platform.startswith("linux"):
            return LinuxPlatformServices(window_handle_provider)
        return UnsupportedPlatformServices()
