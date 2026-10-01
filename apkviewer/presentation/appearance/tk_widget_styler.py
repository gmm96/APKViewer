"""
Applies a palette to the classic Tk widgets that ttk theming does not
reach (Text and Menu).
"""

import tkinter as tk

from .theme_palette import ThemePalette


class TkWidgetStyler:
    @staticmethod
    def style_text(widget: tk.Text, palette: ThemePalette) -> None:
        widget.configure(
            background=palette.text_bg,
            foreground=palette.text_fg,
            insertbackground=palette.text_fg,
            selectbackground=palette.selection_bg,
            selectforeground=palette.selection_fg,
            inactiveselectbackground=palette.selection_bg,
            highlightbackground=palette.window_bg,
            highlightcolor=palette.selection_bg,
        )

    @staticmethod
    def style_menu(menu: tk.Menu, palette: ThemePalette) -> None:
        menu.configure(
            background=palette.window_bg,
            foreground=palette.text_fg,
            activebackground=palette.selection_bg,
            activeforeground=palette.selection_fg,
            disabledforeground=palette.disabled_fg,
            selectcolor=palette.text_fg,
        )
