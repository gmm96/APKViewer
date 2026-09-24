"""
Copies real files onto the OS clipboard, so users can paste them natively
into File Explorer (Windows) or a file manager (Linux).

This follows the same Strategy shape already used elsewhere in the project
(`ManifestFormatter`'s `XmlSerializer`, `ApkExtractor`'s `FileDecoder`):
a common abstract interface, one concrete class per case, and a small
factory function that resolves the right implementation for the current
platform. Replaces the old function-based `clipboard_utils.py` module.
"""
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import List


class ClipboardFileCopier(ABC):
    """Puts real files (not text) onto the system clipboard."""

    @abstractmethod
    def copy(self, file_paths: List[str]) -> bool:
        raise NotImplementedError


class WindowsClipboardFileCopier(ClipboardFileCopier):
    """Uses the CF_HDROP clipboard format via ctypes/user32."""

    def copy(self, file_paths: List[str]) -> bool:
        try:
            import ctypes
            from ctypes import wintypes

            class DROPFILES(ctypes.Structure):
                _fields_ = [
                    ("pFiles", wintypes.DWORD),
                    ("pt", wintypes.POINT),
                    ("fNC", wintypes.BOOL),
                    ("fWide", wintypes.BOOL),
                ]

            GHND = 0x0042
            CF_HDROP = 15

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            file_buffer = "\0".join(file_paths) + "\0\0"
            file_buffer_bytes = file_buffer.encode("utf-16le")

            dropfiles = DROPFILES()
            dropfiles.pFiles = ctypes.sizeof(DROPFILES)
            dropfiles.fWide = True

            h_global = kernel32.GlobalAlloc(GHND, ctypes.sizeof(DROPFILES) + len(file_buffer_bytes))
            if not h_global:
                return False

            p_global = kernel32.GlobalLock(h_global)
            ctypes.memmove(p_global, ctypes.addressof(dropfiles), ctypes.sizeof(DROPFILES))
            ctypes.memmove(p_global + ctypes.sizeof(DROPFILES), file_buffer_bytes, len(file_buffer_bytes))
            kernel32.GlobalUnlock(h_global)

            user32.OpenClipboard(0)
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_HDROP, h_global)
            user32.CloseClipboard()
            return True
        except Exception:
            return False


class LinuxClipboardFileCopier(ClipboardFileCopier):
    """Tries the X11 clipboard (xclip) first, then falls back to Wayland (wl-copy)."""

    _COMMANDS = (
        ["xclip", "-i", "-selection", "clipboard", "-t", "text/uri-list"],
        ["wl-copy", "-t", "text/uri-list"],
    )

    def copy(self, file_paths: List[str]) -> bool:
        payload = "\n".join(f"file://{os.path.abspath(p)}" for p in file_paths).encode("utf-8")
        return any(self._try_run(command, payload) for command in self._COMMANDS)

    @staticmethod
    def _try_run(command: List[str], payload: bytes) -> bool:
        try:
            subprocess.run(command, input=payload, check=True, stderr=subprocess.DEVNULL)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False


class UnsupportedClipboardFileCopier(ClipboardFileCopier):
    """Fallback for platforms with no native file-clipboard integration."""

    def copy(self, file_paths: List[str]) -> bool:
        return False


def default_clipboard_file_copier() -> ClipboardFileCopier:
    """Resolves the right `ClipboardFileCopier` for the running platform."""
    if sys.platform == "win32":
        return WindowsClipboardFileCopier()
    if sys.platform.startswith("linux"):
        return LinuxClipboardFileCopier()
    return UnsupportedClipboardFileCopier()
