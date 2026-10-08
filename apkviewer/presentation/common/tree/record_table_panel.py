"""
A table of records: one row per entity, one column per property, with
header sorting, a live filter, an optional category restriction and,
for rows that have nested rows, an expander showing the detail.
"""

import tkinter as tk
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.tree.base_tree_panel import BaseTreePanel
from apkviewer.presentation.common.tree.record_node import RecordNode
from apkviewer.presentation.common.tree.tree_column import TreeColumn
from apkviewer.presentation.config.theme import FONT_MONO_SMALL

_TAG: str = "record"


class RecordTablePanel(BaseTreePanel[RecordNode]):
    _expand_on_filter = True

    def __init__(
        self,
        parent: tk.Misc,
        palette: ThemePalette,
        columns: Sequence[TreeColumn],
        item_noun: str = "items",
        empty_text: str = "Nothing to show.",
        filter_on_top: bool = True,
        row_styles: Mapping[str, Callable[[ThemePalette], str]] | None = None,
        toolbar_row: bool = False,
        expand_buttons: bool = False,
    ) -> None:
        """`row_styles`: style name -> function giving its text color from the palette."""
        self._row_styles: dict[str, Callable[[ThemePalette], str]] = dict(row_styles or {})
        self._sort_column: str = columns[0].id
        self._reverse: bool = False
        self._category: str | None = None
        self._column_ids: tuple[str, ...] = tuple(column.id for column in columns)
        super().__init__(
            parent, palette, columns, filter_on_top=filter_on_top, toolbar_row=toolbar_row,
            expand_buttons=expand_buttons, item_noun=item_noun, empty_text=empty_text,
        )

    # --- Public API ------------------------------------------------------------

    def set_category(self, category: str | None, refresh: bool = True) -> None:
        """Show only the top-level rows of that category (None = all of them)."""
        self._category = category
        if refresh:
            self._apply_filter()

    # --- BaseTreePanel hooks -------------------------------------------------------

    def _empty_root(self) -> RecordNode:
        return RecordNode.create_root()

    def _filter_root(self, root: RecordNode, query: str) -> RecordNode:
        rows = root.children
        if self._category is not None:
            rows = tuple(row for row in rows if row.category == self._category)
        query_lower = query.strip().lower()
        if query_lower:
            rows = tuple(row for row in rows if row.contains(query_lower))
        return replace(root, children=rows)

    def _children_of(self, node: RecordNode) -> Sequence[RecordNode]:
        if node.iid != "":
            return node.children  # nested rows keep their natural order
        index = self._column_ids.index(self._sort_column)
        return sorted(
            node.children,
            key=lambda row: row.cells[index].lower() if index < len(row.cells) else "",
            reverse=self._reverse,
        )

    def _node_iid(self, node: RecordNode) -> str:
        return node.iid

    def _default_open(self, node: RecordNode) -> bool:
        return node.open_by_default

    def _insert(self, parent_iid: str, node: RecordNode, iid: str, is_open: bool) -> None:
        values = list(node.cells[1:])
        values += [""] * (len(self._column_ids) - 1 - len(values))
        self.tree.insert(
            parent_iid, tk.END, iid=iid, text=node.cells[0] if node.cells else "",
            values=values, open=is_open,
            tags=(_TAG, node.style) if node.style else (_TAG,),
        )

    def _sort_state(self) -> tuple[str, bool]:
        return self._sort_column, self._reverse

    def _toggle_sort(self, column_id: str) -> None:
        if column_id == self._sort_column:
            self._reverse = not self._reverse
        else:
            self._sort_column = column_id
            self._reverse = False

    def _configure_tags(self, palette: ThemePalette) -> None:
        self.tree.tag_configure(_TAG, font=FONT_MONO_SMALL)
        for style, color_of in self._row_styles.items():
            self.tree.tag_configure(style, foreground=color_of(palette))

    def _is_narrowed(self) -> bool:
        return self._filtering or self._category is not None
