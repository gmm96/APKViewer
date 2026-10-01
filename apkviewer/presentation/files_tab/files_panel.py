"""
"Files" tab: hierarchical view of the APK's internal zip entries, with a
live text filter, column-header sorting, and a right-click context menu
for Open / Open with / Copy / Extract to / Details.
"""

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from functools import partial
from tkinter import ttk

from PIL import ImageTk

from apkviewer.application.entry_previewer import EntryPreviewer
from apkviewer.application.file_tree_filter import FileTreeFilter
from apkviewer.application.file_tree_sorter import FileSortKey, FileTreeSorter
from apkviewer.domain.entities.file_node import FileNode
from apkviewer.presentation.common.auto_hide_scrollbar import AutoHideScrollbar
from apkviewer.presentation.common.extract_to_dialog import ExtractToDialog
from apkviewer.presentation.config.theme import COLOR_FOLDER_BG, FONT_MONO_SMALL
from apkviewer.presentation.formatting.human_readable_size_formatter import HumanReadableSizeFormatter
from apkviewer.domain.interfaces.size_formatter import SizeFormatter
from apkviewer.presentation.icons.icon_loader import IconLoader

from .files_context_menu import FilesContextMenu


# Tk column identifier -> label shown in its heading.
_COLUMN_LABELS: dict[str, str] = {
    "#0": "Name",
    "type": "Type",
    "size": "Size",
    "compressed": "Compressed",
    "modified": "Modified",
}
# Tk column identifier -> the (toolkit-agnostic) key the sorter understands.
_COLUMN_SORT_KEYS: dict[str, FileSortKey] = {
    "#0": FileSortKey.NAME,
    "type": FileSortKey.TYPE,
    "size": FileSortKey.SIZE,
    "compressed": FileSortKey.COMPRESSED,
    "modified": FileSortKey.MODIFIED,
}
ARROW_UP: str = "⏶"
ARROW_DOWN: str = "⏷"
_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


class FilesPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Notebook,
        get_default_folder_name: Callable[[], str],
        extract_dialog: ExtractToDialog,
        entry_previewer: EntryPreviewer,
        tree_filter: FileTreeFilter | None = None,
        size_formatter: SizeFormatter | None = None,
        sorter: FileTreeSorter | None = None,
        icon_loader: IconLoader | None = None,
    ) -> None:
        super().__init__(parent)
        self._tree_filter: FileTreeFilter = tree_filter or FileTreeFilter()
        self._size_formatter: SizeFormatter = size_formatter or HumanReadableSizeFormatter()
        self._sorter: FileTreeSorter = sorter or FileTreeSorter()
        self._icon_loader: IconLoader = icon_loader or IconLoader()
        self._entry_previewer: EntryPreviewer = entry_previewer

        self._root_node: FileNode = FileNode.create_root()
        self._node_states: dict[str, bool] = {}
        self.apk_path: str | None = None

        self._icon_file: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/color/file.png",
            padding_left=4,
            padding_right=8
        )
        self._icon_folder: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/color/directory.png",
            padding_left=4,
            padding_right=8
        )

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)

        self._build_treeview()
        self._build_filter_bar()
        self._update_heading_labels()

        self._context_menu: FilesContextMenu = FilesContextMenu(
            self.tree,
            entry_previewer=entry_previewer,
            extract_dialog=extract_dialog,
            get_apk_path=lambda: self.apk_path,
            get_default_folder_name=get_default_folder_name,
            get_node=self._root_node_find,
            size_formatter=self._size_formatter,
            icon_loader=self._icon_loader,
        )

    def _build_treeview(self) -> None:
        ttk.Style().configure("Treeview.Heading", padding=(8, 6))
        columns = ("type", "size", "compressed", "modified")
        self.tree: ttk.Treeview = ttk.Treeview(self, columns=columns, show="tree headings")
        self.tree.column("#0", width=380, minwidth=200, stretch=True, anchor="w")
        self.tree.column("type", width=120, minwidth=80, stretch=False, anchor="w")
        self.tree.column("size", width=100, minwidth=70, stretch=False, anchor="w")
        self.tree.column("compressed", width=120, minwidth=100, stretch=False, anchor="w")
        self.tree.column("modified", width=150, minwidth=130, stretch=False, anchor="w")

        for column in _COLUMN_LABELS:
            self.tree.heading(column, anchor="w", command=partial(self._sort_by, column))

        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        autohide = AutoHideScrollbar(h_scroll, {"row": 1, "column": 0, "sticky": "ew"})
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=autohide.scroll_command)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.tag_configure("folder", background=COLOR_FOLDER_BG, font=FONT_MONO_SMALL)
        self.tree.tag_configure("file", font=FONT_MONO_SMALL)

    def _build_filter_bar(self) -> None:
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_entry: ttk.Entry = ttk.Entry(filter_frame)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

    # --- Public API -------------------------------------------------------

    def render(self, apk_path: str, file_tree: FileNode) -> None:
        self.apk_path = apk_path
        self._root_node = file_tree
        self._node_states.clear()
        self._entry_previewer.reset()  # a new APK invalidates any previous extraction
        self.filter_entry.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self._populate(self._root_node)

    def clear(self) -> None:
        self.apk_path = None
        self.tree.delete(*self.tree.get_children())
        self._root_node = FileNode.create_root()
        self._node_states.clear()

    def cleanup(self) -> None:
        """Releases any temporary files extracted for Open/Open with/Copy. Call on app shutdown."""
        self._entry_previewer.dispose()

    def _root_node_find(self, iid: str) -> FileNode | None:
        # Looked up through a method (not a bound `self._root_node.find`)
        # because render()/clear() replace the root node.
        return self._root_node.find(iid)

    # --- Sorting ---------------------------------------------------------

    def _sort_by(self, column: str) -> None:
        self._sorter.toggle(_COLUMN_SORT_KEYS[column])
        self._update_heading_labels()
        self._apply_filter()

    def _update_heading_labels(self) -> None:
        arrow = f"  {ARROW_UP}" if self._sorter.reverse else f"  {ARROW_DOWN}"
        for column, label in _COLUMN_LABELS.items():
            is_sorted = _COLUMN_SORT_KEYS[column] == self._sorter.key
            self.tree.heading(column, text=label + (arrow if is_sorted else ""))

    # --- Filtering / rendering ----------------------------------------------

    def _save_tree_state(self, parent_iid: str = "") -> None:
        for child_iid in self.tree.get_children(parent_iid):
            self._node_states[child_iid] = self.tree.item(child_iid, "open")
            self._save_tree_state(child_iid)

    def _apply_filter(self) -> None:
        query = self.filter_entry.get()
        self._save_tree_state()
        self.tree.delete(*self.tree.get_children())
        self._populate(self._tree_filter.filter(self._root_node, query))

    def _populate(self, node: FileNode, parent_iid: str = "") -> None:
        for child in self._sorter.sorted_children(node):
            size_str = self._size_formatter.format(child.size)
            compressed_str = self._size_formatter.format(child.compressed_size)
            modified_str = self._format_modified(child.modified)

            if child.is_file:
                type_label = f"{child.extension} File" if child.extension else "File"
                self.tree.insert(
                    parent_iid,
                    tk.END,
                    iid=child.path,
                    text=child.name,
                    image=self._icon_file,
                    values=(
                        type_label,
                        size_str,
                        compressed_str,
                        modified_str
                    ),
                    tags=("file",),
                )
            else:
                self.tree.insert(
                    parent_iid,
                    tk.END,
                    iid=child.path,
                    text=child.name,
                    image=self._icon_folder,
                    values=(
                        f"Directory ({len(child.children)})",
                        size_str,
                        compressed_str,
                        modified_str
                    ),
                    open=self._node_states.get(child.path, True),
                    tags=("folder",),
                )
                self._populate(child, child.path)

    @staticmethod
    def _format_modified(modified: datetime | None) -> str:
        return modified.strftime(_DATE_FORMAT) if modified is not None else ""
