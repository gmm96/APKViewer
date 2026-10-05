"""
Formats an analysis as plain, human-readable text suitable for saving into
a .txt file. Each section is written explicitly from its entity.
"""

from collections.abc import Sequence
from datetime import datetime

from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.domain.entities.application_info import ApplicationInfo
from apkviewer.domain.entities.component_kind import ComponentKind
from apkviewer.domain.entities.components import Component, DeclaredComponents
from apkviewer.domain.entities.configuration_info import ConfigurationInfo
from apkviewer.domain.entities.embedded_content import EmbeddedContent
from apkviewer.domain.entities.exported_intent import ExportedIntent
from apkviewer.domain.entities.security_info import SecurityInfo
from apkviewer.domain.entities.third_party_info import ThirdPartyInfo
from apkviewer.domain.interfaces.date_formatter import DateFormatter
from apkviewer.domain.interfaces.size_formatter import SizeFormatter


class AppInfoSerializer:
    _INDENT: str = "  "

    def __init__(
        self,
        size_formatter: SizeFormatter | None = None,
        date_formatter: DateFormatter | None = None,
    ) -> None:
        self._size_formatter: SizeFormatter | None = size_formatter
        self._date_formatter: DateFormatter | None = date_formatter

    def format(self, result: AnalysisResult) -> str:
        inspection = result.inspection
        blocks = [
            self._application(inspection.application),
            self._configuration(inspection.configuration),
            self._embedded_content(inspection.embedded_content),
            self._security(inspection.security),
            self._third_party(inspection.third_party),
            self._components(inspection.components),
            self._intents(inspection.components.exported_intents()),
        ]
        if inspection.warnings:
            blocks.append(
                self._block(
                    "Analysis warnings",
                    [f"- [{warning.area.value}] {warning.message}" for warning in inspection.warnings],
                )
            )
        return "\n\n".join(blocks) + "\n"

    # --- Sections ------------------------------------------------------------

    def _application(self, info: ApplicationInfo) -> str:
        lines = [
            f"App Name: {info.app_name}",
            f"Package Name: {info.package_name}",
            f"Version Name: {self._text(info.version_name)}",
            f"Version Code: {self._text(info.version_code)}",
            f"Min SDK: {self._text(info.min_sdk)}",
            f"Target SDK: {self._text(info.target_sdk)}",
        ]
        if info.max_sdk:
            lines.append(f"Max SDK: {info.max_sdk}")
        lines += [
            f"File Name: {self._text(info.file_name, 'Unknown')}",
            f"File Path: {self._text(info.file_path, 'Unknown')}",
            f"File Size: {self._size(info.file_size)}",
            f"Last Modified: {self._date(info.last_modified)}",
        ]
        return self._block("Application", lines)

    def _configuration(self, info: ConfigurationInfo) -> str:
        architectures = ", ".join(info.architectures) or "None / Unknown (Java only)"
        lines = [f"Architectures: {architectures}"]
        lines += self._list(
            "Hardware Requirements", [feature.as_text() for feature in info.hardware_requirements]
        )
        lines += self._list("Supported Locales", info.locales)
        lines += self._list("Screen Densities", info.screen_densities)
        return self._block("Configuration", lines)

    def _embedded_content(self, info: EmbeddedContent) -> str:
        return self._block("Embedded Content", self._list("Discovered URLs", info.urls))

    def _security(self, info: SecurityInfo) -> str:
        lines = [f"Signature schemes: {', '.join(info.signature_schemes) or 'None (unsigned)'}"]
        lines += self._list("Permissions", info.permissions)
        lines += self._list("AppOps / Custom Perms", info.custom_permissions)
        lines += self._list("Certificates", [cert.as_text() for cert in info.certificates])
        return self._block("Permissions & Signing", lines)

    def _third_party(self, info: ThirdPartyInfo) -> str:
        lines = self._list("Libraries", info.libraries)
        lines += self._list("Trackers", info.trackers)
        return self._block("Third-party Code", lines)

    def _components(self, info: DeclaredComponents) -> str:
        groups = (
            ("Activities", (ComponentKind.ACTIVITY, ComponentKind.ACTIVITY_ALIAS)),
            ("Services", (ComponentKind.SERVICE,)),
            ("Receivers", (ComponentKind.RECEIVER,)),
            ("Providers", (ComponentKind.PROVIDER,)),
        )
        lines: list[str] = []
        for label, kinds in groups:
            lines += self._list(label, self._names(info.of_kind(*kinds)))
        return self._block("Declared Components", lines)

    def _intents(self, intents: Sequence[ExportedIntent]) -> str:
        items = [self._intent_text(intent) for intent in intents]
        return self._block("Exported Intents", self._list("Intent Actions", items))

    # --- Helpers ---------------------------------------------------------------

    @staticmethod
    def _block(title: str, lines: list[str]) -> str:
        return "\n".join([title, "=" * len(title), *lines])

    def _list(self, label: str, items: Sequence[str]) -> list[str]:
        lines = [f"{label} ({len(items)}):"]
        if not items:
            lines.append(f"{self._INDENT}None found")
        for item in items:
            # Items such as certificates or intents span several lines: keep them aligned.
            item_lines = str(item).splitlines() or [""]
            lines.append(f"{self._INDENT}- {item_lines[0]}")
            lines.extend(f"{self._INDENT}  {extra}" for extra in item_lines[1:])
        return lines

    @staticmethod
    def _names(components: Sequence[Component]) -> list[str]:
        return [component.name for component in components]

    @staticmethod
    def _intent_text(intent: ExportedIntent) -> str:
        lines = [intent.name, f"Component: {intent.component_kind.value} {intent.component_name}"]
        if intent.categories:
            lines.append("Categories: " + ", ".join(intent.categories))
        for data in intent.data:
            lines.append("Data: " + ", ".join(f"{key}='{value}'" for key, value in data.as_pairs()))
        if intent.auto_verify:
            lines.append("Auto-verify: yes")
        return "\n".join(lines)

    @staticmethod
    def _text(value: object, default: str = "") -> str:
        return default if value is None else str(value)

    def _size(self, size: int | None) -> str:
        if size is None:
            return "Unknown"
        return self._size_formatter.format(size, True) if self._size_formatter else str(size)

    def _date(self, value: datetime | None) -> str:
        if value is None:
            return "Unknown"
        return self._date_formatter.format(value) if self._date_formatter else str(value)
