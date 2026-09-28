"""
Formats the analysis sections (the data behind the Information tab) as
plain, human-readable text suitable for saving into a .txt file.
"""

from collections.abc import Mapping
from typing import Any


class AppInfoSerializer:
    _INDENT: str = "  "

    def format(self, sections: Mapping[str, Mapping[str, Any]]) -> str:
        blocks = [self._format_section(title, fields) for title, fields in sections.items()]
        return "\n\n".join(blocks) + "\n"

    def _format_section(self, title: str, fields: Mapping[str, Any]) -> str:
        lines = [title, "=" * len(title)]
        for label, value in fields.items():
            if isinstance(value, list):
                lines.extend(self._format_list(label, value))
            else:
                lines.append(f"{label}: {'' if value is None else value}")
        return "\n".join(lines)

    def _format_list(self, label: str, items: list[Any]) -> list[str]:
        lines = [f"{label} ({len(items)}):"]
        if not items:
            lines.append(f"{self._INDENT}None found")
        for item in items:
            # Items such as certificates span several lines: keep them aligned.
            item_lines = str(item).splitlines() or [""]
            lines.append(f"{self._INDENT}- {item_lines[0]}")
            lines.extend(f"{self._INDENT}  {extra}" for extra in item_lines[1:])
        return lines
