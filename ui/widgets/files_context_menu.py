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

from core.apk_extractor import ApkExtractor
from ui.widgets.clipboard_utils import copy_files_to_clipboard
from ui.widgets.file_details_dialog import FileDetailsDialog


class FilesContextMenu:
    def __init__(self, tree: ttk.Treeview, extractor: ApkExtractor, get_apk_path_cb):
        self._tree = tree
        self._extractor = extractor
        self._get_apk_path = get_apk_path_cb
        
        self._temp_dir = tempfile.TemporaryDirectory(prefix="apkviewer_")

        self._menu = tk.Menu(tree, tearoff=0)
        
        # Padded text to artificially widen the context menu for better UX
        self._menu.add_command(label="{:<40}".format("Open"), command=self._cmd_open)
        self._menu.add_command(label="{:<40}".format("Open with..."), command=self._cmd_open_with)
        self._menu.add_separator()
        self._menu.add_command(label="{:<40}".format("Copy File"), command=self._cmd_copy)
        self._menu.add_command(label="{:<40}".format("Extract to..."), command=self._cmd_extract)
        self._menu.add_separator()
        self._menu.add_command(label="{:<40}".format("Details"), command=self._cmd_details)

        self._tree.bind("<Button-3>", self._on_right_click)
        self._tree.bind("<Button-2>", self._on_right_click)
        
        # 1. Close menu when clicking anywhere else inside the app
        self._tree.winfo_toplevel().bind("<Button-1>", lambda e: self._menu.unpost(), add="+")
        
        # 2. Close menu when clicking completely outside the app (losing window focus)
        self._menu.bind("<FocusOut>", lambda e: self._menu.unpost())

    def _on_right_click(self, event):
        iid = self._tree.identify_row(event.y)
        if iid:
            if iid not in self._tree.selection():
                self._tree.selection_set(iid)
            
            # Unpost any ghost menus first
            self._menu.unpost()
            
            # Post manually and force focus to enable <FocusOut> detection
            self._menu.post(event.x_root, event.y_root)
            self._menu.focus_set()

    def _get_selected_paths(self) -> list:
        return list(self._tree.selection())

    # --- Menu Commands --------------------------------------------------------

    def _cmd_open(self):
        self._menu.unpost()
        paths = self._get_selected_paths()
        if not paths:
            return
            
        extracted = self._extractor.extract(self._get_apk_path(), paths, self._temp_dir.name)
        for p in extracted:
            self._os_open(os.path.abspath(p))

    def _cmd_open_with(self):
        self._menu.unpost()
        paths = self._get_selected_paths()
        if not paths:
            return
            
        extracted = self._extractor.extract(self._get_apk_path(), paths, self._temp_dir.name)
        
        for p in extracted:
            self._os_open_with(os.path.abspath(p))

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
            
        extracted = self._extractor.extract(self._get_apk_path(), paths, self._temp_dir.name)
        abs_paths = [os.path.abspath(p) for p in extracted]
        
        success = copy_files_to_clipboard(abs_paths)
        if not success:
            clipboard_text = "\n".join(abs_paths)
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
            
        extracted = self._extractor.extract(self._get_apk_path(), paths, dest_dir)
        
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

        dialog = FileDetailsDialog(self._tree)
        dialog.show(items_data)

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
