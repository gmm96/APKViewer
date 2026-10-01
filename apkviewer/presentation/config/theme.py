"""
Fonts shared across widgets. Colors live in the palettes
(see apkviewer.presentation.appearance.palettes).
"""

# --- Fonts ---
FONT_TITLE: tuple[str, int, str] = ("Helvetica", 20, "bold")
FONT_SUBTITLE: tuple[str, int] = ("Helvetica", 12)
FONT_MONO: tuple[str, int] = ("Consolas", 10)
FONT_MONO_SMALL: tuple[str, int] = ("Consolas", 9)
FONT_MONO_SMALL_ITALIC: tuple[str, int, str] = FONT_MONO_SMALL + ("italic",)
