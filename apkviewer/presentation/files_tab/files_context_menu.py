"""
Context menu for the Files panel tree. Handles extracting files and
wiring the resulting Open / Open with / Copy / Extract to / Details
commands to their (injected) collaborators, plus strict focus management
for the popup menu itself.

OS integration (actually launching a file / showing a native "Open
with..." picker) and clipboard integration (putting real files on the
clipboard) are intentionally NOT implemented here - they're injected as
`OsFileOpener` and `ClipboardFileCopier` interfaces, so this class stays
focused on being a menu.
"""

from collections.abc import Callable
import os
import tempfile
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import ImageTk

from apkviewer.domain.interfaces.clipboard_file_copier import ClipboardFileCopier
from apkviewer.domain.interfaces.os_file_opener import OsFileOpener
from apkviewer.domain.interfaces.size_formatter import SizeFormatter
from apkviewer.infrastructure.zip.apk_extractor import ApkExtractor
from apkviewer.presentation.common.extract_to_dialog import ExtractToDialog
from apkviewer.presentation.icons.icon_loader import IconLoader

from .file_details_dialog import FileDetailsDialog


class FilesContextMenu:
    # Index of the "Open with..." entry within self._menu - needed because
    # the entries are added in this fixed order.
    _OPEN_WITH_INDEX = 1

    def __init__(
        self,
        tree: ttk.Treeview,
        extractor: ApkExtractor,
        get_apk_path_cb,
        os_file_opener: OsFileOpener,
        clipboard_copier: ClipboardFileCopier,
        extract_dialog: ExtractToDialog,
        get_default_folder_name: Callable[[], str],
        size_formatter: SizeFormatter | None = None,
        get_meta_cb=None,
        icon_loader: IconLoader | None = None
    ) -> None:
        self._tree: ttk.Treeview = tree
        self._extractor: ApkExtractor = extractor
        self._get_apk_path = get_apk_path_cb
        self._extract_dialog: ExtractToDialog = extract_dialog
        self._get_default_folder_name: Callable[[], str] = get_default_folder_name

        # Optional: () -> dict mapping a tree iid to its raw {"__size__": ...}
        # metadata. Only used to compute real totals for the multi-select
        # Details summary; everything else in this class only ever reads
        # from the treeview's own (already-formatted) values.
        self._get_meta = get_meta_cb
        self._size_formatter: SizeFormatter | None = size_formatter

        self._os_file_opener: OsFileOpener = os_file_opener
        self._clipboard_copier: ClipboardFileCopier = clipboard_copier
        self._icon_loader: IconLoader = icon_loader or IconLoader()

        self._temp_dir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory(prefix="apkviewer_")

        self._menu: tk.Menu = tk.Menu(tree, tearoff=0)

        # Delegate icon loading, tinting, and padding to the injected IconLoader
        self.icon_hex_color: str = "#333333"
        self._icon_open: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/outline/open_file.png",
            hex_color=self.icon_hex_color,
            padding_left=8,
            padding_right=8
        )
        self._icon_open_with: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/outline/open_with_file.png",
            hex_color=self.icon_hex_color,
            padding_left=8,
            padding_right=8
        )
        self._icon_copy: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/outline/copy_file.png",
            hex_color=self.icon_hex_color,
            padding_left=8,
            padding_right=8
        )
        self._icon_extract: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/outline/unarchive_file.png",
            hex_color=self.icon_hex_color,
            padding_left=8,
            padding_right=8
        )
        self._icon_info: ImageTk.PhotoImage = self._icon_loader.load_icon(
            "assets/icons/outline/file_info.png",
            hex_color=self.icon_hex_color,
            padding_left=8,
            padding_right=8
        )

        self._menu.add_command(label="{:<40}".format("Open"), command=self._cmd_open, image=self._icon_open, compound=tk.LEFT)
        self._menu.add_command(label="{:<40}".format("Open with..."), command=self._cmd_open_with, image=self._icon_open_with, compound=tk.LEFT)
        self._menu.add_separator()
        self._menu.add_command(label="{:<40}".format("Copy File"), command=self._cmd_copy, image=self._icon_copy, compound=tk.LEFT)
        self._menu.add_command(label="{:<40}".format("Extract to..."), command=self._cmd_extract, image=self._icon_extract, compound=tk.LEFT)
        self._menu.add_separator()
        self._menu.add_command(label="{:<40}".format("Details"), command=self._cmd_details, image=self._icon_info, compound=tk.LEFT)

        self._tree.bind("<Button-3>", self._on_right_click)
        self._tree.bind("<Button-2>", self._on_right_click)

        # 1. Close menu when clicking anywhere else inside the app
        self._tree.winfo_toplevel().bind("<Button-1>", lambda e: self._menu.unpost(), add="+")

        # 2. Close menu when clicking completely outside the app (losing window focus)
        self._menu.bind("<FocusOut>", lambda e: self._menu.unpost())

    def _on_right_click(self, event) -> None:
        iid = self._tree.identify_row(event.y)
        if iid:
            if iid not in self._tree.selection():
                self._tree.selection_set(iid)

            self._update_menu_state()

            # Unpost any ghost menus first
            self._menu.unpost()

            # Post manually and force focus to enable <FocusOut> detection
            self._menu.post(event.x_root, event.y_root)
            self._menu.focus_set()

    def _get_selected_paths(self) -> list:
        return list(self._tree.selection())

    def _is_folder(self, iid: str) -> bool:
        values = self._tree.item(iid, "values")
        return bool(values) and str(values[0]).startswith("Directory")

    def _update_menu_state(self) -> None:
        # "Open with..." launches an application on a *file*; doing that
        # for a folder isn't a meaningful operation (and behaves oddly with
        # the native OS pickers used below), so disable it whenever the
        # selection includes one.
        paths = self._get_selected_paths()
        any_folder = any(self._is_folder(iid) for iid in paths)
        state = tk.DISABLED if (not paths or any_folder) else tk.NORMAL
        self._menu.entryconfigure(self._OPEN_WITH_INDEX, state=state)

    def reset_workspace(self) -> None:
        """Discards any files previously extracted for Open/Open with/Copy.

        Call this whenever a new APK is loaded: without it, files from a
        *different* APK that happen to share the same internal path (e.g.
        "AndroidManifest.xml") would silently overwrite each other in the
        same temp directory across analyses in one session, and the temp
        directory would otherwise grow without bound for the whole session.
        """
        self._temp_dir.cleanup()
        self._temp_dir = tempfile.TemporaryDirectory(prefix="apkviewer_")

    # --- Menu Commands --------------------------------------------------------

    def _extract_and_resolve(self, paths: list) -> list:
        """Extracts the requested entries and returns the on-disk path for
        each *requested* item (one per selected row) rather than every
        nested file a folder expands into - so Open/Open with/Copy act on
        exactly what the user selected (e.g. the folder itself), instead of
        every file inside it individually."""
        apk_path = self._get_apk_path()
        self._extractor.extract(apk_path, paths, self._temp_dir.name)
        return [os.path.abspath(os.path.join(self._temp_dir.name, *p.split("/"))) for p in paths]

    def _cmd_open(self) -> None:
        self._menu.unpost()
        paths = self._get_selected_paths()
        if not paths:
            return

        try:
            for target in self._extract_and_resolve(paths):
                self._os_file_opener.open(target)
        except Exception as e:
            messagebox.showerror("Open failed", str(e), parent=self._tree)

    def _cmd_open_with(self) -> None:
        self._menu.unpost()
        paths = [p for p in self._get_selected_paths() if not self._is_folder(p)]
        if not paths:
            return

        try:
            targets = self._extract_and_resolve(paths)
        except Exception as e:
            messagebox.showerror("Open with failed", str(e), parent=self._tree)
            return

        # Native "Open With" pickers (SHOpenWithDialog, the XDG portal) act
        # on one file at a time and immediately launch the chosen app, so a
        # multi-file selection shows one picker per file in turn.
        for target in targets:
            try:
                self._os_file_opener.open_with(target)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch OS Open With dialog:\n{e}", parent=self._tree)

    def _cmd_copy(self) -> None:
        self._menu.unpost()
        paths = self._get_selected_paths()
        if not paths:
            return

        try:
            targets = self._extract_and_resolve(paths)
        except Exception as e:
            messagebox.showerror("Copy failed", str(e), parent=self._tree)
            return

        success = self._clipboard_copier.copy(targets)
        if not success:
            clipboard_text = "\n".join(targets)
            self._tree.clipboard_clear()
            self._tree.clipboard_append(clipboard_text)
            messagebox.showwarning(
                "Copy File",
                "Native file copy requires xclip/wl-copy on Linux. Paths have been copied as text instead.",
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

        dialog = FileDetailsDialog(self._tree)
        dialog.show(items_data, summary)

    def _build_summary(self, paths: list) -> dict | None:
        """Real totals (not just a count) for the multi-select Details
        popup - mirrors how file managers show "N items, totaling X" when
        several rows are selected at once."""
        if not self._get_meta or not self._size_formatter:
            return None

        metas = [self._get_meta(iid) for iid in paths]
        metas = [m for m in metas if m]
        if not metas:
            return None

        file_count = sum(1 for m in metas if m.get("__is_file__", False))
        total_size = sum(m.get("__size__", 0) for m in metas)
        total_compressed = sum(m.get("__compressed__", 0) for m in metas)

        return {
            "file_count": file_count,
            "folder_count": len(metas) - file_count,
            "total_size": self._size_formatter.format(total_size),
            "total_compressed": self._size_formatter.format(total_compressed),
        }
