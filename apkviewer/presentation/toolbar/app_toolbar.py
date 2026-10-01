"""
Generic, data-driven top menu bar. It knows nothing about what the items
do: the caller describes the menus declaratively (AppToolbarItem,
AppToolbarChoiceGroup, or None for a separator) and can enable/disable
items by key. Adding a menu or an entry therefore never requires touching
this class.

The bar is drawn with regular widgets (not the native menubar) so that its
drop-downs are popped up and dismissed by the same PopupMenuController as
every other context menu of the app: they close when the user clicks
anywhere else or when the application loses focus.

Colors come from the current palette; `apply_palette` re-tints the menus
and their icons when the color mode changes.
"""

import tkinter as tk
from collections.abc import Callable, Iterable, Mapping, Sequence
from tkinter import ttk
from typing import Optional

from PIL import Image, ImageTk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.appearance.tk_widget_styler import TkWidgetStyler
from apkviewer.presentation.common.popup_menu_controller import PopupMenuController
from apkviewer.presentation.icons.icon_loader import IconLoader
from apkviewer.presentation.viewmodels.app_toolbar_choice_group import AppToolbarChoiceGroup
from apkviewer.presentation.viewmodels.app_toolbar_item import AppToolbarItem


# A None entry renders as a separator.
MenuEntry = AppToolbarItem | AppToolbarChoiceGroup | None


class AppToolbar:
    _ICON_SIZE: tuple[int, int] = (16, 16)
    _ICON_PADDING: int = 8
    _BUTTON_STYLE: str = "Menubar.Toolbutton"

    def __init__(
        self,
        root: tk.Tk,
        menus: Mapping[str, Sequence[MenuEntry]],
        palette: ThemePalette,
        icon_loader: Optional[IconLoader] = None,
    ) -> None:
        self._root: tk.Tk = root
        self._palette: ThemePalette = palette
        self._icon_loader: IconLoader = icon_loader or IconLoader()
        self._icons: list[ImageTk.PhotoImage] = []
        self._blank_icon: ImageTk.PhotoImage = self._create_blank_icon()
        self._positions: dict[str, tuple[tk.Menu, int]] = {}
        self._entry_icons: list[tuple[tk.Menu, int, str]] = []  # (menu, index, icon path)
        self._choice_vars: dict[str, tk.StringVar] = {}
        self._commands: dict[str, Callable[[], None]] = {}
        self._enabled: dict[str, bool] = {}

        self._configure_button_style()
        self._bar: ttk.Frame = ttk.Frame(root)
        self._bar.pack(side=tk.TOP, fill=tk.X)
        ttk.Separator(root, orient="horizontal").pack(side=tk.TOP, fill=tk.X)

        self._menus: dict[str, tk.Menu] = {}
        self._buttons: dict[str, ttk.Button] = {}
        self._popups: dict[str, PopupMenuController] = {}
        self._was_open_on_press: dict[str, bool] = {}

        for title, entries in menus.items():
            menu = tk.Menu(self._bar, tearoff=0)
            self._populate(menu, entries)
            self._menus[title] = menu
            self._buttons[title] = self._create_button(title)

        # Created once every button exists: clicking any menu button is
        # handled by the button itself, never as "clicked elsewhere".
        for title, menu in self._menus.items():
            self._popups[title] = PopupMenuController(
                root,
                menu,
                ignored_widgets=self._buttons.values()
            )
        self._style_menus()

    def set_enabled(self, keys: Iterable[str], enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for key in keys:
            menu, index = self._positions[key]
            menu.entryconfigure(index, state=state)
            self._enabled[key] = enabled

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        self._configure_button_style()  # ttk style settings are kept per theme
        self._style_menus()
        self._icons.clear()
        for menu, index, icon_path in self._entry_icons:
            menu.entryconfigure(index, image=self._load_icon(icon_path))

    # --- Styling -------------------------------------------------------------

    def _configure_button_style(self) -> None:
        ttk.Style().configure(self._BUTTON_STYLE, padding=(10, 3))

    def _style_menus(self) -> None:
        for menu in self._menus.values():
            TkWidgetStyler.style_menu(menu, self._palette)

    # --- Menu buttons --------------------------------------------------------

    def _create_button(self, title: str) -> ttk.Button:
        button = ttk.Button(
            self._bar,
            text=title,
            style=self._BUTTON_STYLE,
            takefocus=False,
            command=lambda: self._toggle(title),
        )
        button.pack(side=tk.LEFT)
        # Remember whether the drop-down was open *before* this click, so
        # clicking the button of an open menu closes it instead of
        # immediately re-opening it.
        button.bind("<ButtonPress-1>", lambda _event: self._remember_state(title), add="+")
        button.bind(
            "<Enter>",
            lambda _event: self._toggle(title)
                if (PopupMenuController._open_controller is not None and not self._popups[title].is_open)
                else None
        )
        return button

    def _remember_state(self, title: str) -> None:
        self._was_open_on_press[title] = self._popups[title].is_open

    def _toggle(self, title: str) -> None:
        popup = self._popups[title]
        was_open = self._was_open_on_press.pop(title, popup.is_open)
        if was_open:
            popup.unpost()
            return
        button = self._buttons[title]
        popup.post(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())

    # --- Construction --------------------------------------------------------

    def _populate(self, menu: tk.Menu, entries: Sequence[MenuEntry]) -> None:
        # Entries without an icon get a transparent spacer so labels stay aligned.
        has_icons = self._uses_icons(entries)
        for entry in entries:
            if entry is None:
                menu.add_separator()
            elif isinstance(entry, AppToolbarChoiceGroup):
                self._add_choice_group(menu, entry, has_icons)
            else:
                self._add_item(menu, entry, has_icons)

    @staticmethod
    def _uses_icons(entries: Sequence[MenuEntry]) -> bool:
        for entry in entries:
            if isinstance(entry, AppToolbarItem) and entry.icon_path:
                return True
            if isinstance(entry, AppToolbarChoiceGroup) and any(c.icon_path for c in entry.choices):
                return True
        return False

    def _add_item(self, menu: tk.Menu, item: AppToolbarItem, use_icons: bool) -> None:
        options: dict = {
            "label": f"{item.label:<30}",
            "command": lambda key=item.key: self._invoke(key),
        }
        if item.accelerator:
            options["accelerator"] = item.accelerator
        if use_icons:
            options["image"] = self._icon_option(item.icon_path)
            options["compound"] = tk.LEFT
        menu.add_command(**options)

        index = self._last_index(menu)
        self._positions[item.key] = (menu, index)
        self._commands[item.key] = item.command
        self._enabled[item.key] = True
        if item.icon_path:
            self._entry_icons.append((menu, index, item.icon_path))
        if item.shortcut:
            self._root.bind(
                item.shortcut,
                lambda _event, key=item.key: self._invoke(key)  # type: ignore
            )

    def _add_choice_group(self, menu: tk.Menu, group: AppToolbarChoiceGroup, use_icons: bool) -> None:
        """A disabled title followed by radio entries (exactly one selected)."""
        title_options: dict = {"label": f"{group.title:<30}", "state": tk.DISABLED}
        if use_icons:
            title_options["image"] = self._blank_icon
            title_options["compound"] = tk.LEFT
        menu.add_command(**title_options)

        variable = tk.StringVar(master=menu, value=group.selected_key)
        self._choice_vars[group.key] = variable
        for choice in group.choices:
            options: dict = {
                "label": f"{choice.label:<30}",
                "variable": variable,
                "value": choice.key,
                "command": choice.command,
            }
            if use_icons:
                options["image"] = self._icon_option(choice.icon_path)
                options["compound"] = tk.LEFT
            menu.add_radiobutton(**options)
            if choice.icon_path:
                self._entry_icons.append((menu, self._last_index(menu), choice.icon_path))

    @staticmethod
    def _last_index(menu: tk.Menu) -> int:
        index = menu.index(tk.END)
        return index if index is not None else 0

    def _icon_option(self, icon_path: str | None) -> ImageTk.PhotoImage:
        return self._load_icon(icon_path) if icon_path else self._blank_icon

    def _load_icon(self, icon_path: str) -> ImageTk.PhotoImage:
        icon = self._icon_loader.load_icon(
            icon_path,
            size=self._ICON_SIZE,
            hex_color=self._palette.icon_tint,
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
