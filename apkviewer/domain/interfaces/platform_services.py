"""
Port (abstract factory) that groups every dependency whose implementation
depends on the operating system. The composition root asks it for what it
needs, so the rest of the code never checks the platform itself.
"""

from abc import ABC, abstractmethod

from .clipboard_file_copier import ClipboardFileCopier
from .os_file_opener import OsFileOpener
from .system_color_scheme_detector import SystemColorSchemeDetector
from .url_opener import UrlOpener


class PlatformServices(ABC):
    @abstractmethod
    def create_os_file_opener(self) -> OsFileOpener:
        raise NotImplementedError

    @abstractmethod
    def create_clipboard_file_copier(self) -> ClipboardFileCopier:
        raise NotImplementedError

    @abstractmethod
    def create_url_opener(self) -> UrlOpener:
        raise NotImplementedError

    @abstractmethod
    def create_system_color_scheme_detector(self) -> SystemColorSchemeDetector:
        raise NotImplementedError
