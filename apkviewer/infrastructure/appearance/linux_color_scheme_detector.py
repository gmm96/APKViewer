"""
Linux implementation of SystemColorSchemeDetector. Desktops expose their
preference in different places, so a few probes are tried in order; the
first whose answer mentions "dark" decides.
"""

import subprocess

from apkviewer.domain.entities.color_scheme import ColorScheme
from apkviewer.domain.interfaces.system_color_scheme_detector import SystemColorSchemeDetector


class LinuxColorSchemeDetector(SystemColorSchemeDetector):
    _PROBES: tuple[list[str], ...] = (
        # GNOME 42+ and most freedesktop-aware desktops: 'prefer-dark'.
        ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
        # Older GTK desktops: theme names such as 'Adwaita-dark'.
        ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
        # KDE Plasma: color scheme names such as 'BreezeDark'.
        ["kreadconfig6", "--group", "General", "--key", "ColorScheme"],
        ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
    )

    def detect(self) -> ColorScheme:
        if any(self._answer_mentions_dark(probe) for probe in self._PROBES):
            return ColorScheme.DARK
        return ColorScheme.LIGHT

    @staticmethod
    def _answer_mentions_dark(command: list[str]) -> bool:
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=2, check=False
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0 and "dark" in result.stdout.lower()
