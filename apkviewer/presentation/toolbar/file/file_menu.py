"""
Actions that export data out of the currently loaded APK (app info as
text, whole APK contents, launcher icon as PNG). They are UI-agnostic
callables: any widget (menu, toolbar, shortcut) can trigger them.
"""

import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox

from apkviewer.application.export_app_info import ExportAppInfo
from apkviewer.application.export_icon import ExportIcon
from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.presentation.common.extract_to_dialog import ExtractToDialog


class FileMenu:
    def __init__(
        self,
        parent: tk.Misc,
        extract_dialog: ExtractToDialog,
        export_app_info: ExportAppInfo,
        export_icon: ExportIcon,
        get_result: Callable[[], AnalysisResult | None],
    ) -> None:
        self._parent: tk.Misc = parent
        self._extract_dialog: ExtractToDialog = extract_dialog
        self._export_app_info: ExportAppInfo = export_app_info
        self._export_icon: ExportIcon = export_icon
        self._get_result: Callable[[], AnalysisResult | None] = get_result

    def export_app_info(self) -> None:
        result = self._get_result()
        if result is None:
            return

        path = filedialog.asksaveasfilename(
            parent=self._parent,
            title="Export app info",
            defaultextension=".txt",
            initialfile=self._default_file_name(result, "txt", "report"),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            self._export_app_info.execute(result, path)
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc), parent=self._parent)
            return
        self._notify_saved("App info", path)

    def extract_apk(self) -> None:
        result = self._get_result()
        if result is not None:
            self._extract_dialog.run(result.apk_path, result.default_name)

    def extract_icon(self) -> None:
        result = self._get_result()
        if result is None:
            return

        # Check the icon first so the user is not asked for a path we can't fulfil.
        if result.icon_png is None:
            messagebox.showwarning(
                "Extract icon",
                "No raster icon (PNG/WebP/JPG) could be found in this APK.",
                parent=self._parent,
            )
            return

        path = filedialog.asksaveasfilename(
            parent=self._parent,
            title="Extract icon as PNG",
            defaultextension=".png",
            initialfile=self._default_file_name(result, "png"),
            filetypes=[("PNG images", "*.png")],
        )
        if not path:
            return

        try:
            self._export_icon.execute(result, path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Extract icon failed", str(exc), parent=self._parent)
            return
        self._notify_saved("Icon", path)

    # --- Helpers -----------------------------------------------------------

    @staticmethod
    def _default_file_name(
        result: AnalysisResult,
        extension: str,
        suffix: str | None = None
    ) -> str:
        stem = f"{result.default_name}_{suffix}" if suffix else result.default_name
        return f"{stem}.{extension}"

    def _notify_saved(self, what: str, path: str) -> None:
        messagebox.showinfo("Saved", f"{what} saved to:\n{path}", parent=self._parent)
