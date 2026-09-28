"""
"Extract to..." flow shared by the Files tab context menu (selected
entries) and the File menu (whole APK).

It shows the system "save as" dialog pre-filled with a default folder
name. Whatever name the user confirms is created as a folder inside the
chosen location, and the extracted files are written into it.
"""

import os
import tkinter as tk
from collections.abc import Sequence
from tkinter import filedialog, messagebox

from apkviewer.infrastructure import ApkExtractor


class ExtractToDialog:
    def __init__(self, parent: tk.Misc, extractor: ApkExtractor) -> None:
        self._parent: tk.Misc = parent
        self._extractor: ApkExtractor = extractor

    def run(
        self,
        apk_path: str,
        default_folder_name: str,
        internal_paths: Sequence[str] | None = None,
    ) -> None:
        """
        Extract `internal_paths` (or the whole APK when None) into a new
        folder whose name and location are chosen by the user.
        """
        dest_dir = self._ask_destination(default_folder_name)
        if not dest_dir:
            return

        try:
            os.makedirs(dest_dir, exist_ok=True)
            if internal_paths is None:
                extracted = self._extractor.extract_all(apk_path, dest_dir)
            else:
                extracted = self._extractor.extract(apk_path, list(internal_paths), dest_dir)
        except Exception as exc:
            messagebox.showerror("Extract failed", str(exc), parent=self._parent)
            return

        messagebox.showinfo(
            "Extraction Complete",
            f"Successfully extracted {len(extracted)} item(s) to:\n{dest_dir}",
            parent=self._parent,
        )

    def _ask_destination(self, default_folder_name: str) -> str:
        # confirmoverwrite=False: the chosen name is a folder, so the
        # "file already exists, replace it?" prompt would be misleading.
        return filedialog.asksaveasfilename(
            parent=self._parent,
            title="Extract to...",
            initialfile=default_folder_name,
            confirmoverwrite=False,
        )
