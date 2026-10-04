"""
A table of records: one row per entity, one column per property, with
header sorting, a live filter, an optional category restriction and,
for rows that have nested rows, an expander showing the detail.
"""

import tkinter as tk
from collections.abc import Sequence
from dataclasses import replace
from tkinter import ttk

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
    ) -> None:
        self._sort_column: str = columns[0].id
        self._reverse: bool = False
        self._category: str | None = None
        self._column_ids: tuple[str, ...] = tuple(column.id for column in columns)
        self._item_noun: str = item_noun
        self._empty_text: str = empty_text
        super().__init__(parent, palette, columns, filter_on_top=filter_on_top)

        self._count_label: ttk.Label = ttk.Label(self.filter_bar, text="")
        self._count_label.pack(side=tk.RIGHT, padx=(5, 0), before=self.filter_entry)
        self._empty_label: ttk.Label = ttk.Label(self, text=empty_text)
        self._after_rebuild(self._root_node)

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

    def _insert(self, parent_iid: str, node: RecordNode, iid: str, is_open: bool) -> None:
        values = list(node.cells[1:])
        values += [""] * (len(self._column_ids) - 1 - len(values))
        self.tree.insert(
            parent_iid, tk.END, iid=iid, text=node.cells[0] if node.cells else "",
            values=values, open=is_open, tags=(_TAG,),
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

    def _after_rebuild(self, displayed_root: RecordNode) -> None:
        shown = len(displayed_root.children)
        total = len(self._root_node.children)
        counter = f"{shown} {self._item_noun}"
        if shown != total:
            counter = f"{shown} of {total} {self._item_noun}"
        self._count_label.configure(text=counter)

        if shown:
            self._empty_label.place_forget()
            return
        narrowed = self._filtering or self._category is not None
        self._empty_label.configure(text="No matches." if total and narrowed else self._empty_text)
        self._empty_label.place(in_=self.tree, relx=0.5, rely=0.5, anchor="center")
