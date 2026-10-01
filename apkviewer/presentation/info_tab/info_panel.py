"""
"Info" tab: short dashboard with the app identity, versions, SDK range,
architectures and hardware features.
"""

from tkinter import ttk

from apkviewer.domain.entities.analysis_labels import SECTION_APPLICATION, SECTION_CONFIGURATION, SECTION_EMBEDDED_CONTENT
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.sections_panel import SectionsPanel
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker
from apkviewer.domain.interfaces.date_formatter import DateFormatter
from apkviewer.domain.interfaces.size_formatter import SizeFormatter


class InfoPanel(SectionsPanel):
    def __init__(
        self,
        parent: ttk.Notebook,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        line_marker: TextLineMarker | None = None,
        size_formatter: SizeFormatter | None = None,
        date_formatter: DateFormatter | None = None,
    ) -> None:
        super().__init__(
            parent,
            (SECTION_APPLICATION, SECTION_CONFIGURATION, SECTION_EMBEDDED_CONTENT),
            context_menu,
            palette,
            line_marker,
            size_formatter,
            date_formatter
        )
