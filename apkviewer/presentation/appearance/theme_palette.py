"""
Every color the application needs that the ttk theme cannot provide by
itself (classic Tk widgets, text tags, tinted icons, status messages).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePalette:
    window_bg: str
    text_bg: str
    text_fg: str
    disabled_fg: str
    secondary_fg: str
    selection_bg: str
    selection_fg: str
    mark_bg: str
    folder_bg: str
    placeholder_bg: str
    placeholder_border: str
    icon_tint: str
    xml_tag: str
    xml_attr: str
    xml_value: str
    xml_comment: str
    status_neutral: str
    status_info: str
    status_success: str
    status_error: str
