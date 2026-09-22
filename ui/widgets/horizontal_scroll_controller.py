"""
Decides whether the Manifest view needs a horizontal scrollbar.

Tk's Text widget only accounts for lines it has actually laid out (i.e.
scrolled into view at least once) when computing its horizontal scroll
region. In practice this means the standard `xscrollcommand` callback
reports a scrollbar visibility/size that keeps changing as the user
scrolls vertically through a tall document, even though the real content
never changed.

This controller sidesteps that Tk quirk entirely: it measures the widest
line of the *whole* document itself (once per render, and again on every
resize) and decides the scrollbar's visibility from that single, stable
value, instead of trusting Tk's partial live callback.
"""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


class ManifestHorizontalScrollController:
    def __init__(self, text_widget: tk.Text, scrollbar: ttk.Scrollbar, grid_kwargs: dict, font):
        self._text = text_widget
        self._scrollbar = scrollbar
        self._grid_kwargs = grid_kwargs
        self._font = font if isinstance(font, tkfont.Font) else tkfont.Font(font=font)
        self._content_width_px = 0

        self._text.bind("<Configure>", lambda _event: self._refresh_visibility())

    def on_content_changed(self, content: str) -> None:
        """Call once after new content has been inserted into the text widget."""
        self._content_width_px = self._measure_longest_line(content)
        self._refresh_visibility()

    def _measure_longest_line(self, content: str) -> int:
        # The widget uses a monospace font, so the line with the most
        # characters is guaranteed to also be the widest one in pixels -
        # no need to measure every single line.
        longest_line = max(content.splitlines(), key=len, default="")
        return self._font.measure(longest_line)

    def _refresh_visibility(self) -> None:
        visible_width = self._text.winfo_width()
        if self._content_width_px > visible_width:
            self._scrollbar.grid(**self._grid_kwargs)
        else:
            self._scrollbar.grid_remove()
