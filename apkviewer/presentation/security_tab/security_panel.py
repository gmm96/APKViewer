"""
"Security" tab: permissions, app-ops, signing certificates, trackers and
third-party libraries.
"""

from tkinter import ttk

from apkviewer.domain.entities.security_info import SecurityInfo
from apkviewer.domain.entities.third_party_info import ThirdPartyInfo
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.form_panel import FormPanel
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker


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
        section.add_list("Permissions", security.permissions)
        section.add_list("AppOps / Custom Perms", security.custom_permissions)
        section.add_list(
            "Certificates",
            [certificate.as_text() for certificate in security.certificates],
            separator="\n\n",
        )

        section = self.add_section("Third-party Code")
        section.add_list("Libraries", third_party.libraries)
        section.add_list("Trackers", third_party.trackers)
