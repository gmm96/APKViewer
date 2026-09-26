"""
macOS implementation of OsFileOpener, backed by the `open` command.
"""

import subprocess

from apkviewer.domain.interfaces import OsFileOpener


class MacFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        subprocess.Popen(["open", path])

    def open_with(self, path: str) -> None:
        subprocess.Popen(["open", "-R", path])
