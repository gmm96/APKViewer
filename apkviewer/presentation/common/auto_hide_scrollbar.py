"""
Wraps a ttk.Scrollbar so it hides itself (via grid_remove) whenever the
whole content is already visible, and re-grids it otherwise. Bind its
`scroll_command` method to a widget's xscrollcommand/yscrollcommand.
"""

from tkinter import ttk
from typing import Any

class AutoHideScrollbar:
    def __init__(self, scrollbar: ttk.Scrollbar, grid_kwargs: dict[str, Any]) -> None:
        self._scrollbar: ttk.Scrollbar = scrollbar
        self._grid_kwargs: dict[str, Any] = grid_kwargs

    def scroll_command(self, first: float, last: float) -> None:
        if float(first) <= 0.0 and float(last) >= 1.0:
            self._scrollbar.grid_remove()
        else:
            self._scrollbar.grid(**self._grid_kwargs)
        self._scrollbar.set(first, last)
