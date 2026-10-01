"""
Formats byte counts as B / KB / MB / GB / TB, as most file browsers do.
"""

from apkviewer.domain.interfaces.size_formatter import SizeFormatter


class HumanReadableSizeFormatter(SizeFormatter):
    _UNITS: tuple[str, str, str, str] = ("B", "KB", "MB", "GB")

    def format(self, num_bytes: int, full_mode: bool = False) -> str:
        try:
            num = float(num_bytes)
        except (TypeError, ValueError):
            return "-"
        total_bytes = int(num)
        for unit in self._UNITS:
            if num < 1024.0:
                readable = f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
                if full_mode:
                    return f"{readable} ({total_bytes:,} B)"
                return readable
            num /= 1024.0
        readable = f"{num:.1f} TB"
        if full_mode:
            return f"{readable} ({total_bytes:,} B)"
        return readable
