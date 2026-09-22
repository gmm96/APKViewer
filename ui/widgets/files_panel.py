import os
import tkinter as tk
from tkinter import ttk

from config import COLOR_FOLDER_BG, FONT_MONO_SMALL
from core import FileTreeFilter
from ui.widgets.tree_sorter import FileTreeSorter
from utils.size_formatter import HumanReadableSizeFormatter, SizeFormatter
from utils.ui_helpers import AutoHideScrollbar

_COLUMN_LABELS = {
    "#0": "Name",
    "type": "Type",
    "size": "Size",
    "compressed": "Compressed",
    "modified": "Modified",
}
ARROW_UP = "⏶"
ARROW_DOWN = "⏷"


class FilesPanel(ttk.Frame):
    def __init__(
        self,
        parent,
        tree_filter: FileTreeFilter = None,
        size_formatter: SizeFormatter = None,
        sorter: FileTreeSorter = None,
    ):
        super().__init__(parent)
        self._tree_filter = tree_filter or FileTreeFilter()
        self._size_formatter = size_formatter or HumanReadableSizeFormatter()
        self._sorter = sorter or FileTreeSorter()
        self._tree_data = {}
        
        self._node_states = {}

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)

        self._build_treeview()
        self._build_filter_bar()
        self._update_heading_labels()

    def _build_treeview(self):
        ttk.Style().configure("Treeview.Heading", padding=(8, 6))

        columns = ("type", "size", "compressed", "modified")
        self.tree = ttk.Treeview(self, columns=columns, show="tree headings")

        self.tree.column("#0", width=380, minwidth=200, stretch=True, anchor="w")
        self.tree.column("type", width=120, minwidth=80, stretch=False, anchor="w")
        self.tree.column("size", width=100, minwidth=70, stretch=False, anchor="w")
        self.tree.column("compressed", width=120, minwidth=100, stretch=False, anchor="w")
        self.tree.column("modified", width=150, minwidth=130, stretch=False, anchor="w")

        for column in _COLUMN_LABELS:
            self.tree.heading(column, anchor="w", command=lambda c=column: self._sort_by(c))

        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        autohide = AutoHideScrollbar(h_scroll, {"row": 1, "column": 0, "sticky": "ew"})
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=autohide.scroll_command)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("folder", background=COLOR_FOLDER_BG, font=FONT_MONO_SMALL)
        self.tree.tag_configure("file", font=FONT_MONO_SMALL)

    def _build_filter_bar(self):
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)

        self.filter_entry = ttk.Entry(filter_frame)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

    # --- Public API -------------------------------------------------------

    def set_tree(self, tree_data: dict):
        self._tree_data = tree_data
        self._node_states.clear()
        self.filter_entry.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self._populate(self._tree_data)

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self._tree_data = {}
        self._node_states.clear()

    # --- Sorting ---------------------------------------------------------

    def _sort_by(self, column: str):
        self._sorter.toggle(column)
        self._update_heading_labels()
        self._apply_filter()

    def _update_heading_labels(self):
        arrow = f"  {ARROW_UP}" if self._sorter.reverse else f"  {ARROW_DOWN}"
        for column, label in _COLUMN_LABELS.items():
            text = label + (arrow if column == self._sorter.column else "")
            self.tree.heading(column, text=text)

    # --- Filtering / rendering ----------------------------------------------

    def _save_tree_state(self, parent_iid=""):
        for child_iid in self.tree.get_children(parent_iid):
            self._node_states[child_iid] = self.tree.item(child_iid, "open")
            self._save_tree_state(child_iid)

    def _apply_filter(self):
        query = self.filter_entry.get()
        self._save_tree_state()
        self.tree.delete(*self.tree.get_children())
        self._populate(self._tree_filter.filter(self._tree_data, query))

    def _populate(self, node_dict: dict, parent_iid: str = ""):
        entries = self._sorter.sorted_entries(node_dict)

        for name, meta in entries:
            iid = f"{parent_iid}/{name}" if parent_iid else name
            
            size_str = self._size_formatter.format(meta.get("__size__", 0))
            compressed_str = self._size_formatter.format(meta.get("__compressed__", 0))
            modified_str = meta.get("__modified__", "")

            if meta.get("__is_file__", False):
                ext = os.path.splitext(name)[1].lstrip(".").upper()
                type_label = f"{ext} File" if ext else "File"
                self.tree.insert(
                    parent_iid, tk.END, iid=iid, text=f" \U0001F4C4 {name}",
                    values=(type_label, size_str, compressed_str, modified_str),
                    tags=("file",),
                )
            else:
                child_count = len(meta.get("__children__", {}))
                is_open = self._node_states.get(iid, True)
                self.tree.insert(
                    parent_iid,
                    tk.END,
                    iid=iid,
                    text=f" \U0001F4C1 {name}",
                    values=(f"Directory ({child_count})", size_str, compressed_str, modified_str),
                    open=is_open,
                    tags=("folder",),
                )
                self._populate(meta.get("__children__", {}), iid)
