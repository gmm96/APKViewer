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
from apkviewer.application.resolve_color_scheme import ResolveColorScheme
from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.domain.entities.analysis_warning import AnalysisArea
from apkviewer.domain.entities.color_mode import ColorMode
from apkviewer.domain.interfaces.url_opener import UrlOpener
from apkviewer.domain.interfaces.size_formatter import SizeFormatter
from apkviewer.domain.interfaces.date_formatter import DateFormatter
from apkviewer.presentation.appearance.forest_theme import ForestTheme
from apkviewer.presentation.appearance.theme_manager import ThemeManager
from apkviewer.presentation.common.extract_to_dialog import ExtractToDialog
from apkviewer.presentation.common.status_bar import StatusBar
from apkviewer.presentation.common.status_level import StatusLevel
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.components_tab.components_panel import ComponentsPanel
from apkviewer.presentation.files_tab.files_panel import FilesPanel
from apkviewer.presentation.header.app_header import AppHeader
from apkviewer.presentation.icons.icon_loader import IconLoader
from apkviewer.presentation.info_tab.info_panel import InfoPanel
from apkviewer.presentation.intents_tab.intents_panel import IntentsPanel
from apkviewer.presentation.manifest_tab.manifest_panel import ManifestPanel
from apkviewer.presentation.permissions_tab.permissions_panel import PermissionsPanel
from apkviewer.presentation.security_tab.security_panel import SecurityPanel
from apkviewer.presentation.toolbar.app_toolbar import AppToolbar
from apkviewer.presentation.toolbar.file.file_menu import FileMenu
from apkviewer.presentation.toolbar.help.help_menu import HelpMenu
from apkviewer.presentation.toolbar.settings.settings_menu import SettingsMenu
from apkviewer.presentation.viewmodels.app_toolbar_choice import AppToolbarChoice
from apkviewer.presentation.viewmodels.app_toolbar_choice_group import AppToolbarChoiceGroup
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
        resolve_color_scheme: ResolveColorScheme,
        icon_loader: IconLoader | None = None,
        size_formatter: SizeFormatter | None = None,
        date_formatter: DateFormatter | None = None,
    ) -> None:
        self.root: tk.Tk = root
        self.root.title("APKViewer")
        self.root.geometry("1000x750")
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self._analyze_apk: AnalyzeApk = analyze_apk
        self._entry_previewer: EntryPreviewer = entry_previewer
        self._icon_loader: IconLoader = icon_loader or IconLoader()
        self._size_formatter: SizeFormatter | None = size_formatter
        self._date_formatter: DateFormatter | None = date_formatter

        # Activates the ttk theme (AUTO = follow the OS) before any widget exists.
        self._theme: ThemeManager = ThemeManager(root, ForestTheme(root), resolve_color_scheme)

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
        self._settings_actions: SettingsMenu = SettingsMenu(root, self._theme)

        self.context_menu: TextContextMenu = TextContextMenu(root, self._theme.palette)
        self._build_menu()  # first: the menu bar must be packed at the very top of the window
        self._build_layout()
        self._subscribe_to_theme_changes()

    def _subscribe_to_theme_changes(self) -> None:
        for listener in (
            self.header.apply_palette,
            self.status_bar.apply_palette,
            self.context_menu.apply_palette,
            self.menu_bar.apply_palette,
            self.info_panel.apply_palette,
            self.security_panel.apply_palette,
            self.permissions_panel.apply_palette,
            self.components_panel.apply_palette,
            self.intents_panel.apply_palette,
            self.manifest_panel.apply_palette,
            self.files_panel.apply_palette,
        ):
            self._theme.subscribe(listener)

    def _build_layout(self) -> None:
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
        self.header: AppHeader = AppHeader(
            top_frame, on_load_click=self.load_apk, palette=self._theme.palette
        )
        self.header.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.status_bar: StatusBar = StatusBar(self.root, self._theme.palette)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        palette = self._theme.palette
        self.info_panel: InfoPanel = InfoPanel(
            notebook,
            self.context_menu,
            palette,
            size_formatter=self._size_formatter,
            date_formatter=self._date_formatter,
        )
        self.security_panel: SecurityPanel = SecurityPanel(notebook, self.context_menu, palette)
        self.permissions_panel: PermissionsPanel = PermissionsPanel(notebook, palette)
        self.components_panel: ComponentsPanel = ComponentsPanel(notebook, palette)
        self.intents_panel: IntentsPanel = IntentsPanel(notebook, palette)
        self.manifest_panel: ManifestPanel = ManifestPanel(notebook, self.context_menu, palette)
        self.files_panel: FilesPanel = FilesPanel(
            notebook,
            get_default_folder_name=self._default_extract_folder_name,
            extract_dialog=self._extract_dialog,
            entry_previewer=self._entry_previewer,
            palette=palette,
            icon_loader=self._icon_loader,
        )

        notebook.add(self.info_panel, text="Info")
        notebook.add(self.security_panel, text="Security")
        notebook.add(self.permissions_panel, text="Permissions")
        notebook.add(self.components_panel, text="Components")
        notebook.add(self.intents_panel, text="Intents")
        notebook.add(self.manifest_panel, text="Manifest")
        notebook.add(self.files_panel, text="Files")

    def _build_menu(self) -> None:
        export, help_ = self._file_actions, self._help_actions
        settings = self._settings_actions
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
                "Settings": [
                    AppToolbarChoiceGroup(
                        key="color_mode",
                        title="Color mode",
                        choices=(
                            AppToolbarChoice(
                                ColorMode.LIGHT.value, "Light mode",
                                lambda: settings.set_color_mode(ColorMode.LIGHT),
                                f"{_ICONS_DIR}/light_mode.png",
                            ),
                            AppToolbarChoice(
                                ColorMode.DARK.value, "Dark mode",
                                lambda: settings.set_color_mode(ColorMode.DARK),
                                f"{_ICONS_DIR}/dark_mode.png",
                            ),
                            AppToolbarChoice(
                                ColorMode.AUTO.value, "Auto (follow system)",
                                lambda: settings.set_color_mode(ColorMode.AUTO),
                            ),
                        ),
                        selected_key=settings.color_mode.value,
                    ),
                ],
                "Help": [
                    AppToolbarItem("source_code", "Source code", help_.open_source_code, f"{_ICONS_DIR}/code.png"),
                    AppToolbarItem("report_issue", "Report issue", help_.report_issue, f"{_ICONS_DIR}/bug_report.png"),
                    AppToolbarItem("about", "About", help_.show_about, f"{_ICONS_DIR}/info.png"),
                ],
            },
            self._theme.palette,
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
        self._set_status(
            f"Analyzing: {os.path.basename(apk_path)}... (Please wait)", StatusLevel.INFO
        )
        self._set_loading(True)
        self.header.reset_to_placeholder(os.path.basename(apk_path))
        self.info_panel.clear()
        self.security_panel.clear()
        self.permissions_panel.clear()
        self.components_panel.clear()
        self.intents_panel.clear()
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
            count = len(result.inspection.warnings)
            if count:
                self._set_status(
                    f"Analysis completed with {count} warning(s): some data could not be read "
                    "(see the notice at the top of the tabs).",
                    StatusLevel.INFO,
                )
            else:
                self._set_status("Analysis completed successfully.", StatusLevel.SUCCESS)
        finally:
            self.root.after(0, lambda: self._set_loading(False))

    def _report_failure(self, message: str) -> None:
        self.root.after(
            0,
            lambda: messagebox.showerror(
                "Error",
                f"An error occurred while analyzing the APK:\n{message}"
            ),
        )
        self.root.after(0, self.header.show_error)
        self._set_status("Analysis failed.", StatusLevel.ERROR)

    # --- UI updates (must run on the Tk main thread) ---------------------------

    def _set_status(self, message: str, level: StatusLevel = StatusLevel.NEUTRAL) -> None:
        self.root.after(0, lambda: self.status_bar.set_status(message, level))

    def _set_loading(self, loading: bool) -> None:
        self.header.set_loading_enabled(not loading)
        self.menu_bar.set_enabled(("load_apk",), not loading)

    def _render_result(self, result: AnalysisResult) -> None:
        self._result = result
        inspection = result.inspection
        self.header.show_result(
            app_name=result.app_name,
            package_name=result.package_name,
            icon_png=result.icon_png,
        )
        self.info_panel.render(
            inspection.application, inspection.configuration, inspection.embedded_content
        )
        self.security_panel.render(inspection.security, inspection.third_party)
        self.permissions_panel.render(inspection.permissions)
        self.components_panel.render(inspection.components)
        self.intents_panel.render(inspection.components.exported_intents())
        self.manifest_panel.render(result.manifest_xml)
        self.files_panel.render(result.apk_path, result.file_tree)
        components_warnings = result.warning_messages(AnalysisArea.COMPONENTS)
        self.info_panel.show_warnings(result.warning_messages(AnalysisArea.INFO, AnalysisArea.ICON))
        self.security_panel.show_warnings(result.warning_messages(AnalysisArea.SECURITY))
        self.permissions_panel.show_warnings(result.warning_messages(AnalysisArea.PERMISSIONS))
        self.components_panel.show_warnings(components_warnings)
        self.intents_panel.show_warnings(components_warnings)
        self.menu_bar.set_enabled(self._ANALYSIS_DEPENDENT_ITEMS, True)
