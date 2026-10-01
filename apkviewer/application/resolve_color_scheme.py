"""
Use case: turn the user's color preference into the scheme to render.
The operating system is only queried when the preference is AUTO.
"""

from apkviewer.domain.entities.color_mode import ColorMode
from apkviewer.domain.entities.color_scheme import ColorScheme
from apkviewer.domain.interfaces.system_color_scheme_detector import SystemColorSchemeDetector


class ResolveColorScheme:
    def __init__(self, detector: SystemColorSchemeDetector) -> None:
        self._detector: SystemColorSchemeDetector = detector

    def execute(self, mode: ColorMode) -> ColorScheme:
        if mode is ColorMode.LIGHT:
            return ColorScheme.LIGHT
        if mode is ColorMode.DARK:
            return ColorScheme.DARK
        return self._detector.detect()
