"""
Infrastructure layer: concrete adapters for androguard, the zip/APK
format, XML serialization, OS shell integration and the system clipboard.
Everything here implements a port declared in apkviewer.domain.interfaces.
"""

from .androguard.apk_loader import ApkLoader
from .formatting.human_readable_size_formatter import HumanReadableSizeFormatter
from .platforms.platform_services_resolver import PlatformServicesResolver
from .url.webbrowser_url_opener import WebBrowserUrlOpener
from .xml.lxml_serializer import LxmlSerializer
from .zip.apk_extractor import ApkExtractor
from .zip.axml_decoder import AxmlDecoder

__all__ = [
    "ApkLoader",
    "ApkExtractor",
    "AxmlDecoder",
    "LxmlSerializer",
    "HumanReadableSizeFormatter",
    "WebBrowserUrlOpener",
    "PlatformServicesResolver",
]
