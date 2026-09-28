"""
Actions that export data out of the currently loaded APK (app info as
text, whole APK contents, launcher icon as PNG). They are UI-agnostic
callables: any widget (menu, toolbar, shortcut) can trigger them.
"""

import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox

from PIL import Image

from apkviewer.application import AppInfoSerializer, IconExtractor
from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.presentation.common import ExtractToDialog


class FileMenu:
    _PNG_SAFE_MODES: tuple[str, ...] = ("RGB", "RGBA", "L", "LA", "P")

    def __init__(
        self,
        parent: tk.Misc,
        extract_dialog: ExtractToDialog,
        icon_extractor: IconExtractor,
        info_serializer: AppInfoSerializer,
        get_apk_path: Callable[[], str | None],
        get_result: Callable[[], AnalysisResult | None],
    ) -> None:
        self._parent: tk.Misc = parent
        self._extract_dialog: ExtractToDialog = extract_dialog
        self._icon_extractor: IconExtractor = icon_extractor
        self._report_formatter: AppInfoSerializer = info_serializer
        self._get_apk_path: Callable[[], str | None] = get_apk_path
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
            with open(path, "w", encoding="utf-8") as file:
                file.write(self._report_formatter.format(result.sections))
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc), parent=self._parent)
            return
        self._notify_saved("App info", path)

    def extract_apk(self) -> None:
        apk_path = self._get_apk_path()
        result = self._get_result()
        if apk_path and result is not None:
            self._extract_dialog.run(apk_path, result.package_name)

    def extract_icon(self) -> None:
        result = self._get_result()
        if result is None:
            return

        # Resolve the icon first so the user is not asked for a path we can't fulfil.
        icon = self._icon_extractor.extract_full_resolution(result.apk)
        if icon is None:
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
            self._to_png_compatible(icon).save(path, format="PNG")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Extract icon failed", str(exc), parent=self._parent)
            return
        self._notify_saved("Icon", path)

    # --- Helpers -----------------------------------------------------------
    
    @staticmethod
    def _default_file_name(result: AnalysisResult, extension: str, suffix: str | None = None) -> str:
        return f"{result.package_name}_{suffix}.{extension}" if suffix else f"{result.package_name}.{extension}"

    @classmethod
    def _to_png_compatible(cls, image: Image.Image) -> Image.Image:
        return image if image.mode in cls._PNG_SAFE_MODES else image.convert("RGBA")

    def _notify_saved(self, what: str, path: str) -> None:
        messagebox.showinfo("Saved", f"{what} saved to:\n{path}", parent=self._parent)
