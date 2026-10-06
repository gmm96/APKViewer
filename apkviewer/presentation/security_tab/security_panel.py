"""
"Security" tab: the APK signature schemes (a table with the status of each),
one card per signing certificate (identity, validity, key, fingerprints),
permissions, trackers and third-party libraries.

Certificate values are selectable fields (with a copy icon) because a
fingerprint is something to copy: VirusTotal, `apksigner` comparisons...
"""

from datetime import datetime, timezone
from tkinter import ttk

from apkviewer.domain.entities.security_info import Certificate, SecurityInfo
from apkviewer.domain.entities.third_party_info import ThirdPartyInfo
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.form_panel import FormPanel, FormSection
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker

# (scheme as reported by the inspector, first Android release that checks it, note)
_SCHEMES: tuple[tuple[str, str, str], ...] = (
    ("v1 (JAR)", "all versions", ""),
    ("v2", "7.0+ (API 24)", ""),
    ("v3", "9+ (API 28)", "allows key rotation"),
    ("v3.1", "13+ (API 33)", ""),
    ("v4", "11+ (API 30)", "lives in a separate .idsig file"),
)
_UNCHECKABLE: str = "v4"  # not present inside the APK, so its status can't be read
_MONOSPACE_FIELDS: frozenset[str] = frozenset({"Serial number", "SHA-256", "SHA-1", "MD5"})


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
        self._render_schemes(security.signature_schemes)

        now = datetime.now(timezone.utc)
        total = len(security.certificates)
        for number, certificate in enumerate(security.certificates, start=1):
            self._render_certificate(number, total, certificate, now)
        if not total:
            self.add_section("Signing certificate").add_entry(
                "Certificate",
                "None found (unsigned APK)"
            )

        section = self.add_section("Permissions")
        section.add_list("Permissions", security.permissions)
        section.add_list("AppOps / Custom Perms", security.custom_permissions)

        section = self.add_section("Third-party Code")
        section.add_list("Libraries", third_party.libraries)
        section.add_list("Trackers", third_party.trackers)

    # --- Signature schemes ----------------------------------------------------------------------

    def _render_schemes(self, present: tuple[str, ...]) -> None:
        frame = self.add_section("Signature schemes").frame

        #frame.columnconfigure(4, weight=1)
        
        frame.columnconfigure(0, weight=1, uniform="col") 
        frame.columnconfigure(1, weight=1, uniform="col")
        frame.columnconfigure(2, weight=1, uniform="col")
        frame.columnconfigure(3, weight=2, uniform="col") # Más espacio para las notas
        
        for column, title in enumerate(("Scheme", "Status", "Android", "Note")):
            self.create_muted_label(frame, title).grid(
                row=0, column=column, sticky="w", padx=10, pady=(6, 4)
            )
        for index, (scheme, android, note) in enumerate(_SCHEMES):
            ttk.Separator(frame, orient="horizontal").grid(
                row=1 + 2 * index, column=0, columnspan=4, sticky="ew", padx=10
            )
            row = 2 + 2 * index
            ttk.Label(frame, text=scheme).grid(row=row, column=0, sticky="w", padx=10, pady=6)
            self.create_chip(frame, *self._status(scheme, present)).grid(
                row=row, column=1, sticky="w", padx=10
            )
            ttk.Label(frame, text=android).grid(row=row, column=2, sticky="w", padx=10)
            self.create_muted_label(frame, note).grid(row=row, column=3, sticky="w", padx=10)

    @staticmethod
    def _status(scheme: str, present: tuple[str, ...]) -> tuple[str, str]:
        if scheme == _UNCHECKABLE:
            return "Can't be checked", "muted"
        return ("Signed", "success") if scheme in present else ("Not signed", "neutral")

    # --- Certificates ----------------------------------------------------------------------------

    def _render_certificate(
        self, number: int, total: int, certificate: Certificate, now: datetime
    ) -> None:
        title = "Signing certificate" if total == 1 else f"Signing certificate {number} of {total}"
        section = self.add_section(title, self._validity_badge(certificate, now))
        if not certificate.is_readable:
            section.add_entry("Certificate", certificate.as_text())
            return

        groups = (
            ("Identity", (
                ("Subject", certificate.subject),
                ("Issuer", certificate.issuer),
                ("Serial number", certificate.serial_number),
            )),
            ("Validity", (
                ("Valid from", certificate.valid_from_text()),
                ("Valid until", certificate.valid_until_text()),
            )),
            ("Key", (
                ("Public key", certificate.public_key),
                ("Signature", certificate.signature_algorithm),
            )),
            ("Fingerprints", (
                ("SHA-256", certificate.sha256),
                ("SHA-1", certificate.sha1),
                ("MD5", certificate.md5),
            )),
        )
        for group_title, rows in groups:
            self._add_group(section, group_title, rows)

    @staticmethod
    def _add_group(
        section: FormSection,
        title: str,
        rows: tuple[tuple[str, str | None], ...]
    ) -> None:
        readable = [(label, value) for label, value in rows if value]
        if not readable:
            return
        section.add_group(title)
        for label, value in readable:
            section.add_entry(label, value, monospace=label in _MONOSPACE_FIELDS)

    @staticmethod
    def _validity_badge(certificate: Certificate, now: datetime) -> tuple[str, str] | None:
        if certificate.valid_until is None:
            return None
        if certificate.is_expired(now):
            return "expired", "danger"
        return f"valid until {certificate.valid_until.year}", "success"
