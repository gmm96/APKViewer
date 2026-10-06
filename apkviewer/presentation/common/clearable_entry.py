"""
Text field with an X at its right end that empties it. The X is shown
whenever the field has text and hidden when it is empty.
"""

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from apkviewer.presentation.icons.field_icons import ENTRY_STYLE, FieldIcons


class ClearableEntry(ttk.Entry):
    def __init__(
        self,
        parent: tk.Misc,
        icons: FieldIcons,
        on_clear: Callable[[], None] | None = None,
        **options: object,
    ) -> None:
        FieldIcons.configure_entry_style()
        self._variable: tk.StringVar = tk.StringVar(master=parent)
        super().__init__(parent, textvariable=self._variable, style=ENTRY_STYLE, **options)
        self._icons: FieldIcons = icons
        self._on_clear: Callable[[], None] | None = on_clear

        # A sibling of the entry (a place() target must be its master or a child of it).
        self._clear_label: ttk.Label = ttk.Label(parent, image=icons.clear, cursor="hand2")
        self._clear_label.bind("<Button-1>", self._clear)
        self._variable.trace_add("write", lambda *_args: self._refresh())
        self._refresh()

    def refresh_icons(self) -> None:
        """Re-read the icon after a theme change."""
        FieldIcons.configure_entry_style()
        self._clear_label.configure(image=self._icons.clear)

    def destroy(self) -> None:
        self._clear_label.destroy()
        super().destroy()

    def _refresh(self) -> None:
        if self._variable.get():
            self._clear_label.place(in_=self, relx=1.0, x=-8, rely=0.5, anchor="e")
        else:
            self._clear_label.place_forget()

    def _clear(self, _event: tk.Event | None = None) -> str:
        self._variable.set("")
        self.focus_set()
        if self._on_clear is not None:
            self._on_clear()
        return "break"
