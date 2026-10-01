"""
Bottom status bar showing the current operation state.
"""

import tkinter as tk
from tkinter import ttk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.status_level import StatusLevel


class StatusBar(ttk.Frame):
    def __init__(self, parent: tk.Tk, palette: ThemePalette) -> None:
        super().__init__(parent, relief="sunken", borderwidth=1)
        self._palette: ThemePalette = palette
        self._level: StatusLevel = StatusLevel.NEUTRAL
        self.label: ttk.Label = ttk.Label(self, text="Ready.")
        self.label.pack(side="left", padx=10, pady=2)
        self._refresh_color()

    def set_status(self, message: str, level: StatusLevel = StatusLevel.NEUTRAL) -> None:
        self._level = level
        self.label.config(text=message)
        self._refresh_color()

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        self._refresh_color()

    def _refresh_color(self) -> None:
        colors = {
            StatusLevel.NEUTRAL: self._palette.status_neutral,
            StatusLevel.INFO: self._palette.status_info,
            StatusLevel.SUCCESS: self._palette.status_success,
            StatusLevel.ERROR: self._palette.status_error,
        }
        self.label.config(foreground=colors[self._level])
