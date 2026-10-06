"""
Starting point of every tree of the app. It owns what all of them share:
the Treeview with auto-hiding scrollbars, header-click sorting with arrow
indicators, a live text filter, open/closed state preservation and an
optional maximum height (in rows) after which the tree scrolls instead of
growing.

Subclasses only say how their nodes are ordered, filtered and inserted.

NOTE: a subclass must set the state its hooks need (e.g. its sorter)
BEFORE calling `super().__init__`, because this constructor already
builds the widgets and calls those hooks.
"""

import tkinter as tk
from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import partial
from tkinter import ttk
from typing import Generic, TypeVar

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.auto_hide_scrollbar import AutoHideScrollbar
from apkviewer.presentation.common.clearable_entry import ClearableEntry
from apkviewer.presentation.common.tree.tree_column import TreeColumn
from apkviewer.presentation.icons.field_icons import FieldIcons
from apkviewer.presentation.icons.icon_loader import IconLoader

NodeT = TypeVar("NodeT")

ARROW_UP: str = "⏶"
ARROW_DOWN: str = "⏷"


class BaseTreePanel(ttk.Frame, Generic[NodeT], ABC):
    # When True, filtering opens every node that has children (so matches are
    # visible) instead of restoring the user's own open/closed choices.
    _expand_on_filter: bool = False

    def __init__(
        self,
        parent: tk.Misc,
        palette: ThemePalette,
        columns: Sequence[TreeColumn],
        max_visible_rows: int | None = None,
        min_visible_rows: int = 3,
        filter_on_top: bool = False,
    ) -> None:
        """`max_visible_rows=None` makes the tree fill the space it is given."""
        super().__init__(parent)
        self._columns: tuple[TreeColumn, ...] = tuple(columns)
        self._max_rows: int | None = max_visible_rows
        self._min_rows: int = min_visible_rows
        self._root_node: NodeT = self._empty_root()
        self._node_states: dict[str, bool] = {}
        self._filtering: bool = False
        self._tree_row: int = 1 if filter_on_top else 0
        self._filter_row: int = 0 if filter_on_top else 2

        self._field_icons: FieldIcons = FieldIcons(IconLoader(), palette)

        self.rowconfigure(self._tree_row, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_tree(palette)
        self._build_filter_bar()
        self._update_heading_labels()
        self._fit_height()

    # --- Hooks ---------------------------------------------------------------

    @abstractmethod
    def _empty_root(self) -> NodeT:
        """The (invisible) node that holds the top-level entries."""

    @abstractmethod
    def _filter_root(self, root: NodeT, query: str) -> NodeT:
        """A copy of the tree keeping only what matches `query` (the root itself if empty)."""

    @abstractmethod
    def _children_of(self, node: NodeT) -> Sequence[NodeT]:
        """The children of `node` in display order."""

    @abstractmethod
    def _node_iid(self, node: NodeT) -> str:
        """Unique, stable id of the node inside the Treeview."""

    @abstractmethod
    def _insert(self, parent_iid: str, node: NodeT, iid: str, is_open: bool) -> None:
        """Insert one node (its children are inserted by the caller)."""

    @abstractmethod
    def _sort_state(self) -> tuple[str, bool]:
        """(id of the column currently sorted, descending?)."""

    @abstractmethod
    def _toggle_sort(self, column_id: str) -> None:
        """Sort by that column; asking again for the same one flips the direction."""

    def _default_open(self, node: NodeT) -> bool:
        return False

    def _has_children(self, node: NodeT) -> bool:
        return bool(self._children_of(node))

    def _configure_tags(self, palette: ThemePalette) -> None:
        """Configure the Treeview tags that depend on the palette."""

    def _after_rebuild(self, displayed_root: NodeT) -> None:
        """Called every time the visible rows were rebuilt (counters, empty states...)."""

    # --- Public API ------------------------------------------------------------

    def show(self, root: NodeT) -> None:
        self._root_node = root
        self._node_states.clear()
        self._filtering = False
        self.filter_entry.delete(0, tk.END)
        self._rebuild(root)

    def clear(self) -> None:
        self.show(self._empty_root())

    def apply_palette(self, palette: ThemePalette) -> None:
        self._apply_tree_style(palette)
        self._field_icons.apply_palette(palette)
        self.filter_entry.refresh_icons()

    def expand_all(self) -> None:
        """Open every row that is currently listed (respecting the filter / category)."""
        self._set_all_open(True)

    def collapse_all(self) -> None:
        self._set_all_open(False)

    def _set_all_open(self, is_open: bool) -> None:
        self._apply_open_state("", is_open)
        self._fit_height()

    def _apply_open_state(self, parent_iid: str, is_open: bool) -> None:
        for iid in self.tree.get_children(parent_iid):
            if self.tree.get_children(iid):
                self.tree.item(iid, open=is_open)
                self._node_states[iid] = is_open  # remembered across filter / category changes
                self._apply_open_state(iid, is_open)

    # --- Construction ------------------------------------------------------------

    def _build_tree(self, palette: ThemePalette) -> None:
        data_columns = [column.id for column in self._columns if column.id != "#0"]
        options: dict = {"columns": data_columns, "show": "tree headings"}
        if self._max_rows is not None:
            options["height"] = self._min_rows
        self.tree: ttk.Treeview = ttk.Treeview(self, **options)

        for column in self._columns:
            self.tree.column(
                column.id,
                width=column.width,
                minwidth=column.min_width,
                stretch=column.stretch,
                anchor="w",
            )
            self.tree.heading(column.id, anchor="w", command=partial(self._on_heading_click, column.id))

        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        v_auto = AutoHideScrollbar(v_scroll, {"row": self._tree_row, "column": 1, "sticky": "ns"})
        h_auto = AutoHideScrollbar(h_scroll, {"row": self._tree_row + 1, "column": 0, "sticky": "ew"})
        self.tree.configure(yscrollcommand=v_auto.scroll_command, xscrollcommand=h_auto.scroll_command)
        self.tree.grid(row=self._tree_row, column=0, sticky="nsew")

        self.tree.bind("<<TreeviewOpen>>", self._on_toggle, add="+")
        self.tree.bind("<<TreeviewClose>>", self._on_toggle, add="+")
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.tree.bind(sequence, self._on_mousewheel)
        self._apply_tree_style(palette)

    def _apply_tree_style(self, palette: ThemePalette) -> None:
        # ttk style settings are stored per theme: re-applied on every theme change.
        ttk.Style().configure("Treeview.Heading", padding=(8, 6))
        self._configure_tags(palette)

    def _build_filter_bar(self) -> None:
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=self._filter_row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        # Public: other widgets (e.g. category pills) can be packed into this bar.
        self.filter_bar: ttk.Frame = filter_frame
        self.filter_label: ttk.Label = ttk.Label(filter_frame, text="Filter:")
        self.filter_label.pack(side=tk.LEFT)
        self.filter_entry: ClearableEntry = ClearableEntry(
            filter_frame, self._field_icons, on_clear=self._apply_filter
        )
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda _event: self._apply_filter())

    # --- Sorting / filtering / rendering ---------------------------------------------

    def _on_heading_click(self, column_id: str) -> None:
        self._toggle_sort(column_id)
        self._update_heading_labels()
        self._apply_filter()

    def _update_heading_labels(self) -> None:
        sorted_column, reverse = self._sort_state()
        arrow = f"  {ARROW_UP}" if reverse else f"  {ARROW_DOWN}"
        for column in self._columns:
            suffix = arrow if column.id == sorted_column else ""
            self.tree.heading(column.id, text=column.label + suffix)

    def _apply_filter(self) -> None:
        query = self.filter_entry.get().strip()
        if not (self._filtering and self._expand_on_filter):
            self._save_tree_state()
        self._filtering = bool(query)
        self._rebuild(self._filter_root(self._root_node, query))

    def _rebuild(self, displayed_root: NodeT) -> None:
        self.tree.delete(*self.tree.get_children())
        self._populate(displayed_root)
        self._fit_height()
        self._after_rebuild(displayed_root)

    def _populate(self, node: NodeT, parent_iid: str = "") -> None:
        for child in self._children_of(node):
            iid = self._node_iid(child)
            self._insert(parent_iid, child, iid, self._resolve_open(child, iid))
            self._populate(child, iid)

    def _resolve_open(self, node: NodeT, iid: str) -> bool:
        if self._filtering and self._expand_on_filter:
            return self._has_children(node)
        return self._node_states.get(iid, self._default_open(node))

    def _save_tree_state(self, parent_iid: str = "") -> None:
        for child_iid in self.tree.get_children(parent_iid):
            self._node_states[child_iid] = self._is_item_open(child_iid)
            self._save_tree_state(child_iid)

    def _is_item_open(self, iid: str) -> bool:
        return bool(self.getboolean(self.tree.item(iid, "open")))

    # --- Height limit / scrolling ---------------------------------------------------------

    def _on_toggle(self, _event: tk.Event) -> None:
        # The event fires before the item's state changes: measure afterwards.
        self.after_idle(self._fit_height)

    def _fit_height(self) -> None:
        if self._max_rows is None:
            return
        visible = self._count_visible_rows("")
        self.tree.configure(height=max(self._min_rows, min(visible, self._max_rows)))

    def _count_visible_rows(self, parent_iid: str) -> int:
        total = 0
        for iid in self.tree.get_children(parent_iid):
            total += 1
            if self._is_item_open(iid):
                total += self._count_visible_rows(iid)
        return total

    def _on_mousewheel(self, event: tk.Event) -> str | None:
        first, last = self.tree.yview()
        if first <= 0.0 and last >= 1.0:
            return None  # nothing to scroll here: let the page behind it scroll
        if event.num == 4 or event.delta > 0:
            self.tree.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.tree.yview_scroll(1, "units")
        return "break"  # handled: the enclosing scrollable page must not scroll too
