"""
Infrastructure layer: concrete adapters for androguard, the zip/APK
format, XML serialization, OS shell integration and the system clipboard.
Everything here implements a port declared in apkviewer.domain.ports.
"""

from .androguard.apk_loader import ApkLoader
from .clipboard.clipboard_file_copier_factory import default_clipboard_file_copier
from .formatting.human_readable_size_formatter import HumanReadableSizeFormatter
from .os_integration.os_file_opener_factory import default_os_file_opener
from .xml.lxml_serializer import LxmlSerializer
from .zip.apk_extractor import ApkExtractor
from .zip.axml_decoder import AxmlDecoder

__all__ = [
    "ApkLoader",
    "ApkExtractor",
    "AxmlDecoder",
    "LxmlSerializer",
    "HumanReadableSizeFormatter",
    "default_os_file_opener",
    "default_clipboard_file_copier",
]
