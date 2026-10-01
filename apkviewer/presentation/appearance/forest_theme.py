"""
Loads and activates the Forest ttk theme (https://github.com/rdbende/Forest-ttk-theme,
MIT). Each variant is sourced from its .tcl file only once and can then be
switched freely at runtime.
"""

import tkinter as tk
from tkinter import ttk

from apkviewer.domain.entities.color_scheme import ColorScheme
from apkviewer.presentation.icons.asset_path_resolver import AssetPathResolver


class ForestTheme:
    _THEME_DIR: str = "assets/theme/forest"
    _THEME_NAMES: dict[ColorScheme, str] = {
        ColorScheme.LIGHT: "forest-light",
        ColorScheme.DARK: "forest-dark",
    }

    def __init__(self, root: tk.Tk, asset_path_resolver: AssetPathResolver | None = None) -> None:
        self._root: tk.Tk = root
        self._asset_path_resolver: AssetPathResolver = asset_path_resolver or AssetPathResolver()
        self._loaded: set[str] = set()

    def apply(self, scheme: ColorScheme) -> None:
        name = self._THEME_NAMES[scheme]
        if name not in self._loaded:
            tcl_path = self._asset_path_resolver.resolve(f"{self._THEME_DIR}/{name}.tcl")
            self._root.tk.call("source", tcl_path)
            self._loaded.add(name)
        ttk.Style(self._root).theme_use(name)
