"""
"Components" tab: declared activities, services, receivers and providers,
plus the exported intent actions (double-click one to see its details).
"""

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from apkviewer.domain.entities.analysis_labels import (
    FIELD_INTENT_ACTIONS,
    SECTION_COMPONENTS,
    SECTION_INTENTS,
)
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.sections_panel import SectionsPanel
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker


class ComponentsPanel(SectionsPanel):
    def __init__(
        self,
        parent: ttk.Notebook,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        on_intent_double_click: Callable[[str], None],
        line_marker: TextLineMarker | None = None,
    ) -> None:
        super().__init__(
            parent,
            (SECTION_COMPONENTS, SECTION_INTENTS),
            context_menu,
            palette,
            line_marker,
        )
        self._on_intent_double_click: Callable[[str], None] = on_intent_double_click

    def _on_list_widget_created(self, label_text: str, text_widget: tk.Text) -> None:
        if label_text == FIELD_INTENT_ACTIONS:
            text_widget.bind("<Double-Button-1>", self._handle_intent_double_click)

    def _handle_intent_double_click(self, event: tk.Event) -> None:
        widget = event.widget
        if not isinstance(widget, tk.Text):
            return
        index = widget.index(f"@{event.x},{event.y}")
        line_num = index.split(".")[0]
        line_text = widget.get(f"{line_num}.0", f"{line_num}.end").strip()
        if line_text and line_text != "None found":
            self._on_intent_double_click(line_text)
