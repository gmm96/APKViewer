"""
A notice shown at the top of a tab when part of its data could not be
read, so the user can tell "nothing found" from "could not look".
"""

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk

from apkviewer.presentation.appearance.theme_palette import ThemePalette


class WarningBanner(ttk.Frame):
    def __init__(self, parent: tk.Misc, palette: ThemePalette, before: tk.Widget) -> None:
        """`before`: the widget it is packed above whenever it has something to say."""
        super().__init__(parent)
        self._before: tk.Widget = before
        self._label: ttk.Label = ttk.Label(self, justify=tk.LEFT, anchor="w")
        self._label.pack(fill=tk.X, padx=12, pady=6)
        self.bind("<Configure>", lambda event: self._label.configure(wraplength=max(event.width - 30, 100)))
        self.apply_palette(palette)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._label.configure(foreground=palette.status_error)

    def show(self, messages: Sequence[str]) -> None:
        """Show these messages, or hide the banner when there are none."""
        if not messages:
            self.pack_forget()
            return
        self._label.configure(text="\n".join(f"⚠ {message}" for message in messages))
        self.pack(side=tk.TOP, fill=tk.X, before=self._before)
