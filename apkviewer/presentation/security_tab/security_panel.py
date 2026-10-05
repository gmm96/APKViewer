"""
"Security" tab: signature schemes, permissions, app-ops, one section per
signing certificate (fingerprints, key, validity...), trackers and
third-party libraries.

Certificate values are read-only entry fields on purpose: a fingerprint is
something to select and copy (VirusTotal, `apksigner` comparisons...).
"""

from datetime import datetime, timezone
from tkinter import ttk

from apkviewer.domain.entities.security_info import Certificate, SecurityInfo
from apkviewer.domain.entities.third_party_info import ThirdPartyInfo
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.form_panel import FormPanel
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker

_CHECKED_SCHEMES: tuple[str, ...] = ("v1 (JAR)", "v2", "v3", "v3.1")


class SecurityPanel(FormPanel):
    def __init__(
        self,
        parent: ttk.Notebook,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        line_marker: TextLineMarker | None = None,
    ) -> None:
        super().__init__(parent, context_menu, palette, line_marker)

    def render(self, security: SecurityInfo, third_party: ThirdPartyInfo) -> None:
        self.clear()

        section = self.add_section("Permissions & Signing")
        section.add_entry("Signature schemes", self._schemes_text(security.signature_schemes))
        section.add_list("Permissions", security.permissions)
        section.add_list("AppOps / Custom Perms", security.custom_permissions)

        now = datetime.now(timezone.utc)
        total = len(security.certificates)
        for number, certificate in enumerate(security.certificates, start=1):
            self._render_certificate(number, total, certificate, now)

        section = self.add_section("Third-party Code")
        section.add_list("Libraries", third_party.libraries)
        section.add_list("Trackers", third_party.trackers)

    def _render_certificate(
        self, number: int, total: int, certificate: Certificate, now: datetime
    ) -> None:
        section = self.add_section(f"Signing certificate {number} of {total}")
        if not certificate.is_readable:
            section.add_entry("Certificate", certificate.as_text())
            return
        for label, value in certificate.fields(now):
            section.add_entry(label, value)

    @staticmethod
    def _schemes_text(present: tuple[str, ...]) -> str:
        """Every scheme explicitly as yes/no. v4 is a separate .idsig file: not visible in the APK."""
        checked = [f"{scheme}: {'yes' if scheme in present else 'no'}" for scheme in _CHECKED_SCHEMES]
        return "   ·   ".join(checked + ["v4: not detectable from the APK"])
