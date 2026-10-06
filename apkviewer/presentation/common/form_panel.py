"""
Base class of the tabs made of "form" sections: read-only fields for
single values (with a copy icon) and read-only text boxes for lists. A tab
builds its sections explicitly (`add_section(...).add_entry(...)`), so it
decides what to show instead of rendering whatever a dictionary contains.
"""

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk
from typing import Any

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.appearance.tk_widget_styler import TkWidgetStyler
from apkviewer.presentation.common.auto_hide_scrollbar import AutoHideScrollbar
from apkviewer.presentation.common.copyable_entry import CopyableEntry
from apkviewer.presentation.common.scrollable_frame import ScrollableFrame
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker
from apkviewer.presentation.common.warning_banner import WarningBanner
from apkviewer.presentation.config.layout import LABEL_WIDTH, MIN_LIST_LINES
from apkviewer.presentation.config.theme import FONT_MONO_SMALL
from apkviewer.presentation.icons.field_icons import FieldIcons
from apkviewer.presentation.icons.icon_loader import IconLoader

# Chip kinds: "success", "danger", "neutral" (filled) and "muted" (outlined).
CHIP_KINDS: tuple[str, ...] = ("success", "danger", "neutral", "muted")


class FormPanel(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        line_marker: TextLineMarker | None = None,
        icon_loader: IconLoader | None = None,
    ) -> None:
        super().__init__(parent)
        self._palette: ThemePalette = palette
        self._context_menu: TextContextMenu = context_menu
        self._line_marker: TextLineMarker = line_marker or TextLineMarker()
        self._icons: FieldIcons = FieldIcons(icon_loader or IconLoader(), palette)
        self._list_widgets: list[tk.Text] = []
        self._copy_entries: list[CopyableEntry] = []
        self._chips: list[tuple[tk.Label, str]] = []
        self._muted_labels: list[ttk.Label] = []
        self._next_row: int = 0

        self.scroll_frame: ScrollableFrame = ScrollableFrame(self, palette)
        self.scroll_frame.pack(expand=True, fill=tk.BOTH)
        self.scroll_frame.inner_frame.columnconfigure(0, weight=1)
        self._banner: WarningBanner = WarningBanner(self, palette, before=self.scroll_frame)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        self.scroll_frame.apply_palette(palette)
        self._banner.apply_palette(palette)
        self._icons.apply_palette(palette)
        for widget in self._list_widgets:
            self._style_list_widget(widget)
        for entry in self._copy_entries:
            entry.refresh_icons()
        for chip, kind in self._chips:
            self._style_chip(chip, kind)
        for label in self._muted_labels:
            label.configure(foreground=palette.secondary_fg)

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        self._list_widgets.clear()
        self._copy_entries.clear()
        self._chips.clear()
        self._muted_labels.clear()
        self._next_row = 0
        for widget in self.scroll_frame.inner_frame.winfo_children():
            widget.destroy()

    def add_section(self, title: str, badge: tuple[str, str] | None = None) -> "FormSection":
        """`badge`: optional (text, chip kind) shown on the section's title line, at its right."""
        frame = ttk.LabelFrame(self.scroll_frame.inner_frame, text=title)
        frame.grid(row=self._next_row, column=0, sticky="ew", padx=15, pady=10)
        self._next_row += 1
        if badge is not None:
            self.create_chip(frame, *badge).place(relx=1.0, x=-14, y=-4, anchor="ne")
        return FormSection(self, frame)

    # --- Widgets shared by the sections ------------------------------------------------------

    def create_copy_entry(self, parent: tk.Misc, text: str, monospace: bool = False) -> CopyableEntry:
        entry = CopyableEntry(parent, text, self._icons, font=FONT_MONO_SMALL if monospace else None)
        self._copy_entries.append(entry)
        return entry

    def create_chip(self, parent: tk.Misc, text: str, kind: str) -> tk.Label:
        chip = tk.Label(parent, text=text, padx=8, pady=1, borderwidth=0)
        self._chips.append((chip, kind))
        self._style_chip(chip, kind)
        return chip

    def create_muted_label(self, parent: tk.Misc, text: str) -> ttk.Label:
        label = ttk.Label(parent, text=text, foreground=self._palette.secondary_fg)
        self._muted_labels.append(label)
        return label

    def _style_chip(self, chip: tk.Label, kind: str) -> None:
        p = self._palette
        foreground, background, border = {
            "success": (p.status_success, p.mark_bg, p.mark_bg),
            "danger": (p.status_error, p.folder_bg, p.folder_bg),
            "neutral": (p.secondary_fg, p.folder_bg, p.folder_bg),
            "muted": (p.secondary_fg, p.window_bg, p.placeholder_border),
        }[kind]
        chip.configure(
            foreground=foreground, background=background,
            highlightthickness=1, highlightbackground=border, highlightcolor=border,
        )

    def build_list_widget(self, container: ttk.Frame, text: str, line_count: int) -> None:
        text_widget = tk.Text(
            container,
            height=line_count,
            wrap=tk.NONE,
            borderwidth=1,
            relief="solid",
            font=FONT_MONO_SMALL,
        )
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=text_widget.xview)
        autohide = AutoHideScrollbar(h_scroll, {"row": 1, "column": 0, "sticky": "ew"})
        text_widget.configure(xscrollcommand=autohide.scroll_command)
        text_widget.grid(row=0, column=0, sticky="ew")
        text_widget.insert(tk.END, text)
        text_widget.configure(state="disabled")
        self._line_marker.bind(text_widget)
        self._list_widgets.append(text_widget)
        self._style_list_widget(text_widget)
        self._context_menu.attach(text_widget)

    def _style_list_widget(self, text_widget: tk.Text) -> None:
        TkWidgetStyler.style_text(text_widget, self._palette)
        self._line_marker.apply_palette(text_widget, self._palette)


class FormSection:
    """One LabelFrame of a FormPanel; each call adds a row to it."""

    def __init__(self, panel: FormPanel, frame: ttk.LabelFrame) -> None:
        self._panel: FormPanel = panel
        self.frame: ttk.LabelFrame = frame  # for sections that lay out their own widgets
        self._row: int = 0
        frame.columnconfigure(1, weight=1)

    def add_group(self, title: str) -> None:
        """A small caption that starts a group of rows."""
        self._panel.create_muted_label(self.frame, title.upper()).grid(
            row=self._row, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0)
        )
        self._row += 1

    def add_entry(self, label_text: str, value: Any, monospace: bool = False) -> None:
        """A selectable, read-only field; a copy icon appears while it is hovered or focused."""
        ttk.Label(self.frame, text=label_text, width=LABEL_WIDTH).grid(
            row=self._row, column=0, sticky="w", padx=10, pady=5
        )
        field = self._panel.create_copy_entry(
            self.frame, "" if value is None else str(value), monospace
        )
        field.grid(row=self._row, column=1, sticky="ew", padx=10, pady=5)
        self._row += 1

    def add_list(self, label_text: str, items: Sequence[str], separator: str = "\n") -> None:
        ttk.Label(self.frame, text=f"{label_text} ({len(items)})", width=LABEL_WIDTH).grid(
            row=self._row, column=0, sticky="nw", padx=10, pady=5
        )
        text, line_count = _build_display_text(items, separator)
        container = ttk.Frame(self.frame)
        container.grid(row=self._row, column=1, sticky="ew", padx=10, pady=5)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self._panel.build_list_widget(container, text, line_count)
        self._row += 1


def _build_display_text(items: Sequence[str], separator: str) -> tuple[str, int]:
    text = separator.join(items) if items else "None found"
    line_count = max(text.count("\n") + 1, MIN_LIST_LINES)
    text += "\n" * (line_count - (text.count("\n") + 1))
    return text, line_count
