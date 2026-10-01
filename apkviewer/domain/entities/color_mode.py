"""
The user's color preference. AUTO means "follow the operating system" and
is resolved into a concrete ColorScheme by the ResolveColorScheme use case.
"""

from enum import Enum


class ColorMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
