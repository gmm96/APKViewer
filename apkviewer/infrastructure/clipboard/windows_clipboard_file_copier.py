"""
Windows implementation of ClipboardFileCopier, using the CF_HDROP
clipboard format via ctypes/user32.
"""

from apkviewer.domain.interfaces.clipboard_file_copier import ClipboardFileCopier


class WindowsClipboardFileCopier(ClipboardFileCopier):
    def copy(self, file_paths: list[str]) -> bool:
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

            windll = getattr(ctypes, "windll")
            user32 = windll.user32
            kernel32 = windll.kernel32

            file_buffer = "\0".join(file_paths) + "\0\0"
            file_buffer_bytes = file_buffer.encode("utf-16le")

            dropfiles = DROPFILES()
            dropfiles.pFiles = ctypes.sizeof(DROPFILES)
            dropfiles.fWide = True

            h_global = kernel32.GlobalAlloc(GHND, ctypes.sizeof(DROPFILES) + len(file_buffer_bytes))
            if not h_global:
                return False

            p_global = kernel32.GlobalLock(h_global)
            ctypes.memmove(
                p_global,
                ctypes.addressof(dropfiles),
                ctypes.sizeof(DROPFILES)
            )
            ctypes.memmove(
                p_global + ctypes.sizeof(DROPFILES),
                file_buffer_bytes,
                len(file_buffer_bytes)
            )
            kernel32.GlobalUnlock(h_global)

            user32.OpenClipboard(0)
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_HDROP, h_global)
            user32.CloseClipboard()
            return True
        except Exception:
            return False
