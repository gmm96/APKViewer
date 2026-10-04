"""
Minimal XML syntax highlighter applied to the Manifest.xml text view.

Positions are converted to "line.column" indices and applied in one
`tag_add` call per tag: Tk resolves "1.0 + N chars" by walking the text
from the start, which made big manifests (hundreds of KB) take half a
minute and freeze the window.
"""

import re
import tkinter as tk
from bisect import bisect_right
from collections.abc import Callable

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
        """`content` must be exactly the text inserted at the start of the widget."""
        line_starts = [0]
        line_starts.extend(match.end() for match in re.finditer("\n", content))

        def index(offset: int) -> str:
            line = bisect_right(line_starts, offset) - 1
            return f"{line + 1}.{offset - line_starts[line]}"

        ranges: dict[str, list[str]] = {
            "xml_tag": [], "xml_attr": [], "xml_value": [], "xml_comment": [],
        }
        for tag_match in self._TAG_RE.finditer(content):
            self._add(ranges["xml_tag"], index, tag_match.start(), tag_match.end())
            base = tag_match.start()
            for attr_match in self._ATTR_RE.finditer(tag_match.group()):
                self._add(ranges["xml_attr"], index, base + attr_match.start(1), base + attr_match.end(1))
                self._add(ranges["xml_value"], index, base + attr_match.start(2), base + attr_match.end(2))
        for match in self._COMMENT_RE.finditer(content):
            self._add(ranges["xml_comment"], index, match.start(), match.end())

        for tag_name, indices in ranges.items():
            if indices:
                text_widget.tag_add(tag_name, *indices)
        text_widget.tag_raise("xml_comment")

    @staticmethod
    def _add(target: list[str], index: Callable[[int], str], start: int, end: int) -> None:
        target.append(index(start))
        target.append(index(end))
