"""
Cross-platform clipboard utilities for copying actual files, allowing users
to paste them natively into File Explorer (Windows) or File Managers (Linux).
"""
import os
import subprocess
import sys


def copy_files_to_clipboard(file_paths: list) -> bool:
    if not file_paths:
        return False

    if sys.platform == "win32":
        return _copy_files_win(file_paths)
    elif sys.platform.startswith("linux"):
        return _copy_files_linux(file_paths)
    
    return False


def _copy_files_win(file_paths: list) -> bool:
    try:
        import ctypes
        from ctypes import wintypes
        
        class DROPFILES(ctypes.Structure):
            _fields_ = [
                ("pFiles", wintypes.DWORD),
                ("pt", wintypes.POINT),
                ("fNC", wintypes.BOOL),
                ("fWide", wintypes.BOOL)
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
        
        hGlobal = kernel32.GlobalAlloc(GHND, ctypes.sizeof(DROPFILES) + len(file_buffer_bytes))
        if not hGlobal:
            return False
            
        pGlobal = kernel32.GlobalLock(hGlobal)
        ctypes.memmove(pGlobal, ctypes.addressof(dropfiles), ctypes.sizeof(DROPFILES))
        ctypes.memmove(pGlobal + ctypes.sizeof(DROPFILES), file_buffer_bytes, len(file_buffer_bytes))
        kernel32.GlobalUnlock(hGlobal)
        
        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_HDROP, hGlobal)
        user32.CloseClipboard()
        return True
    except Exception:
        return False


def _copy_files_linux(file_paths: list) -> bool:
    uris = "\n".join([f"file://{os.path.abspath(p)}" for p in file_paths])
    try:
        # Try X11 clipboard
        subprocess.run(
            ['xclip', '-i', '-selection', 'clipboard', '-t', 'text/uri-list'], 
            input=uris.encode('utf-8'), check=True, stderr=subprocess.DEVNULL
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            # Fallback to Wayland clipboard
            subprocess.run(
                ['wl-copy', '-t', 'text/uri-list'], 
                input=uris.encode('utf-8'), check=True, stderr=subprocess.DEVNULL
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
