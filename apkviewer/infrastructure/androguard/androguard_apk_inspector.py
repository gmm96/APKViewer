"""
Androguard-backed implementation of the ApkInspector port: loads the APK
once and runs every section extractor, the icon extractor and the manifest
formatter against it.
"""

from apkviewer.domain.entities.analysis_labels import (
    SECTION_APPLICATION,
    SECTION_CONFIGURATION,
    SECTION_EMBEDDED_CONTENT,
    SECTION_COMPONENTS,
    SECTION_INTENTS,
    SECTION_SECURITY,
    SECTION_THIRD_PARTY,
)
from apkviewer.domain.entities.apk_inspection import ApkInspection
from apkviewer.domain.interfaces.apk_inspector import ApkInspector
from apkviewer.infrastructure.androguard.analysis_section_extractor import AnalysisSectionExtractor
from apkviewer.infrastructure.androguard.apk_loader import ApkLoader
from apkviewer.infrastructure.androguard.extractors.app_info_extractor import ApplicationInfoExtractor
from apkviewer.infrastructure.androguard.extractors.configuration_extractor import ConfigurationExtractor
from apkviewer.infrastructure.androguard.extractors.embedded_content_extractor import EmbeddedContentExtractor
from apkviewer.infrastructure.androguard.extractors.components_extractor import ComponentsExtractor
from apkviewer.infrastructure.androguard.extractors.intent_actions_extractor import IntentActionsExtractor
from apkviewer.infrastructure.androguard.extractors.security_info_extractor import SecurityInfoExtractor
from apkviewer.infrastructure.androguard.extractors.tracker_detector import TrackerDetector
from apkviewer.infrastructure.androguard.icon_extractor import IconExtractor
from apkviewer.infrastructure.androguard.manifest_formatter import ManifestFormatter


class AndroguardApkInspector(ApkInspector):
    def __init__(
        self,
        apk_loader: ApkLoader | None = None,
        icon_extractor: IconExtractor | None = None,
        manifest_formatter: ManifestFormatter | None = None,
        section_extractors: dict[str, AnalysisSectionExtractor] | None = None,
    ) -> None:
        self._apk_loader: ApkLoader = apk_loader or ApkLoader()
        self._icon_extractor: IconExtractor = icon_extractor or IconExtractor()
        self._manifest_formatter: ManifestFormatter = manifest_formatter or ManifestFormatter()
        self._section_extractors: dict[str, AnalysisSectionExtractor] = (
            section_extractors or self._default_section_extractors()
        )

    @staticmethod
    def _default_section_extractors() -> dict[str, AnalysisSectionExtractor]:
        return {
            SECTION_APPLICATION: ApplicationInfoExtractor(),
            SECTION_CONFIGURATION: ConfigurationExtractor(),
            SECTION_EMBEDDED_CONTENT: EmbeddedContentExtractor(),
            SECTION_SECURITY: SecurityInfoExtractor(),
            SECTION_THIRD_PARTY: TrackerDetector(),
            SECTION_COMPONENTS: ComponentsExtractor(),
            SECTION_INTENTS: IntentActionsExtractor(),
        }

    def inspect(self, apk_path: str) -> ApkInspection:
        apk = self._apk_loader.load(apk_path)
        return ApkInspection(
            package_name=apk.get_package() or "",
            app_name=apk.get_app_name() or "",
            icon_png=self._icon_extractor.extract(apk),
            sections={
                title: extractor.extract(apk) for title, extractor in self._section_extractors.items()
            },
            manifest_xml=self._manifest_formatter.format(apk),
        )
