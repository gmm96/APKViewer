"""
Context menu for the Files panel tree. Handles extracting files and
wiring the resulting Open / Open with / Copy / Extract to / Details
commands to their (injected) collaborators, plus strict focus management
for the popup menu itself.

OS integration (actually launching a file / showing a native "Open
with..." picker) and clipboard integration (putting real files on the
clipboard) are intentionally NOT implemented here - they're injected as
`OsFileOpener` and `ClipboardFileCopier` strategies, so this class stays
focused on being a menu.
"""
import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from core.apk_extractor import ApkExtractor
from ui.widgets.file_details_dialog import FileDetailsDialog
from ui.widgets.os_file_opener import OsFileOpener, default_os_file_opener
from utils.clipboard_service import ClipboardFileCopier, default_clipboard_file_copier
from utils.ui_helpers import AssetPathResolver


class FilesContextMenu:
    # Index of the "Open with..." entry within self._menu - needed because
    # the entries are added in this fixed order.
    _OPEN_WITH_INDEX = 1

    def __init__(
        self,
        tree: ttk.Treeview,
        extractor: ApkExtractor,
        get_apk_path_cb,
        size_formatter=None,
        get_meta_cb=None,
        os_file_opener: OsFileOpener = None,
        clipboard_copier: ClipboardFileCopier = None,
        asset_path_resolver: AssetPathResolver = None,
    ):
        self._tree = tree
        self._extractor = extractor
        self._get_apk_path = get_apk_path_cb
        # Optional: () -> dict mapping a tree iid to its raw {"__size__": ...}
        # metadata. Only used to compute real totals for the multi-select
        # Details summary; everything else in this class only ever reads
        # from the treeview's own (already-formatted) values.
        self._get_meta = get_meta_cb
        self._size_formatter = size_formatter

        self._os_file_opener = os_file_opener or default_os_file_opener()
        self._clipboard_copier = clipboard_copier or default_clipboard_file_copier()
        self._asset_path_resolver = asset_path_resolver or AssetPathResolver()

        self._temp_dir = tempfile.TemporaryDirectory(prefix="apkviewer_")

        self._menu = tk.Menu(tree, tearoff=0)

        self._icon_open = self._load_icon("assets/icons/file_open.png")
        self._icon_open_with = self._load_icon("assets/icons/file_open_with.png")
        self._icon_copy = self._load_icon("assets/icons/file_copy.png")
        self._icon_extract = self._load_icon("assets/icons/file_unarchive.png")
        self._icon_info = self._load_icon("assets/icons/file_info.png")

        self._menu.add_command(label="{:<40}".format("  Open"), command=self._cmd_open, image=self._icon_open, compound=tk.LEFT)
        self._menu.add_command(label="{:<40}".format("  Open with..."), command=self._cmd_open_with, image=self._icon_open_with, compound=tk.LEFT)
        self._menu.add_separator()
        self._menu.add_command(label="{:<40}".format("  Copy File"), command=self._cmd_copy, image=self._icon_copy, compound=tk.LEFT)
        self._menu.add_command(label="{:<40}".format("  Extract to..."), command=self._cmd_extract, image=self._icon_extract, compound=tk.LEFT)
        self._menu.add_separator()
        self._menu.add_command(label="{:<40}".format("  Details"), command=self._cmd_details, image=self._icon_info, compound=tk.LEFT)

        self._tree.bind("<Button-3>", self._on_right_click)
        self._tree.bind("<Button-2>", self._on_right_click)

        # 1. Close menu when clicking anywhere else inside the app
        self._tree.winfo_toplevel().bind("<Button-1>", lambda e: self._menu.unpost(), add="+")

        # 2. Close menu when clicking completely outside the app (losing window focus)
        self._menu.bind("<FocusOut>", lambda e: self._menu.unpost())

    def _load_icon(self, relative_path: str, size: tuple = (16, 16), hex_color: str = "#333333", padding_left: int = 8, padding_right: int = 4):
        """Loads, tints, resizes and pads an icon with transparent margin using Pillow."""
        path = self._asset_path_resolver.resolve(relative_path)

        img = Image.open(path).convert("RGBA")

        alpha_mask = img.getchannel("A")
        colored_img = Image.new("RGBA", img.size, color=hex_color)
        colored_img.putalpha(alpha_mask)

        colored_img = colored_img.resize(size, Image.Resampling.LANCZOS)

        canvas_width = padding_left + size[0] + padding_right
        canvas = Image.new("RGBA", (canvas_width, size[1]), (0, 0, 0, 0))
        canvas.paste(colored_img, (padding_left, 0))

        return ImageTk.PhotoImage(canvas)

    def _on_right_click(self, event):
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

    def _cmd_open(self):
        self._menu.unpost()
        paths = self._get_selected_paths()
        if not paths:
            return

        try:
            for target in self._extract_and_resolve(paths):
                self._os_file_opener.open(target)
        except Exception as e:
            messagebox.showerror("Open failed", str(e), parent=self._tree)

    def _cmd_open_with(self):
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

    def _cmd_copy(self):
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

    def _cmd_extract(self):
        self._menu.unpost()
        paths = self._get_selected_paths()
        if not paths:
            return

        dest_dir = filedialog.askdirectory(title="Extract to...", parent=self._tree)
        if not dest_dir:
            return

        try:
            extracted = self._extractor.extract(self._get_apk_path(), paths, dest_dir)
        except Exception as e:
            messagebox.showerror("Extract failed", str(e), parent=self._tree)
            return

        messagebox.showinfo(
            "Extraction Complete",
            f"Successfully extracted {len(extracted)} item(s) to:\n{dest_dir}",
            parent=self._tree,
        )

    def _cmd_details(self):
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

    def _build_summary(self, paths: list) -> dict:
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
