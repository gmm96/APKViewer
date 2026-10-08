"""
A copy icon laid over the right end of a widget (a field or a list box).
It shows only while the pointer is over the widget or the widget has the
focus, and clicking it copies a text to the clipboard (the icon turns green
for a moment as confirmation).
"""

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from apkviewer.presentation.icons.field_icons import FieldIcons


class CopyIconOverlay:
    _FEEDBACK_MS: int = 900

    def __init__(
        self,
        target: tk.Widget,
        icons: FieldIcons,
        get_text: Callable[[], str],
        background: str | None = None,
        top_offset: int | None = None,
    ) -> None:
        """
        `background`: color of the surface under the icon, when it isn't the window's
        (e.g. a Text box). `top_offset`: put the icon that many pixels from the top
        instead of centering it vertically (for tall widgets).
        """
        self._target: tk.Widget = target
        self._icons: FieldIcons = icons
        self._get_text: Callable[[], str] = get_text
        self._top_offset: int | None = top_offset
        self._focused: bool = False
        self._restore_job: str | None = None

        parent = target.master  # a place() target must be the master or a child of it
        if background is None:
            self._icon: tk.Label | ttk.Label = ttk.Label(parent, image=icons.copy, cursor="hand2")
        else:
            self._icon = tk.Label(
                parent, image=icons.copy, cursor="hand2",
                background=background, borderwidth=0, highlightthickness=0,
            )
        for widget in (target, self._icon):
            widget.bind("<Enter>", self._schedule_refresh, add="+")
            widget.bind("<Leave>", self._schedule_refresh, add="+")
        target.bind("<FocusIn>", lambda _event: self._set_focused(True), add="+")
        target.bind("<FocusOut>", lambda _event: self._set_focused(False), add="+")
        self._icon.bind("<Button-1>", self.copy)
        self.refresh()

    @property
    def is_shown(self) -> bool:
        return bool(self._icon.winfo_manager())

    def refresh_icons(self) -> None:
        """Re-read the icon after a theme change."""
        self._icon.configure(image=self._icons.copy)

    def set_background(self, color: str) -> None:
        if isinstance(self._icon, tk.Label):
            self._icon.configure(background=color)

    # --- Visibility ----------------------------------------------------------------------------

    def refresh(self) -> None:
        if self._focused or self._pointer_inside():
            if self._top_offset is None:
                self._icon.place(in_=self._target, relx=1.0, x=-8, rely=0.5, anchor="e")
            else:
                self._icon.place(in_=self._target, relx=1.0, x=-8, y=self._top_offset, anchor="ne")
        else:
            self._icon.place_forget()

    def _set_focused(self, focused: bool) -> None:
        self._focused = focused
        self.refresh()

    def _schedule_refresh(self, _event: tk.Event) -> None:
        # Moving from the widget onto the icon fires Leave then Enter: judge by where the pointer is.
        self._target.after_idle(self.refresh)

    def _pointer_inside(self) -> bool:
        x, y = self._target.winfo_pointerxy()
        left, top = self._target.winfo_rootx(), self._target.winfo_rooty()
        return (
            left <= x < left + self._target.winfo_width()
            and top <= y < top + self._target.winfo_height()
        )

    # --- Copy ------------------------------------------------------------------------------------

    def copy(self, _event: tk.Event | None = None) -> str:
        self._target.clipboard_clear()
        self._target.clipboard_append(self._get_text())
        self._icon.configure(image=self._icons.copied)
        if self._restore_job is not None:
            self._target.after_cancel(self._restore_job)
        self._restore_job = self._target.after(self._FEEDBACK_MS, self._restore_icon)
        return "break"

    def _restore_icon(self) -> None:
        self._restore_job = None
        self._icon.configure(image=self._icons.copy)
