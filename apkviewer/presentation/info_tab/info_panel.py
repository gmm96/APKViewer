"""
"Info" tab: displays the core application identity, build configuration, 
and embedded endpoints.
"""

from tkinter import ttk

from apkviewer.domain.entities.analysis_labels import (
    SECTION_APPLICATION,
    SECTION_CONFIGURATION,
    SECTION_EMBEDDED_CONTENT
)
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
        line_marker: TextLineMarker | None = None,
        size_formatter: SizeFormatter | None = None,
        date_formatter: DateFormatter | None = None,
    ) -> None:
        super().__init__(
            parent,
            (SECTION_APPLICATION, SECTION_CONFIGURATION, SECTION_EMBEDDED_CONTENT),
            context_menu,
            line_marker,
            size_formatter=size_formatter,
            date_formatter=date_formatter,
        )
