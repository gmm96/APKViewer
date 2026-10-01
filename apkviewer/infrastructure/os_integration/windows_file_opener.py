"""
Windows implementation of OsFileOpener: default-app open via os.startfile,
and the native "Open with..." picker via shell32's SHOpenWithDialog.
"""

import os

from apkviewer.domain.interfaces.os_file_opener import OsFileOpener


class WindowsFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        getattr(os, "startfile")(path)

    def open_with(self, path: str) -> None:
        # pylint: disable=import-outside-toplevel
        # pylint: disable=invalid-name
        import ctypes
        from ctypes import wintypes

        class OPENASINFO(ctypes.Structure):
            _fields_ = [
                ("pcszFile", wintypes.LPCWSTR),
                ("pcszClass", wintypes.LPCWSTR),
                ("oaifInFlags", wintypes.DWORD),
            ]

        OAIF_EXEC = 0x00000004
        OAIF_HIDE_REGISTRATION = 0x00000020
        info = OPENASINFO(path, None, OAIF_EXEC | OAIF_HIDE_REGISTRATION)
        WinDLL = getattr(ctypes, "WinDLL")
        shell32 = WinDLL("shell32", use_last_error=True)
        shell32.SHOpenWithDialog.argtypes = [wintypes.HWND, ctypes.POINTER(OPENASINFO)]
        shell32.SHOpenWithDialog.restype = wintypes.HRESULT
        hr = shell32.SHOpenWithDialog(None, ctypes.byref(info))
        if hr != 0:
            raise OSError(f"SHOpenWithDialog failed with HRESULT 0x{hr & 0xffffffff:08X}")
