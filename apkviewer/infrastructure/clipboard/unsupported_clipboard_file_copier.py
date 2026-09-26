"""
Fallback for platforms with no native file-clipboard integration.
"""

from apkviewer.domain.interfaces import ClipboardFileCopier


class UnsupportedClipboardFileCopier(ClipboardFileCopier):
    def copy(self, file_paths: list[str]) -> bool:
        return False
