"""
Fallback OsFileOpener for platforms with no native "open" integration.
"""

import sys

from apkviewer.domain.interfaces import OsFileOpener


class UnsupportedFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        raise RuntimeError(f"Opening files is not supported on platform: {sys.platform}")

    def open_with(self, path: str) -> None:
        raise RuntimeError(f"Open With is not supported on platform: {sys.platform}")
