"""
Linux implementation of ClipboardFileCopier: tries the X11 clipboard
(xclip) first, then falls back to Wayland (wl-copy).
"""

import os
import subprocess

from apkviewer.domain.interfaces import ClipboardFileCopier


class LinuxClipboardFileCopier(ClipboardFileCopier):
    _COMMANDS: tuple[list[str], list[str]] = (
        ["xclip", "-i", "-selection", "clipboard", "-t", "text/uri-list"],
        ["wl-copy", "-t", "text/uri-list"],
    )

    def copy(self, file_paths: list[str]) -> bool:
        payload = "\n".join(f"file://{os.path.abspath(p)}" for p in file_paths).encode("utf-8")
        return any(self._try_run(command, payload) for command in self._COMMANDS)

    @staticmethod
    def _try_run(command: list[str], payload: bytes) -> bool:
        try:
            subprocess.run(command, input=payload, check=True, stderr=subprocess.DEVNULL)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
