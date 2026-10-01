"""
Formats a datetime into an extended English format (24h).
"""

from datetime import datetime

from apkviewer.domain.interfaces.date_formatter import DateFormatter


class EnglishLongDateFormatter(DateFormatter):
    _DAYS: tuple[str, ...] = (
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    )
    _MONTHS: tuple[str, ...] = ("",
        "January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December"
    )

    def format(self, dt: datetime) -> str:
        day_name = self._DAYS[dt.weekday()]
        month_name = self._MONTHS[dt.month]
        ordinal_day = self._get_ordinal(dt.day)
        time_str = dt.strftime("%H:%M:%S")
        ms = f"{dt.microsecond // 1000:03d}"
        return f"{day_name}, {ordinal_day} {month_name} {dt.year}, {time_str}.{ms}"

    @staticmethod
    def _get_ordinal(n: int) -> str:
        if 11 <= (n % 100) <= 13:
            return f"{n}th"
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"
