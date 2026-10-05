"""
"Info" tab: app identity, versions, SDK range, configuration and the
content embedded in the code.
"""

from tkinter import ttk

from apkviewer.domain.entities.application_info import ApplicationInfo
from apkviewer.domain.entities.configuration_info import ConfigurationInfo
from apkviewer.domain.entities.embedded_content import EmbeddedContent
from apkviewer.domain.interfaces.date_formatter import DateFormatter
from apkviewer.domain.interfaces.size_formatter import SizeFormatter
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.form_panel import FormPanel
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker
from apkviewer.presentation.formatting.english_long_date_formatter import EnglishLongDateFormatter
from apkviewer.presentation.formatting.human_readable_size_formatter import HumanReadableSizeFormatter


class InfoPanel(FormPanel):
    def __init__(
        self,
        parent: ttk.Notebook,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        line_marker: TextLineMarker | None = None,
        size_formatter: SizeFormatter | None = None,
        date_formatter: DateFormatter | None = None,
    ) -> None:
        super().__init__(parent, context_menu, palette, line_marker)
        self._size_formatter: SizeFormatter = size_formatter or HumanReadableSizeFormatter()
        self._date_formatter: DateFormatter = date_formatter or EnglishLongDateFormatter()

    def render(
        self,
        application: ApplicationInfo,
        configuration: ConfigurationInfo,
        embedded_content: EmbeddedContent,
    ) -> None:
        self.clear()

        section = self.add_section("Application")
        section.add_entry("App Name", application.app_name)
        section.add_entry("Package Name", application.package_name)
        section.add_entry("Version Name", application.version_name)
        section.add_entry("Version Code", application.version_code)
        section.add_entry("Min SDK", application.min_sdk)
        section.add_entry("Target SDK", application.target_sdk)
        if application.max_sdk:
            section.add_entry("Max SDK", application.max_sdk)
        section.add_entry("File Name", application.file_name or "Unknown")
        section.add_entry("File Path", application.file_path or "Unknown")
        section.add_entry("File Size", self._format_size(application.file_size))
        section.add_entry("Last Modified", self._format_date(application))

        section = self.add_section("Configuration")
        section.add_entry(
            "Architectures",
            ", ".join(configuration.architectures) or "None / Unknown (Java only)",
        )
        section.add_list(
            "Hardware Requirements",
            [feature.as_text() for feature in configuration.hardware_requirements],
        )
        section.add_list("Supported Locales", configuration.locales)
        section.add_list("Screen Densities", configuration.screen_densities)

        section = self.add_section("Embedded Content")
        section.add_list("Discovered URLs", embedded_content.urls)

    def _format_size(self, size: int | None) -> str:
        return "Unknown" if size is None else self._size_formatter.format(size, True)

    def _format_date(self, application: ApplicationInfo) -> str:
        modified = application.last_modified
        return "Unknown" if modified is None else self._date_formatter.format(modified)
