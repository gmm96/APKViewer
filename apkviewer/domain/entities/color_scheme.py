"""
A concrete color scheme that can be rendered (what the user actually sees).
"""

from enum import Enum


class ColorScheme(Enum):
    LIGHT = "light"
    DARK = "dark"
