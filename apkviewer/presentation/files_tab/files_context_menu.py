"""
Context menu for the Files panel tree. It only translates menu clicks
into calls on the injected collaborators (the EntryPreviewer use case and
the "Extract to..." dialog) and manages focus for the popup menu itself.

Launching files, the native "Open with..." picker and the file clipboard
are NOT implemented here: they are reached through the EntryPreviewer
use case, so this class stays focused on being a menu.
"""

import os
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from PIL import ImageTk

from apkviewer.application.entry_previewer import EntryPreviewer
from apkviewer.domain.entities.file_node import FileNode
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.appearance.tk_widget_styler import TkWidgetStyler
from apkviewer.presentation.common.extract_to_dialog import ExtractToDialog
from apkviewer.presentation.common.popup_menu_controller import PopupMenuController
from apkviewer.domain.interfaces.size_formatter import SizeFormatter
from apkviewer.presentation.icons.icon_loader import IconLoader

from .file_details_dialog import FileDetailsDialog


class FilesContextMenu:
    # Index of the "Open with..." entry within self._menu - needed because
    # the entries are added in this fixed order.
    _OPEN_WITH_INDEX: int = 1

    def __init__(
        self,
        tree: ttk.Treeview,
        entry_previewer: EntryPreviewer,
        extract_dialog: ExtractToDialog,
        get_apk_path: Callable[[], str | None],
        get_default_folder_name: Callable[[], str],
        get_node: Callable[[str], FileNode | None],
        size_formatter: SizeFormatter,
        palette: ThemePalette,
        icon_loader: IconLoader | None = None,
    ) -> None:
        self._tree: ttk.Treeview = tree
        self._entry_previewer: EntryPreviewer = entry_previewer
        self._extract_dialog: ExtractToDialog = extract_dialog
        self._get_apk_path: Callable[[], str | None] = get_apk_path
        self._get_default_folder_name: Callable[[], str] = get_default_folder_name
        self._get_node: Callable[[str], FileNode | None] = get_node
        self._size_formatter: SizeFormatter = size_formatter
        self._palette: ThemePalette = palette
        self._icon_loader: IconLoader = icon_loader or IconLoader()

        self._menu: tk.Menu = tk.Menu(tree, tearoff=0)
        self._icons: list[ImageTk.PhotoImage] = []  # keep references so Tk doesn't drop them
        self._entry_icon_files: list[tuple[int, str]] = []  # (menu index, icon file)

        self._add_entry("Open", self._cmd_open, "open_file.png")
        self._add_entry("Open with...", self._cmd_open_with, "open_with_file.png")
        self._menu.add_separator()
        self._add_entry("Copy File", self._cmd_copy, "copy_file.png")
        self._add_entry("Extract to...", self._cmd_extract, "unarchive_file.png")
        self._menu.add_separator()
        self._add_entry("Details", self._cmd_details, "file_info.png")

        # Closing on outside clicks / focus loss / Escape is shared with every other popup.
        self._popup: PopupMenuController = PopupMenuController(tree, self._menu)
        TkWidgetStyler.style_menu(self._menu, palette)

        self._tree.bind("<Button-3>", self._on_right_click)
        self._tree.bind("<Button-2>", self._on_right_click)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        TkWidgetStyler.style_menu(self._menu, palette)
        self._icons.clear()
        for index, icon_file in self._entry_icon_files:
            self._menu.entryconfigure(index, image=self._load_icon(icon_file))

    def _load_icon(self, icon_file: str) -> ImageTk.PhotoImage:
        icon = self._icon_loader.load_icon(
            f"assets/icons/outline/{icon_file}",
            hex_color=self._palette.icon_tint,
            padding_left=8,
            padding_right=8,
        )
        self._icons.append(icon)
        return icon

    def _add_entry(self, label: str, command: Callable[[], None], icon_file: str) -> None:
        icon = self._load_icon(icon_file)
        self._menu.add_command(label=f"{label:<40}", command=command, image=icon, compound=tk.LEFT)
        index = self._menu.index(tk.END)
        self._entry_icon_files.append((index if index is not None else 0, icon_file))

    def _on_right_click(self, event) -> None:
        iid = self._tree.identify_row(event.y)
        if iid:
            if iid not in self._tree.selection():
                self._tree.selection_set(iid)

            self._update_menu_state()
            self._popup.post(event.x_root, event.y_root)

    def _get_selected_paths(self) -> list[str]:
        return list(self._tree.selection())

    def _is_folder(self, iid: str) -> bool:
        node = self._get_node(iid)
        return node is not None and not node.is_file

    def _update_menu_state(self) -> None:
        # "Open with..." launches an application on a *file*; doing that
        # for a folder isn't a meaningful operation (and behaves oddly with
        # the native OS pickers), so disable it whenever the selection
        # includes one.
        paths = self._get_selected_paths()
        any_folder = any(self._is_folder(iid) for iid in paths)
        state = tk.DISABLED if (not paths or any_folder) else tk.NORMAL
        self._menu.entryconfigure(self._OPEN_WITH_INDEX, state=state)

    # --- Menu Commands --------------------------------------------------------

    def _prepare(self, paths: list[str], error_title: str) -> list[str] | None:
        """Extract the entries into the workspace; None (after telling the user) on failure."""
        apk_path = self._get_apk_path()
        if not paths or not apk_path:
            return None
        try:
            return self._entry_previewer.prepare(apk_path, paths)
        except Exception as exc:
            messagebox.showerror(error_title, str(exc), parent=self._tree)
            return None

    def _cmd_open(self) -> None:
        self._menu.unpost()
        targets = self._prepare(self._get_selected_paths(), "Open failed")
        if targets is None:
            return

        try:
            for target in targets:
                self._entry_previewer.open(target)
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc), parent=self._tree)

    def _cmd_open_with(self) -> None:
        self._menu.unpost()
        files_only = [p for p in self._get_selected_paths() if not self._is_folder(p)]
        targets = self._prepare(files_only, "Open with failed")
        if targets is None:
            return

        # Native "Open With" pickers act on one file at a time and
        # immediately launch the chosen app, so a multi-file selection
        # shows one picker per file in turn.
        for target in targets:
            try:
                self._entry_previewer.open_with(target)
            except Exception as exc:
                messagebox.showerror(
                    "Error", f"Failed to launch OS Open With dialog:\n{exc}",
                    parent=self._tree
                )

    def _cmd_copy(self) -> None:
        self._menu.unpost()
        targets = self._prepare(self._get_selected_paths(), "Copy failed")
        if targets is None:
            return

        if not self._entry_previewer.copy_to_clipboard(targets):
            self._tree.clipboard_clear()
            self._tree.clipboard_append("\n".join(targets))
            messagebox.showwarning(
                "Copy File",
                "Copying files to the clipboard is not available on this system. "
                "Their paths have been copied as text instead.",
                parent=self._tree,
            )

    def _cmd_extract(self) -> None:
        self._menu.unpost()
        paths = self._get_selected_paths()
        apk_path = self._get_apk_path()
        if not paths or not apk_path:
            return
        self._extract_dialog.run(apk_path, self._get_default_folder_name(), paths)

    def _cmd_details(self) -> None:
        self._menu.unpost()
        paths = self._get_selected_paths()
        if not paths:
            return

        items_data = []
        for iid in paths:
            values = self._tree.item(iid, "values")
            items_data.append({
                "name": os.path.basename(iid) or iid,
                "type": values[0] if len(values) > 0 else "Unknown",
                "size": values[1] if len(values) > 1 else "-",
                "compressed": values[2] if len(values) > 2 else "-",
                "modified": values[3] if len(values) > 3 else "-",
            })

        summary = self._build_summary(paths) if len(paths) > 1 else None
        FileDetailsDialog(self._tree).show(items_data, summary)

    def _build_summary(self, paths: list[str]) -> dict | None:
        """Real totals (not just a count) for the multi-select Details
        popup - mirrors how file managers show "N items, totaling X"."""
        nodes = [node for node in (self._get_node(iid) for iid in paths) if node is not None]
        if not nodes:
            return None

        file_count = sum(1 for node in nodes if node.is_file)
        return {
            "file_count": file_count,
            "folder_count": len(nodes) - file_count,
            "total_size": self._size_formatter.format(sum(node.size for node in nodes)),
            "total_compressed": self._size_formatter.format(
                sum(node.compressed_size for node in nodes)
            ),
        }
