"""
Windows implementation of SystemColorSchemeDetector: reads the "apps use
light theme" flag from the registry.
"""

import importlib

from apkviewer.domain.entities.color_scheme import ColorScheme
from apkviewer.domain.interfaces.system_color_scheme_detector import SystemColorSchemeDetector


class WindowsColorSchemeDetector(SystemColorSchemeDetector):
    _KEY: str = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    _VALUE: str = "AppsUseLightTheme"

    def detect(self) -> ColorScheme:
        try:
            winreg = importlib.import_module("winreg")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._KEY) as key:
                uses_light, _ = winreg.QueryValueEx(key, self._VALUE)
        except (ImportError, OSError):
            return ColorScheme.LIGHT
        return ColorScheme.LIGHT if uses_light else ColorScheme.DARK
