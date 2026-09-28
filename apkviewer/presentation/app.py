"""
Main application window: wires together the header, status bar, tabs and
the background analysis pipeline. This is the composition root for the
whole UI - every non-trivial dependency is created (or accepted) here and
handed down to the collaborators that need it.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from apkviewer.application import (
    AppInfoSerializer,
    ApkAnalyzer,
    FileTreeBuilder,
    IconExtractor,
    ManifestFormatter,
)
from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.domain.interfaces import PlatformServices
from apkviewer.infrastructure import ApkExtractor, PlatformServicesResolver
from apkviewer.presentation.toolbar.help import HelpMenu
from apkviewer.presentation.toolbar.file import FileMenu
from apkviewer.presentation.common import ExtractToDialog, StatusBar, TextContextMenu, TkWindowHandleProvider
from apkviewer.presentation.files_tab import FilesPanel
from apkviewer.presentation.header import AppHeader
from apkviewer.presentation.icons import IconLoader
from apkviewer.presentation.info_tab import InfoPanel
from apkviewer.presentation.intent import IntentDetailsDialog
from apkviewer.presentation.manifest_tab import ManifestPanel
from apkviewer.presentation.toolbar import AppToolbar
from apkviewer.presentation.viewmodels import AppToolbarItem

_ICONS_DIR = "assets/icons/outline"


class ApkAnalyzerApp:
    # Menu items that only make sense once an APK has been analyzed.
    _ANALYSIS_DEPENDENT_ITEMS: tuple[str, ...] = ("export_app_info", "extract_apk", "extract_icon")

    def __init__(
        self,
        root: tk.Tk,
        analyzer: ApkAnalyzer | None = None,
        manifest_formatter: ManifestFormatter | None = None,
        file_tree_builder: FileTreeBuilder | None = None,
        icon_loader: IconLoader | None = None,
        icon_extractor: IconExtractor | None = None,
        info_serializer: AppInfoSerializer | None = None,
        file_menu: FileMenu | None = None,
        help_menu: HelpMenu | None = None,
        platform_services: PlatformServices | None = None,
    ) -> None:
        self.root: tk.Tk = root
        self.root.title("APKViewer")
        self.root.geometry("1000x750")
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self._platform_services: PlatformServices = platform_services or PlatformServicesResolver().resolve(
            TkWindowHandleProvider(root)
        )
        self._icon_extractor: IconExtractor = icon_extractor or IconExtractor()
        self._analyzer: ApkAnalyzer = analyzer or ApkAnalyzer(icon_extractor=self._icon_extractor)
        self._manifest_formatter: ManifestFormatter = manifest_formatter or ManifestFormatter()
        self._file_tree_builder: FileTreeBuilder = file_tree_builder or FileTreeBuilder()
        self._icon_loader: IconLoader = icon_loader or IconLoader()

        # State of the APK currently shown (None while nothing is loaded).
        self._apk_path: str | None = None
        self._result: AnalysisResult | None = None

        self._export_actions: FileMenu = file_menu or FileMenu(
            parent=root,
            extract_dialog=ExtractToDialog(root, ApkExtractor()),
            icon_extractor=self._icon_extractor,
            info_serializer=info_serializer or AppInfoSerializer(),
            get_apk_path=lambda: self._apk_path,
            get_result=lambda: self._result,
        )
        self._help_actions: HelpMenu = help_menu or HelpMenu(
            root,
            url_opener=self._platform_services.create_url_opener(),
        )

        self._configure_style()
        self.context_menu: TextContextMenu = TextContextMenu(root)
        self.intent_dialog: IntentDetailsDialog = IntentDetailsDialog(root)
        self._build_layout()
        self._build_menu()

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=(20, 2))
        style.map("TNotebook.Tab", padding=[("selected", (20, 3))])

    def _build_layout(self) -> None:
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
        self.header: AppHeader = AppHeader(top_frame, on_load_click=self.load_apk)
        self.header.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.status_bar: StatusBar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))
        self.info_panel: InfoPanel = InfoPanel(
            notebook,
            self.context_menu,
            on_intent_double_click=self.intent_dialog.open
        )
        notebook.add(self.info_panel, text="Information")
        self.manifest_panel: ManifestPanel = ManifestPanel(notebook, self.context_menu)
        notebook.add(self.manifest_panel, text="Manifest")
        self.files_panel: FilesPanel = FilesPanel(
            notebook,
            icon_loader=self._icon_loader,
            platform_services=self._platform_services,
            get_default_folder_name=self._default_extract_folder_name,
        )
        notebook.add(self.files_panel, text="Files")

    def _build_menu(self) -> None:
        export, help_ = self._export_actions, self._help_actions
        self.menu_bar: AppToolbar = AppToolbar(
            self.root,
            {
                "File": [
                    AppToolbarItem("load_apk", "Load APK", self.load_apk, f"{_ICONS_DIR}/android.png", "Ctrl+O", "<Control-o>"),
                    None,
                    AppToolbarItem("export_app_info", "Export app info", export.export_app_info, f"{_ICONS_DIR}/save_file.png"),
                    AppToolbarItem("extract_apk", "Extract to...", export.extract_apk, f"{_ICONS_DIR}/unarchive_file.png"),
                    AppToolbarItem("extract_icon", "Extract icon as PNG", export.extract_icon, f"{_ICONS_DIR}/image.png"),
                    None,
                    AppToolbarItem("exit", "Exit", self.exit_app, f"{_ICONS_DIR}/exit_app.png"),
                ],
                "Help": [
                    AppToolbarItem("source_code", "Source code", help_.open_source_code, f"{_ICONS_DIR}/code.png"),
                    AppToolbarItem("report_issue", "Report issue", help_.report_issue, f"{_ICONS_DIR}/bug_report.png"),
                    AppToolbarItem("about", "About", help_.show_about, f"{_ICONS_DIR}/info.png"),
                ],
            },
            icon_loader=self._icon_loader,
        )
        self.menu_bar.set_enabled(self._ANALYSIS_DEPENDENT_ITEMS, False)

    # --- Public actions ----------------------------------------------------

    def load_apk(self) -> None:
        apk_path = filedialog.askopenfilename(
            title="Select APK file",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")],
        )
        if apk_path:
            self.start_analysis(apk_path)

    def exit_app(self) -> None:
        self.files_panel.cleanup()  # drop temp files extracted for Open / Open with / Copy
        self.root.destroy()

    def start_analysis(self, apk_path: str) -> None:
        if not os.path.exists(apk_path):
            messagebox.showerror("Error", f"File not found:\n{apk_path}")
            return
        self._apk_path = None
        self._result = None
        self.menu_bar.set_enabled(self._ANALYSIS_DEPENDENT_ITEMS, False)
        self._set_status(f"Analyzing: {os.path.basename(apk_path)}... (Please wait)", "blue")
        self._set_loading(True)
        self.header.reset_to_placeholder(os.path.basename(apk_path))
        self.info_panel.clear()
        self.manifest_panel.clear()
        self.files_panel.clear()
        threading.Thread(target=self._analyze_in_background, args=(apk_path,), daemon=True).start()

    def _default_extract_folder_name(self) -> str:
        return self._result.default_name if self._result else "app"

    # --- Background worker (runs off the Tk main thread) ----------------------

    def _analyze_in_background(self, apk_path: str) -> None:
        try:
            result = self._analyzer.analyze(apk_path)
            manifest_xml = self._manifest_formatter.format(result.apk)
            file_tree = self._file_tree_builder.build(apk_path)
            self.root.after(
                0,
                lambda: self._render_result(
                    apk_path,
                    result,
                    manifest_xml,
                    file_tree
                )
            )
            self._set_status("Analysis completed successfully.", "green")
        except Exception as exc:
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Error",
                    f"An error occurred while analyzing the APK:\n{exc}"
                )
            )
            self.root.after(0, self.header.show_error)
            self._set_status("Analysis failed.", "red")
        finally:
            self.root.after(0, lambda: self._set_loading(False))

    # --- UI updates (must run on the Tk main thread) ---------------------------

    def _set_status(self, message: str, color: str = "gray") -> None:
        self.root.after(0, lambda: self.status_bar.set_status(message, color))

    def _set_loading(self, loading: bool) -> None:
        self.header.set_loading_enabled(not loading)
        self.menu_bar.set_enabled(("load_apk",), not loading)

    def _render_result(
            self,
            apk_path: str,
            result: AnalysisResult,
            manifest_xml: str,
            file_tree: dict[str, dict[str, Any]]
        ) -> None:
        self._apk_path = apk_path
        self._result = result

        app_info = result.sections.get("App Information", {})
        self.header.show_result(
            app_name=app_info.get("App name") or "",
            package_name=app_info.get("Package name") or "",
            icon_image=result.icon,
        )
        self.info_panel.render(result.sections)
        self.manifest_panel.render(manifest_xml)
        self.files_panel.render(apk_path, file_tree)
        self.menu_bar.set_enabled(self._ANALYSIS_DEPENDENT_ITEMS, True)
