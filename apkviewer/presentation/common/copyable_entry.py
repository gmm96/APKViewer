"""
Read-only text field with a copy icon at its right end. The icon only
shows while the pointer is over the field or the field has the focus.
"""

import tkinter as tk
from tkinter import ttk

from apkviewer.presentation.icons.field_icons import ENTRY_STYLE, FieldIcons


class CopyableEntry(ttk.Frame):
    _FEEDBACK_MS: int = 900

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        icons: FieldIcons,
        font: tuple | None = None,
    ) -> None:
        super().__init__(parent)
        self._text: str = text
        self._icons: FieldIcons = icons
        self._focused: bool = False
        self._restore_job: str | None = None

        FieldIcons.configure_entry_style()
        self.entry: ttk.Entry = ttk.Entry(self, style=ENTRY_STYLE)
        if font is not None:
            self.entry.configure(font=font)
        self.entry.insert(0, text)
        self.entry.configure(state="readonly")
        self.entry.pack(fill=tk.X, expand=True)

        self._icon: ttk.Label = ttk.Label(self, image=icons.copy, cursor="hand2")
        for widget in (self.entry, self._icon):
            widget.bind("<Enter>", self._schedule_refresh, add="+")
            widget.bind("<Leave>", self._schedule_refresh, add="+")
        self.entry.bind("<FocusIn>", lambda _event: self._set_focused(True), add="+")
        self.entry.bind("<FocusOut>", lambda _event: self._set_focused(False), add="+")
        self._icon.bind("<Button-1>", self._copy)
        self._refresh()

    def get(self) -> str:
        return self._text

    def refresh_icons(self) -> None:
        """Re-read the icons after a theme change."""
        FieldIcons.configure_entry_style()
        self._icon.configure(image=self._icons.copy)

    # --- Visibility -------------------------------------------------------------------

    def _set_focused(self, focused: bool) -> None:
        self._focused = focused
        self._refresh()

    def _schedule_refresh(self, _event: tk.Event) -> None:
        # Moving from the field onto the icon fires Leave then Enter: judge by where the pointer is.
        self.after_idle(self._refresh)

    def _refresh(self) -> None:
        if self._focused or self._pointer_inside():
            self._icon.place(in_=self.entry, relx=1.0, x=-8, rely=0.5, anchor="e")
        else:
            self._icon.place_forget()

    def _pointer_inside(self) -> bool:
        x, y = self.winfo_pointerxy()
        left, top = self.winfo_rootx(), self.winfo_rooty()
        return left <= x < left + self.winfo_width() and top <= y < top + self.winfo_height()

    # --- Copy --------------------------------------------------------------------------------

    def _copy(self, _event: tk.Event | None = None) -> str:
        self.clipboard_clear()
        self.clipboard_append(self._text)
        self._icon.configure(image=self._icons.copied)  # brief confirmation
        if self._restore_job is not None:
            self.after_cancel(self._restore_job)
        self._restore_job = self.after(self._FEEDBACK_MS, self._restore_icon)
        return "break"

    def _restore_icon(self) -> None:
        self._restore_job = None
        self._icon.configure(image=self._icons.copy)
