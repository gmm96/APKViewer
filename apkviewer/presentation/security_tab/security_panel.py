"""
"Security" tab: permissions, app-ops, signing certificates, trackers and
third-party libraries.
"""

from tkinter import ttk

from apkviewer.domain.entities.analysis_labels import SECTION_SECURITY, SECTION_THIRD_PARTY
from apkviewer.presentation.common.sections_panel import SectionsPanel
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker


class SecurityPanel(SectionsPanel):
    def __init__(
        self,
        parent: ttk.Notebook,
        context_menu: TextContextMenu,
        line_marker: TextLineMarker | None = None,
    ) -> None:
        super().__init__(
            parent,
            (SECTION_SECURITY, SECTION_THIRD_PARTY),
            context_menu,
            line_marker,
        )
