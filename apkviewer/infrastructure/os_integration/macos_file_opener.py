"""
macOS implementation of OsFileOpener, backed by the `open` command.
"""

import subprocess

from apkviewer.domain.interfaces.os_file_opener import OsFileOpener


class MacFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        with subprocess.Popen(["open", path]):
            pass

    def open_with(self, path: str) -> None:
        with subprocess.Popen(["open", "-R", path]):
            pass
