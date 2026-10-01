"""
macOS implementation of SystemColorSchemeDetector: the global
AppleInterfaceStyle default only exists (as "Dark") in dark mode.
"""

import subprocess

from apkviewer.domain.entities.color_scheme import ColorScheme
from apkviewer.domain.interfaces.system_color_scheme_detector import SystemColorSchemeDetector


class MacColorSchemeDetector(SystemColorSchemeDetector):
    def detect(self) -> ColorScheme:
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return ColorScheme.LIGHT
        is_dark = result.returncode == 0 and "dark" in result.stdout.lower()
        return ColorScheme.DARK if is_dark else ColorScheme.LIGHT
