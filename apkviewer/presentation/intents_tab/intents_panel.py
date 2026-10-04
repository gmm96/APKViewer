"""
"Intents" tab: a flat table with one row per entry point of the app
(action + the exported component that answers it), the combination
needed to launch it from adb, Tasker or another app.
"""

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk

from apkviewer.domain.entities.exported_intent import ExportedIntent
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.tree.record_table_panel import RecordTablePanel
from apkviewer.presentation.common.tree.tree_column import TreeColumn
from apkviewer.presentation.components_tab.component_tree_builder import ComponentTreeBuilder

_COLUMNS: tuple[TreeColumn, ...] = (
    TreeColumn("#0", "Action", width=280, min_width=160, stretch=True),
    TreeColumn("component", "Component", width=300, min_width=140, stretch=True),
    TreeColumn("type", "Type", width=100, min_width=70),
    TreeColumn("categories", "Categories", width=190, min_width=100),
    TreeColumn("data", "Data", width=220, min_width=100, stretch=True),
    TreeColumn("verify", "Auto-verify", width=100, min_width=80),
)


class IntentsPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Notebook,
        palette: ThemePalette,
        tree_builder: ComponentTreeBuilder | None = None,
    ) -> None:
        super().__init__(parent)
        self._tree_builder: ComponentTreeBuilder = tree_builder or ComponentTreeBuilder()
        self._table: RecordTablePanel = RecordTablePanel(
            self,
            palette,
            _COLUMNS,
            item_noun="entry points",
            empty_text="No exported intents.",
        )
        self._table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._table.apply_palette(palette)

    def clear(self) -> None:
        self._table.clear()

    def render(self, intents: Sequence[ExportedIntent]) -> None:
        self._table.show(self._tree_builder.build_intents(intents))
