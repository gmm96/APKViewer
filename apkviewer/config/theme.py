"""
Fonts and colors shared across widgets.
"""

# --- Fonts ---
FONT_TITLE: tuple[str, int, str] = ("Helvetica", 20, "bold")
FONT_SUBTITLE: tuple[str, int] = ("Helvetica", 12)
FONT_MONO: tuple[str, int] = ("Consolas", 10)
FONT_MONO_SMALL: tuple[str, int] = ("Consolas", 9)
FONT_MONO_SMALL_ITALIC: tuple[str, int, str] = FONT_MONO_SMALL + ("italic",)

# --- Colors ---
COLOR_PLACEHOLDER_BG: str = "#e0e0e0"
COLOR_PLACEHOLDER_BORDER: str = "#cccccc"
COLOR_TEXT_BG: str = "#fcfcfc"
COLOR_MARK_BG: str = "#cfe3fc"
COLOR_FOLDER_BG: str = "#eef3f8"

# XML syntax highlight colors
COLOR_XML_TAG: str = "#0033B3"
COLOR_XML_ATTR: str = "#871094"
COLOR_XML_VALUE: str = "#067D17"
COLOR_XML_COMMENT: str = "#8C8C8C"
