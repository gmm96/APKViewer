"""
"Manifest" tab: read-only text view with XML syntax highlighting.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional

from config import COLOR_TEXT_BG, FONT_MONO
from ui.context_menu import TextContextMenu
from ui.widgets.xml_highlighter import XmlSyntaxHighlighter
from utils.ui_helpers import AutoHideScrollbar


class ManifestPanel(ttk.Frame):
    def __init__(self, parent, context_menu: TextContextMenu, highlighter: Optional[XmlSyntaxHighlighter] = None) -> None:
        super().__init__(parent)
        self._highlighter: XmlSyntaxHighlighter = highlighter or XmlSyntaxHighlighter()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.text = tk.Text(self, wrap=tk.NONE, font=FONT_MONO, borderwidth=0, bg=COLOR_TEXT_BG)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        autohide = AutoHideScrollbar(h_scroll, {"row": 1, "column": 0, "sticky": "ew"})

        self.text.configure(yscrollcommand=v_scroll.set, xscrollcommand=autohide.scroll_command)
        self.text.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self._highlighter.configure_tags(self.text)
        context_menu.attach(self.text)

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete(1.0, tk.END)

    def render(self, manifest_xml: str):
        self.clear()
        padded_xml = self._pad_lines_to_equal_width(manifest_xml)
        self.text.insert(tk.END, padded_xml)
        self._highlighter.highlight(self.text, padded_xml)
        self.text.configure(state="disabled")

    @staticmethod
    def _pad_lines_to_equal_width(content: str) -> str:
        """
        Right-pad every line with spaces so they all share the width of the
        longest one.

        Tk's Text widget (wrap="none") only reserves horizontal scroll room
        for the lines currently in the vertical viewport - it recomputes
        that room dynamically as you scroll, so without this, the
        horizontal scrollbar keeps resizing itself depending on which part
        of the document happens to be visible. Padding every line to a
        uniform width means whatever is on screen always reports the true,
        whole-document width, so the scrollbar is identical for line 1 and
        line 1000. The added spaces are invisible (monospace font) and are
        stripped again on copy - see TextContextMenu.
        """
        lines = content.split("\n")
        max_len = max((len(line) for line in lines), default=0)
        return "\n".join(line.ljust(max_len) for line in lines)
