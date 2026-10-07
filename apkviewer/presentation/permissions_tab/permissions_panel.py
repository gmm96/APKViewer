"""
"Permissions" tab: three plain tables (no tree), each with its own filter:

  * Permissions: requested permissions that Android defines.
  * AppOps: the requested ones with the "appop" protection (special access
    the user grants from Settings: overlays, install packages, all files...).
  * Custom permissions: anything Android doesn't define, whether the app only
    requests it (another app or a library defines it) or declares it itself.

The tables share the tab's height in proportion to their rows. Dangerous
permissions are written in the error color.
"""

import tkinter as tk
from tkinter import ttk

from apkviewer.domain.entities.permission import Permission, PermissionsInfo
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.tree.record_node import RecordNode
from apkviewer.presentation.common.tree.record_table_panel import RecordTablePanel
from apkviewer.presentation.common.tree.tree_column import TreeColumn
from apkviewer.presentation.common.warning_banner import WarningBanner
from apkviewer.presentation.permissions_tab.permission_rows import DANGEROUS_STYLE, PermissionRowBuilder

_NAME = TreeColumn("#0", "Permission", width=330, min_width=200)
_TYPE = TreeColumn("type", "Type", width=230, min_width=110)
_ORIGIN = TreeColumn("origin", "Origin", width=170, min_width=110)
_MAX_SDK = TreeColumn("max_sdk", "Max SDK", width=75, min_width=60)
_SUMMARY = TreeColumn("summary", "Summary", width=300, min_width=120)
_DESCRIPTION = TreeColumn("description", "Description", width=600, min_width=160, stretch=True)

_STANDARD_COLUMNS: tuple[TreeColumn, ...] = (_NAME, _TYPE, _MAX_SDK, _SUMMARY, _DESCRIPTION)
_CUSTOM_COLUMNS: tuple[TreeColumn, ...] = (_NAME, _TYPE, _ORIGIN, _MAX_SDK, _SUMMARY, _DESCRIPTION)

_MIN_HEIGHT_WITH_ROWS: int = 170
_MIN_HEIGHT_EMPTY: int = 95
_MAX_WEIGHT: int = 30


class _TableGroup:
    """A titled frame (with the row count) holding one filterable table."""

    def __init__(
        self,
        container: ttk.Frame,
        row: int,
        title: str,
        columns: tuple[TreeColumn, ...],
        noun: str,
        empty_text: str,
        palette: ThemePalette,
    ) -> None:
        self._container: ttk.Frame = container
        self._row: int = row
        self._title: str = title
        self._frame: ttk.LabelFrame = ttk.LabelFrame(container, text=title)
        self._frame.grid(row=row, column=0, sticky="nsew", padx=10, pady=(0, 6))
        self._frame.rowconfigure(0, weight=1)
        self._frame.columnconfigure(0, weight=1)
        self.table: RecordTablePanel = RecordTablePanel(
            self._frame,
            palette,
            columns,
            item_noun=noun,
            empty_text=empty_text,
            row_styles={DANGEROUS_STYLE: lambda p: p.status_error},
        )
        self.table.tree.configure(height=3)  # the real height comes from the grid weights
        self.table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.clear()

    def show(self, root: RecordNode) -> None:
        count = len(root.children)
        self.table.show(root)
        self._frame.configure(text=f"{self._title} ({count})")
        # A table with more rows gets more of the tab's height, but never less than a few rows.
        self._container.rowconfigure(
            self._row,
            weight=min(max(count, 4), _MAX_WEIGHT) if count else 0,
            minsize=_MIN_HEIGHT_WITH_ROWS if count else _MIN_HEIGHT_EMPTY,
        )

    def clear(self) -> None:
        self.table.clear()
        self._frame.configure(text=self._title)
        self._container.rowconfigure(self._row, weight=0, minsize=_MIN_HEIGHT_EMPTY)


class PermissionsPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Notebook,
        palette: ThemePalette,
        row_builder: PermissionRowBuilder | None = None,
    ) -> None:
        super().__init__(parent)
        self._row_builder: PermissionRowBuilder = row_builder or PermissionRowBuilder()

        self._container: ttk.Frame = ttk.Frame(self)
        self._container.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self._container.columnconfigure(0, weight=1)
        self._banner: WarningBanner = WarningBanner(self, palette, before=self._container)

        self._permissions: _TableGroup = _TableGroup(
            self._container, 0, "Permissions", _STANDARD_COLUMNS, "permissions",
            "No Android permissions requested.", palette,
        )
        self._app_ops: _TableGroup = _TableGroup(
            self._container, 1, "AppOps (special access)", _STANDARD_COLUMNS, "app ops",
            "No special-access permissions requested.", palette,
        )
        self._custom: _TableGroup = _TableGroup(
            self._container, 2, "Custom permissions", _CUSTOM_COLUMNS, "custom permissions",
            "No custom permissions requested or declared.", palette,
        )
        self._groups: tuple[_TableGroup, ...] = (self._permissions, self._app_ops, self._custom)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._banner.apply_palette(palette)
        for group in self._groups:
            group.table.apply_palette(palette)

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        for group in self._groups:
            group.clear()

    def render(self, info: PermissionsInfo) -> None:
        self._show(self._permissions, info.permissions, with_origin=False)
        self._show(self._app_ops, info.app_ops, with_origin=False)
        self._show(self._custom, info.custom_permissions, with_origin=True)

    def _show(self, group: _TableGroup, permissions: tuple[Permission, ...], with_origin: bool) -> None:
        group.show(self._row_builder.build(permissions, with_origin))
