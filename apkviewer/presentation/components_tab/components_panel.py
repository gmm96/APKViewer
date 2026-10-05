"""
"Components" tab: one table with every declared component. A row of pills
above it restricts the table to one kind (a kind with no components is
dimmed instead of opening an empty view), and each component expands to
show its intent filters.
"""

import tkinter as tk
from tkinter import ttk

from apkviewer.domain.entities.components import DeclaredComponents
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.tree.record_table_panel import RecordTablePanel
from apkviewer.presentation.common.warning_banner import WarningBanner
from apkviewer.presentation.common.tree.tree_column import TreeColumn
from apkviewer.presentation.components_tab.component_tree_builder import ComponentTreeBuilder

_COLUMNS: tuple[TreeColumn, ...] = (
    TreeColumn("#0", "Name", width=460, min_width=220, stretch=True),
    TreeColumn("type", "Type", width=110, min_width=80),
    TreeColumn("exported", "Exported", width=120, min_width=90),
    TreeColumn("permission", "Permission", width=260, min_width=100, stretch=True),
)
_ALL: str = "all"
_PILL_STYLE: str = "ToggleButton"  # a category with components (Forest theme)
_EMPTY_PILL_STYLE: str = "PillEmpty.Toolbutton"  # no components: flat text, no button box


class ComponentsPanel(ttk.Frame):
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
            item_noun="components",
            empty_text="No components declared.",
        )
        self._table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._banner: WarningBanner = WarningBanner(self, palette, before=self._table)

        self._selected: tk.StringVar = tk.StringVar(value=_ALL)
        self._pill_labels: dict[str, str] = {_ALL: "All", **dict(ComponentTreeBuilder.GROUPS)}
        self._pills: dict[str, ttk.Radiobutton] = {}
        for key in self._pill_labels:
            pill = ttk.Radiobutton(
                self._table.filter_bar,
                text=self._pill_labels[key],
                value=key,
                variable=self._selected,
                style=_PILL_STYLE,
                takefocus=False,
                command=self._on_pill_selected,
            )
            pill.pack(side=tk.LEFT, padx=(0, 4), before=self._table.filter_label)
            self._pills[key] = pill
        self._apply_pill_style(palette)
        self._update_pills({})

    def apply_palette(self, palette: ThemePalette) -> None:
        self._table.apply_palette(palette)
        self._banner.apply_palette(palette)
        self._apply_pill_style(palette)

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        self._selected.set(_ALL)
        self._table.set_category(None, refresh=False)
        self._table.clear()
        self._update_pills({})

    def render(self, components: DeclaredComponents) -> None:
        root = self._tree_builder.build_components(components)
        counts: dict[str, int] = {}
        for row in root.children:
            if row.category is not None:
                counts[row.category] = counts.get(row.category, 0) + 1

        self._selected.set(_ALL)
        self._table.set_category(None, refresh=False)
        self._table.show(root)
        self._update_pills(counts)

    # --- Pills -------------------------------------------------------------------

    @staticmethod
    def _apply_pill_style(palette: ThemePalette) -> None:
        # A pill without components loses its button box, so it reads as inactive at a
        # glance (the theme's own disabled look is nearly the same as an enabled button).
        # ttk keeps style settings per theme, so this runs on every theme change.
        ttk.Style().map(_EMPTY_PILL_STYLE, foreground=[("disabled", palette.secondary_fg)])

    def _on_pill_selected(self) -> None:
        key = self._selected.get()
        self._table.set_category(None if key == _ALL else key)

    def _update_pills(self, counts: dict[str, int]) -> None:
        total = sum(counts.values())
        for key, pill in self._pills.items():
            count = total if key == _ALL else counts.get(key, 0)
            pill.configure(
                text=f"{self._pill_labels[key]} ({count})",
                style=_PILL_STYLE if count else _EMPTY_PILL_STYLE,
                state=tk.NORMAL if count else tk.DISABLED,
            )
