"""
Read-only text field with a copy icon at its right end. The icon only
shows while the pointer is over the field or the field has the focus.
"""

import tkinter as tk
from tkinter import ttk

from apkviewer.presentation.common.copy_icon_overlay import CopyIconOverlay
from apkviewer.presentation.icons.field_icons import ENTRY_STYLE, FieldIcons


class CopyableEntry(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        icons: FieldIcons,
        font: tuple | None = None,
    ) -> None:
        super().__init__(parent)
        self._text: str = text

        FieldIcons.configure_entry_style()
        self.entry: ttk.Entry = ttk.Entry(self, style=ENTRY_STYLE)
        if font is not None:
            self.entry.configure(font=font)
        self.entry.insert(0, text)
        self.entry.configure(state="readonly")
        self.entry.pack(fill=tk.X, expand=True)
        self.overlay: CopyIconOverlay = CopyIconOverlay(self.entry, icons, lambda: self._text)

    def get(self) -> str:
        return self._text

    def refresh_icons(self) -> None:
        """Re-read the icons after a theme change."""
        FieldIcons.configure_entry_style()
        self.overlay.refresh_icons()
