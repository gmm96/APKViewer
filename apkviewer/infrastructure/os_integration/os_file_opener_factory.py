"""
Resolves the right OsFileOpener implementation for the running platform.
"""

import sys

from apkviewer.domain.interfaces import OsFileOpener

from .linux_file_opener import LinuxFileOpener
from .macos_file_opener import MacFileOpener
from .unsupported_file_opener import UnsupportedFileOpener
from .windows_file_opener import WindowsFileOpener


def default_os_file_opener() -> OsFileOpener:
    if sys.platform == "win32":
        return WindowsFileOpener()
    if sys.platform == "darwin":
        return MacFileOpener()
    if sys.platform.startswith("linux"):
        return LinuxFileOpener()
    return UnsupportedFileOpener()
