"""
Resolves the right ClipboardFileCopier implementation for the running
platform. Note there is intentionally no dedicated macOS strategy (macOS
falls back to UnsupportedClipboardFileCopier, same as before the
refactor) - this mirrors the original behaviour rather than introducing
new functionality.
"""

import sys

from apkviewer.domain.interfaces import ClipboardFileCopier

from .linux_clipboard_file_copier import LinuxClipboardFileCopier
from .unsupported_clipboard_file_copier import UnsupportedClipboardFileCopier
from .windows_clipboard_file_copier import WindowsClipboardFileCopier


def default_clipboard_file_copier() -> ClipboardFileCopier:
    if sys.platform == "win32":
        return WindowsClipboardFileCopier()
    if sys.platform.startswith("linux"):
        return LinuxClipboardFileCopier()
    return UnsupportedClipboardFileCopier()
