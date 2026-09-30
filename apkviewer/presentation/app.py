"""
Main application window: wires together the header, status bar, tabs and
the background analysis. It is the composition root of the *presentation*
layer only: every use case and platform service it needs is handed in
from outside (see apkviewer.composition_root), so this layer never
imports the infrastructure layer.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from apkviewer.application.analyze_apk import AnalyzeApk
from apkviewer.application.entry_previewer import EntryPreviewer
from apkviewer.application.export_app_info import ExportAppInfo
from apkviewer.application.export_icon import ExportIcon
from apkviewer.application.extract_apk_entries import ExtractApkEntries
from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.domain.interfaces.url_opener import UrlOpener
from apkviewer.presentation.common.extract_to_dialog import ExtractToDialog
from apkviewer.presentation.common.status_bar import StatusBar
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.files_tab.files_panel import FilesPanel
from apkviewer.presentation.header.app_header import AppHeader
from apkviewer.presentation.icons.icon_loader import IconLoader
from apkviewer.presentation.info_tab.info_panel import InfoPanel
from apkviewer.presentation.intent.intent_details_dialog import IntentDetailsDialog
from apkviewer.presentation.manifest_tab.manifest_panel import ManifestPanel
from apkviewer.presentation.toolbar.app_toolbar import AppToolbar
from apkviewer.presentation.toolbar.file.file_menu import FileMenu
from apkviewer.presentation.toolbar.help.help_menu import HelpMenu
from apkviewer.presentation.viewmodels.app_toolbar_item import AppToolbarItem

_ICONS_DIR = "assets/icons/outline"


class ApkAnalyzerApp:
    # Menu items that only make sense once an APK has been analyzed.
    _ANALYSIS_DEPENDENT_ITEMS: tuple[str, ...] = ("export_app_info", "extract_apk", "extract_icon")

    def __init__(
        self,
        root: tk.Tk,
        analyze_apk: AnalyzeApk,
        extract_entries: ExtractApkEntries,
        entry_previewer: EntryPreviewer,
        export_app_info: ExportAppInfo,
        export_icon: ExportIcon,
        url_opener: UrlOpener,
        icon_loader: IconLoader | None = None,
    ) -> None:
        self.root: tk.Tk = root
        self.root.title("APKViewer")
        self.root.geometry("1000x750")
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self._analyze_apk: AnalyzeApk = analyze_apk
        self._entry_previewer: EntryPreviewer = entry_previewer
        self._icon_loader: IconLoader = icon_loader or IconLoader()

        # The analysis currently shown (None while nothing is loaded).
        self._result: AnalysisResult | None = None

        extract_dialog = ExtractToDialog(root, extract_entries)
        self._extract_dialog: ExtractToDialog = extract_dialog
        self._file_actions: FileMenu = FileMenu(
            parent=root,
            extract_dialog=extract_dialog,
            export_app_info=export_app_info,
            export_icon=export_icon,
            get_result=lambda: self._result,
        )
        self._help_actions: HelpMenu = HelpMenu(root, url_opener=url_opener)

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
            get_default_folder_name=self._default_extract_folder_name,
            extract_dialog=self._extract_dialog,
            entry_previewer=self._entry_previewer,
            icon_loader=self._icon_loader,
        )
        notebook.add(self.files_panel, text="Files")

    def _build_menu(self) -> None:
        export, help_ = self._file_actions, self._help_actions
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
            result = self._analyze_apk.execute(apk_path)
        except Exception as exc:
            # `exc` is unbound once the except block ends, so keep its text.
            self._report_failure(str(exc))
        else:
            self.root.after(0, lambda: self._render_result(result))
            self._set_status("Analysis completed successfully.", "green")
        finally:
            self.root.after(0, lambda: self._set_loading(False))

    def _report_failure(self, message: str) -> None:
        self.root.after(
            0,
            lambda: messagebox.showerror("Error", f"An error occurred while analyzing the APK:\n{message}"),
        )
        self.root.after(0, self.header.show_error)
        self._set_status("Analysis failed.", "red")

    # --- UI updates (must run on the Tk main thread) ---------------------------

    def _set_status(self, message: str, color: str = "gray") -> None:
        self.root.after(0, lambda: self.status_bar.set_status(message, color))

    def _set_loading(self, loading: bool) -> None:
        self.header.set_loading_enabled(not loading)
        self.menu_bar.set_enabled(("load_apk",), not loading)

    def _render_result(self, result: AnalysisResult) -> None:
        self._result = result
        self.header.show_result(
            app_name=result.app_name,
            package_name=result.package_name,
            icon_png=result.icon_png,
        )
        self.info_panel.render(result.sections)
        self.manifest_panel.render(result.manifest_xml)
        self.files_panel.render(result.apk_path, result.file_tree)
        self.menu_bar.set_enabled(self._ANALYSIS_DEPENDENT_ITEMS, True)
