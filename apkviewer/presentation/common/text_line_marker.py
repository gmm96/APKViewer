"""
Highlights the line under the cursor when the user single-clicks inside a
read-only Text widget (without dragging a selection). Used by the list
fields so users can mark + copy one line at a time. The highlight color
comes from the palette (see `apply_palette`).
"""

import tkinter as tk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.config.layout import MARKED_LINE_TAG


class TextLineMarker:
    def __init__(self, tag_name: str = MARKED_LINE_TAG) -> None:
        self._tag_name: str = tag_name

    def bind(self, text_widget: tk.Text) -> None:
        text_widget.bind("<Button-1>", lambda e: e.widget.tag_remove(self._tag_name, "1.0", tk.END))
        text_widget.bind("<ButtonRelease-1>", self._on_release)

    def apply_palette(self, text_widget: tk.Text, palette: ThemePalette) -> None:
        text_widget.tag_configure(self._tag_name, background=palette.mark_bg)

    def _on_release(self, event: tk.Event) -> None:
        widget = event.widget
        if not isinstance(widget, tk.Text):
            return
        if widget.tag_ranges(tk.SEL):
            return  # a drag-selection is in progress; don't override it
        index = widget.index(f"@{event.x},{event.y}")
        line_num = index.split(".")[0]
        widget.tag_remove(self._tag_name, "1.0", tk.END)
        widget.tag_add(self._tag_name, f"{line_num}.0", f"{line_num}.end")
