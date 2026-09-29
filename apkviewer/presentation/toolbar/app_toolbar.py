"""
Generic, data-driven top menu bar. It knows nothing about what the items
do: the caller describes the menus declaratively (MenuItem / None for a
separator) and can enable/disable items by key. Adding a menu or an entry
therefore never requires touching this class.

It also makes sure that an open drop-down never gets "stuck": it is closed
when the user clicks elsewhere in the app or when the app loses focus.
"""

import tkinter as tk
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Optional

from PIL import Image, ImageTk

from apkviewer.presentation.icons.icon_loader import IconLoader
from apkviewer.presentation.viewmodels.app_toolbar_item import AppToolbarItem


# A None entry renders as a separator.
MenuEntry = Optional[AppToolbarItem]


class AppToolbar:
    _ICON_SIZE: tuple[int, int] = (16, 16)
    _ICON_PADDING: int = 8
    _ICON_COLOR: str = "#333333"
    # Delay before checking whether the whole app lost focus. Focus briefly
    # moves between the window and its own popped-up menu, so checking
    # immediately would produce false positives.
    _FOCUS_CHECK_DELAY_MS: int = 100

    def __init__(
        self,
        root: tk.Tk,
        menus: Mapping[str, Sequence[MenuEntry]],
        icon_loader: Optional[IconLoader] = None,
    ) -> None:
        self._root: tk.Tk = root
        self._icon_loader: IconLoader = icon_loader or IconLoader()
        self._icons: list[ImageTk.PhotoImage] = []
        self._blank_icon: ImageTk.PhotoImage = self._create_blank_icon()
        self._positions: dict[str, tuple[tk.Menu, int]] = {}
        self._commands: dict[str, Callable[[], None]] = {}
        self._enabled: dict[str, bool] = {}
        self._dropdowns: list[tk.Menu] = []

        self._menubar: tk.Menu = tk.Menu(root)
        for title, entries in menus.items():
            menu = tk.Menu(self._menubar, tearoff=0)
            self._populate(menu, entries)
            self._menubar.add_cascade(label=title, menu=menu)
            self._dropdowns.append(menu)
        root.config(menu=self._menubar)

        self._install_dismiss_handlers()

    def set_enabled(self, keys: Iterable[str], enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for key in keys:
            menu, index = self._positions[key]
            menu.entryconfigure(index, state=state)
            self._enabled[key] = enabled

    # --- Dismiss behaviour -----------------------------------------------------

    def _install_dismiss_handlers(self) -> None:
        # 1. Close the drop-downs when clicking anywhere else inside the app.
        self._root.bind("<Button-1>", lambda _event: self._close_menus(), add="+")

        # 2. Close them when the app loses focus (e.g. clicking outside the window).
        self._root.bind("<FocusOut>", lambda _event: self._schedule_focus_check(), add="+")
        for menu in self._dropdowns:
            menu.bind("<FocusOut>", lambda _event: self._close_menus())

    def _schedule_focus_check(self) -> None:
        self._root.after(self._FOCUS_CHECK_DELAY_MS, self._close_menus_if_app_unfocused)

    def _close_menus_if_app_unfocused(self) -> None:
        # focus_displayof() is None only when no window of this app has focus.
        if self._root.focus_displayof() is None:
            self._close_menus()

    def _close_menus(self) -> None:
        for menu in self._dropdowns:
            menu.unpost()
        self._menubar.unpost()

    # --- Construction --------------------------------------------------------

    def _populate(self, menu: tk.Menu, entries: Sequence[MenuEntry]) -> None:
        # Entries without an icon get a transparent spacer so labels stay aligned.
        has_icons = any(entry is not None and entry.icon_path for entry in entries)
        for entry in entries:
            if entry is None:
                menu.add_separator()
                continue
            self._add_item(menu, entry, has_icons)

    def _add_item(self, menu: tk.Menu, item: AppToolbarItem, use_icons: bool) -> None:
        options: dict = {
            "label": item.label,
            "command": lambda key=item.key: self._invoke(key),
        }
        if item.accelerator:
            options["accelerator"] = item.accelerator
        if use_icons:
            options["image"] = self._icon_for(item)
            options["compound"] = tk.LEFT
        menu.add_command(**options)

        self._positions[item.key] = (menu, menu.index(tk.END))
        self._commands[item.key] = item.command
        self._enabled[item.key] = True
        if item.shortcut:
            self._root.bind(item.shortcut, lambda _event, key=item.key: self._invoke(key))

    def _icon_for(self, item: AppToolbarItem) -> ImageTk.PhotoImage:
        if not item.icon_path:
            return self._blank_icon
        icon = self._icon_loader.load_icon(
            item.icon_path,
            size=self._ICON_SIZE,
            hex_color=self._ICON_COLOR,
            padding_left=self._ICON_PADDING,
            padding_right=self._ICON_PADDING,
        )
        self._icons.append(icon)
        return icon

    def _create_blank_icon(self) -> ImageTk.PhotoImage:
        width = self._ICON_SIZE[0] + 2 * self._ICON_PADDING
        return ImageTk.PhotoImage(Image.new("RGBA", (width, self._ICON_SIZE[1]), (0, 0, 0, 0)))

    def _invoke(self, key: str) -> None:
        # Keyboard shortcuts bypass the menu's own disabled state, so check it here.
        if self._enabled.get(key, False):
            self._commands[key]()
