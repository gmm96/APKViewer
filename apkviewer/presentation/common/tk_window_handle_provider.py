"""
Tkinter implementation of WindowHandleProvider.
"""

import tkinter as tk

from apkviewer.domain.interfaces import WindowHandleProvider


class TkWindowHandleProvider(WindowHandleProvider):
    def __init__(self, window: tk.Misc) -> None:
        self._window: tk.Misc = window

    def get_handle(self) -> str:
        # Tk on Linux always runs on X11 (natively or through XWayland),
        # and portals identify X11 windows as "x11:<hex XID>".
        try:
            return f"x11:{self._window.winfo_toplevel().winfo_id():x}"
        except tk.TclError:
            return ""
