"""
Minimal XML syntax highlighter applied to the Manifest.xml text view.
"""

import re
import tkinter as tk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.config.theme import FONT_MONO_SMALL_ITALIC


class XmlSyntaxHighlighter:
    _TAG_RE: re.Pattern = re.compile(r"<[^>]+>")
    _ATTR_RE: re.Pattern = re.compile(r"([a-zA-Z0-9_:-]+)\s*=\s*(\"[^\"]*\"|'[^']*')")
    _COMMENT_RE: re.Pattern = re.compile(r"<!--.*?-->", re.DOTALL)

    def configure_tags(self, text_widget: tk.Text, palette: ThemePalette) -> None:
        """(Re)configure the tag colors; safe to call again when the palette changes."""
        text_widget.tag_configure("xml_tag", foreground=palette.xml_tag)
        text_widget.tag_configure("xml_attr", foreground=palette.xml_attr)
        text_widget.tag_configure("xml_value", foreground=palette.xml_value)
        text_widget.tag_configure(
            "xml_comment",
            foreground=palette.xml_comment,
            font=FONT_MONO_SMALL_ITALIC
        )

    def highlight(self, text_widget: tk.Text, content: str) -> None:
        for match in self._TAG_RE.finditer(content):
            self._tag_range(text_widget, "xml_tag", match.start(), match.end())
            self._highlight_attributes(text_widget, match)

        for match in self._COMMENT_RE.finditer(content):
            self._tag_range(text_widget, "xml_comment", match.start(), match.end())
            text_widget.tag_raise("xml_comment")

    def _highlight_attributes(
            self,
            text_widget: tk.Text,
            tag_match: "re.Match"
        ) -> None:
        tag_str = tag_match.group()
        base = tag_match.start()
        for attr_match in self._ATTR_RE.finditer(tag_str):
            self._tag_range(
                text_widget,
                "xml_attr",
                base + attr_match.start(1), base + attr_match.end(1)
            )
            self._tag_range(
                text_widget,
                "xml_value",
                base + attr_match.start(2), base + attr_match.end(2)
            )

    @staticmethod
    def _tag_range(text_widget: tk.Text, tag_name: str, start: int, end: int) -> None:
        text_widget.tag_add(tag_name, f"1.0 + {start} chars", f"1.0 + {end} chars")
