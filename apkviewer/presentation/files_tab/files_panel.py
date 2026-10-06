"""
"Files" tab: hierarchical view of the APK's internal zip entries. It is the
files flavour of BaseTreePanel (which provides the filter, header sorting
and scrolling) plus a right-click context menu for Open / Open with / Copy /
Extract to / Details.
"""

import tkinter as tk
from collections.abc import Callable, Sequence
from datetime import datetime

from PIL import ImageTk

from apkviewer.application.entry_previewer import EntryPreviewer
from apkviewer.application.file_tree_filter import FileTreeFilter
from apkviewer.application.file_tree_sorter import FileSortKey, FileTreeSorter
from apkviewer.domain.entities.file_node import FileNode
from apkviewer.domain.interfaces.size_formatter import SizeFormatter
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.extract_to_dialog import ExtractToDialog
from apkviewer.presentation.common.tree.base_tree_panel import BaseTreePanel
from apkviewer.presentation.common.tree.tree_column import TreeColumn
from apkviewer.presentation.config.theme import FONT_MONO_SMALL
from apkviewer.presentation.formatting.human_readable_size_formatter import HumanReadableSizeFormatter
from apkviewer.presentation.icons.icon_loader import IconLoader

from .files_context_menu import FilesContextMenu

_COLUMNS: tuple[TreeColumn, ...] = (
    TreeColumn("#0", "Name", width=380, min_width=200, stretch=True),
    TreeColumn("type", "Type", width=120, min_width=80),
    TreeColumn("size", "Size", width=100, min_width=70),
    TreeColumn("compressed", "Compressed", width=120, min_width=100),
    TreeColumn("modified", "Modified", width=150, min_width=130),
)
# Tree column id -> the (toolkit-agnostic) key the sorter understands.
_COLUMN_SORT_KEYS: dict[str, FileSortKey] = {
    "#0": FileSortKey.NAME,
    "type": FileSortKey.TYPE,
    "size": FileSortKey.SIZE,
    "compressed": FileSortKey.COMPRESSED,
    "modified": FileSortKey.MODIFIED,
}
_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


class FilesPanel(BaseTreePanel[FileNode]):
    def __init__(
        self,
        parent: tk.Misc,
        get_default_folder_name: Callable[[], str],
        extract_dialog: ExtractToDialog,
        entry_previewer: EntryPreviewer,
        palette: ThemePalette,
        tree_filter: FileTreeFilter | None = None,
        size_formatter: SizeFormatter | None = None,
        sorter: FileTreeSorter | None = None,
        icon_loader: IconLoader | None = None,
    ) -> None:
        # State used by the base-class hooks: it must exist before the base builds the widgets.
        self._tree_filter: FileTreeFilter = tree_filter or FileTreeFilter()
        self._size_formatter: SizeFormatter = size_formatter or HumanReadableSizeFormatter()
        self._sorter: FileTreeSorter = sorter or FileTreeSorter()
        self._icon_loader: IconLoader = icon_loader or IconLoader()
        self._entry_previewer: EntryPreviewer = entry_previewer
        self.apk_path: str | None = None
        self._icon_file: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/color/file.png", padding_left=4, padding_right=8
        )
        self._icon_folder: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/color/directory.png", padding_left=4, padding_right=8
        )
        self._icon_xml: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/color/xml.png", padding_left=4, padding_right=8
        )
        self._icon_image: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/color/image.png", padding_left=4, padding_right=8
        )
        self._icon_rsa: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/color/rsa.png", padding_left=4, padding_right=8
        )




        super().__init__(parent, palette, _COLUMNS)  # fills the available space (no row limit)

        self._context_menu: FilesContextMenu = FilesContextMenu(
            self.tree,
            entry_previewer=entry_previewer,
            extract_dialog=extract_dialog,
            get_apk_path=lambda: self.apk_path,
            get_default_folder_name=get_default_folder_name,
            get_node=self._root_node_find,
            size_formatter=self._size_formatter,
            palette=palette,
            icon_loader=self._icon_loader,
        )

    # --- Public API -------------------------------------------------------

    def render(self, apk_path: str, file_tree: FileNode) -> None:
        self.apk_path = apk_path
        self._entry_previewer.reset()  # a new APK invalidates any previous extraction
        self.show(file_tree)

    def clear(self) -> None:
        self.apk_path = None
        super().clear()

    def apply_palette(self, palette: ThemePalette) -> None:
        super().apply_palette(palette)
        self._context_menu.apply_palette(palette)

    def cleanup(self) -> None:
        """Releases any temporary files extracted for Open/Open with/Copy. Call on app shutdown."""
        self._entry_previewer.dispose()

    def _root_node_find(self, iid: str) -> FileNode | None:
        # Looked up through a method because show()/clear() replace the root node.
        return self._root_node.find(iid)

    # --- BaseTreePanel hooks -------------------------------------------------

    def _empty_root(self) -> FileNode:
        return FileNode.create_root()

    def _filter_root(self, root: FileNode, query: str) -> FileNode:
        return self._tree_filter.filter(root, query)

    def _children_of(self, node: FileNode) -> Sequence[FileNode]:
        return self._sorter.sorted_children(node)

    def _node_iid(self, node: FileNode) -> str:
        return node.path

    def _default_open(self, node: FileNode) -> bool:
        return True

    def _sort_state(self) -> tuple[str, bool]:
        column = next(col for col, key in _COLUMN_SORT_KEYS.items() if key == self._sorter.key)
        return column, self._sorter.reverse

    def _toggle_sort(self, column_id: str) -> None:
        self._sorter.toggle(_COLUMN_SORT_KEYS[column_id])

    def _configure_tags(self, palette: ThemePalette) -> None:
        self.tree.tag_configure("file", font=FONT_MONO_SMALL)
        self.tree.tag_configure("folder", background=palette.folder_bg, font=FONT_MONO_SMALL)

    def _insert(self, parent_iid: str, node: FileNode, iid: str, is_open: bool) -> None:
        size_str = self._size_formatter.format(node.size)
        compressed_str = self._size_formatter.format(node.compressed_size)
        modified_str = self._format_modified(node.modified)

        if node.is_file:
            type_label = f"{node.extension} File" if node.extension else "File"
            self.tree.insert(
                parent_iid, tk.END, iid=iid, text=node.name, image=self._get_icon(node),
                values=(type_label, size_str, compressed_str, modified_str), tags=("file",),
            )
        else:
            self.tree.insert(
                parent_iid, tk.END, iid=iid, text=node.name, image=self._icon_folder,
                values=(f"Directory ({len(node.children)})", size_str, compressed_str, modified_str),
                open=is_open, tags=("folder",),
            )

    def _get_icon(self, node: FileNode) -> ImageTk.PhotoImage:
        match node.extension:
            case "XML":
                return self._icon_xml
            case "PNG" | "JPG" | "JPEG" | "GIF" | "WEBP" | "BMP" | "ICO" | "SVG":
                return self._icon_image
            case "RSA":
                return self._icon_rsa
            case _:
                return self._icon_file

    @staticmethod
    def _format_modified(modified: datetime | None) -> str:
        return modified.strftime(_DATE_FORMAT) if modified is not None else ""
