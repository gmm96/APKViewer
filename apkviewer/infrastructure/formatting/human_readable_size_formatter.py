"""
Formats byte counts as B / KB / MB / GB / TB, as most file browsers do.
"""

from apkviewer.domain.interfaces import SizeFormatter


class HumanReadableSizeFormatter(SizeFormatter):
    _UNITS: tuple[str, str, str, str] = ("B", "KB", "MB", "GB")

    def format(self, num_bytes: int) -> str:
        try:
            num = float(num_bytes)
        except (TypeError, ValueError):
            return "-"
        for unit in self._UNITS:
            if num < 1024.0:
                return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} TB"
