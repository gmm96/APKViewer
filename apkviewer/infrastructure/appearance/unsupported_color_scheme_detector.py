"""
Fallback for platforms where the system color scheme cannot be queried.
"""

from apkviewer.domain.entities.color_scheme import ColorScheme
from apkviewer.domain.interfaces.system_color_scheme_detector import SystemColorSchemeDetector


class UnsupportedColorSchemeDetector(SystemColorSchemeDetector):
    def detect(self) -> ColorScheme:
        return ColorScheme.LIGHT
