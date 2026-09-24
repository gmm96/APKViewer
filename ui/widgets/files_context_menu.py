"""
Context menu for the Files panel tree. Handles extracting files, native OS 
integrations (Open With, Clipboard), and strict focus management.
"""
import asyncio
import os
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from core.apk_extractor import ApkExtractor
from ui.widgets.clipboard_utils import copy_files_to_clipboard
from ui.widgets.file_details_dialog import FileDetailsDialog
from utils.ui_helpers import get_asset_path


class FilesContextMenu:
    # Index of the "Open with..." entry within self._menu - needed because
    # the entries are added in this fixed order.
    _OPEN_WITH_INDEX = 1

    def __init__(self, tree: ttk.Treeview, extractor: ApkExtractor, get_apk_path_cb, size_formatter=None, get_meta_cb=None):
        self._tree = tree
        self._extractor = extractor
        self._get_apk_path = get_apk_path_cb
        # Optional: () -> dict mapping a tree iid to its raw {"__size__": ...}
        # metadata. Only used to compute real totals for the multi-select
        # Details summary; everything else in this class only ever reads
        # from the treeview's own (already-formatted) values.
        self._get_meta = get_meta_cb
        self._size_formatter = size_formatter

        self._temp_dir = tempfile.TemporaryDirectory(prefix="apkviewer_")

        self._menu = tk.Menu(tree, tearoff=0)
        
        # Carga, coloreo, redimensión y padding de los iconos al vuelo
        self._icon_open = self._load_icon("assets/icons/file_open.png")
        self._icon_open_with = self._load_icon("assets/icons/file_open_with.png")
        self._icon_copy = self._load_icon("assets/icons/file_copy.png")
        self._icon_extract = self._load_icon("assets/icons/file_unarchive.png")
        self._icon_info = self._load_icon("assets/icons/file_info.png")

        # Restauramos el {:<40} para ensanchar el menú artificialmente
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
        """Carga, colorea, redimensiona y añade padding transparente al icono usando Pillow."""
        path = get_asset_path(relative_path)
        
        # 1. Abrir asegurando que tenga canal de transparencia (RGBA)
        img = Image.open(path).convert("RGBA")
        
        # 2. Colorear el icono
        alpha_mask = img.getchannel('A')
        colored_img = Image.new("RGBA", img.size, color=hex_color)
        colored_img.putalpha(alpha_mask)
        
        # 3. Redimensionar
        colored_img = colored_img.resize(size, Image.Resampling.LANCZOS)
        
        # 4. TRUCO DE PADDING: Crear un lienzo transparente más ancho
        canvas_width = padding_left + size[0] + padding_right
        canvas = Image.new("RGBA", (canvas_width, size[1]), (0, 0, 0, 0))
        
        # 5. Pegar el icono desplazado hacia la derecha (creando el padding izquierdo)
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
                self._os_open(target)
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
            self._os_open_with(target)

    def _os_open_with(self, abs_path: str):
        try:
            if sys.platform == "win32":
                self._open_with_windows(abs_path)
            elif sys.platform.startswith("linux"):
                self._open_with_linux_portal(abs_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", abs_path])
            else:
                raise RuntimeError(
                    f"Open With is not supported on platform: {sys.platform}"
                )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to launch OS Open With dialog:\n{e}",
                parent=self._tree
            )

    def _open_with_windows(self, abs_path: str):
        import ctypes
        from ctypes import wintypes

        class OPENASINFO(ctypes.Structure):
            _fields_ = [
                ("pcszFile", wintypes.LPCWSTR),
                ("pcszClass", wintypes.LPCWSTR),
                ("oaifInFlags", wintypes.DWORD),
            ]

        OAIF_EXEC = 0x00000004
        OAIF_HIDE_REGISTRATION = 0x00000020

        info = OPENASINFO(
            abs_path,
            None,
            OAIF_EXEC | OAIF_HIDE_REGISTRATION,
        )

        shell32 = ctypes.WinDLL("shell32", use_last_error=True)

        shell32.SHOpenWithDialog.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(OPENASINFO),
        ]
        shell32.SHOpenWithDialog.restype = wintypes.HRESULT

        hr = shell32.SHOpenWithDialog(
            None,
            ctypes.byref(info),
        )

        if hr != 0:
            raise OSError(
                f"SHOpenWithDialog failed with HRESULT 0x{hr & 0xffffffff:08X}"
            )

    def _open_with_linux_portal(self, abs_path: str):
        asyncio.run(self._open_with_linux_portal_async(abs_path))

    async def _open_with_linux_portal_async(self, abs_path: str):
        try:
            from dbus_next import Message, MessageType, Variant
            from dbus_next.aio import MessageBus
        except ImportError as e:
            raise RuntimeError(
                "The Python package 'dbus-next' is required for "
                "Open With on Linux."
            ) from e

        fd = os.open(abs_path, os.O_RDONLY)

        try:
            bus = await MessageBus(
                negotiate_unix_fd=True
            ).connect()

            try:
                message = Message(
                    destination="org.freedesktop.portal.Desktop",
                    path="/org/freedesktop/portal/desktop",
                    interface="org.freedesktop.portal.OpenURI",
                    member="OpenFile",
                    signature="sha{sv}",
                    body=[
                        "",
                        0,
                        {
                            "ask": Variant("b", True),
                        },
                    ],
                    unix_fds=[fd],
                )

                reply = await bus.call(message)

                if reply.message_type == MessageType.ERROR:
                    raise RuntimeError(
                        f"{reply.error_name}: "
                        f"{reply.body[0] if reply.body else ''}"
                    )

                if reply.message_type != MessageType.METHOD_RETURN:
                    raise RuntimeError(
                        f"Unexpected D-Bus reply type: "
                        f"{reply.message_type}"
                    )
            finally:
                bus.disconnect()
        finally:
            os.close(fd)

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

        success = copy_files_to_clipboard(targets)
        if not success:
            clipboard_text = "\n".join(targets)
            self._tree.clipboard_clear()
            self._tree.clipboard_append(clipboard_text)
            messagebox.showwarning(
                "Copy File", 
                "Native file copy requires xclip/wl-copy on Linux. Paths have been copied as text instead.", 
                parent=self._tree
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
            parent=self._tree
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

    # --- OS Integration -------------------------------------------------------

    @staticmethod
    def _os_open(path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print(f"Failed to open {path}: {e}")
