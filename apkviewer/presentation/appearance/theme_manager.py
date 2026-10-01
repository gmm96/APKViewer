"""
Owns the current color mode: resolves it into a scheme, activates the
matching ttk theme and tells the interested widgets to re-apply their
palette. Widgets never know about modes, only about palettes.
"""

import tkinter as tk
from collections.abc import Callable, Mapping

from apkviewer.application.resolve_color_scheme import ResolveColorScheme
from apkviewer.domain.entities.color_mode import ColorMode
from apkviewer.domain.entities.color_scheme import ColorScheme

from .forest_theme import ForestTheme
from .palettes import PALETTES
from .theme_palette import ThemePalette

PaletteListener = Callable[[ThemePalette], None]


class ThemeManager:
    def __init__(
        self,
        root: tk.Tk,
        forest_theme: ForestTheme,
        resolve_color_scheme: ResolveColorScheme,
        initial_mode: ColorMode = ColorMode.AUTO,
        palettes: Mapping[ColorScheme, ThemePalette] | None = None,
    ) -> None:
        self._root: tk.Tk = root
        self._forest_theme: ForestTheme = forest_theme
        self._resolve_color_scheme: ResolveColorScheme = resolve_color_scheme
        self._palettes: Mapping[ColorScheme, ThemePalette] = palettes or PALETTES
        self._listeners: list[PaletteListener] = []
        self._palette: ThemePalette = self._activate(initial_mode)
        self._mode: ColorMode = initial_mode

    @property
    def mode(self) -> ColorMode:
        return self._mode

    @property
    def palette(self) -> ThemePalette:
        return self._palette

    def subscribe(self, listener: PaletteListener) -> None:
        self._listeners.append(listener)

    def set_mode(self, mode: ColorMode) -> None:
        # Activate first: if it fails, the previous mode stays in effect.
        self._palette = self._activate(mode)
        self._mode = mode
        for listener in list(self._listeners):
            listener(self._palette)

    def _activate(self, mode: ColorMode) -> ThemePalette:
        scheme = self._resolve_color_scheme.execute(mode)
        self._forest_theme.apply(scheme)
        palette = self._palettes[scheme]
        self._root.configure(background=palette.window_bg)
        # Toplevel dialogs are created on demand: the option database gives
        # every new one the right background without any per-dialog code.
        self._root.option_add("*Toplevel.background", palette.window_bg)
        return palette
