"""
Androguard-backed implementation of the ApkInspector port. It loads the
APK once, reads its DEX files once, runs every extractor and maps their
results into a single ApkInspection entity.
"""

from loguru import logger

from apkviewer.domain.entities.apk_inspection import ApkInspection
from apkviewer.domain.interfaces.apk_inspector import ApkInspector
from apkviewer.infrastructure.androguard.apk_loader import ApkLoader
from apkviewer.infrastructure.androguard.dex_reader import DexReader
from apkviewer.infrastructure.androguard.extractors.app_info_extractor import ApplicationInfoExtractor
from apkviewer.infrastructure.androguard.extractors.components_extractor import ComponentsExtractor
from apkviewer.infrastructure.androguard.extractors.configuration_extractor import ConfigurationExtractor
from apkviewer.infrastructure.androguard.extractors.embedded_content_extractor import EmbeddedContentExtractor
from apkviewer.infrastructure.androguard.extractors.security_info_extractor import SecurityInfoExtractor
from apkviewer.infrastructure.androguard.extractors.tracker_detector import TrackerDetector
from apkviewer.infrastructure.androguard.icon_extractor import IconExtractor
from apkviewer.infrastructure.androguard.manifest_formatter import ManifestFormatter

logger.disable("androguard")  # it logs thousands of DEBUG lines per APK


class AndroguardApkInspector(ApkInspector):
    def __init__(
        self,
        apk_loader: ApkLoader | None = None,
        dex_reader: DexReader | None = None,
        icon_extractor: IconExtractor | None = None,
        manifest_formatter: ManifestFormatter | None = None,
        application_extractor: ApplicationInfoExtractor | None = None,
        configuration_extractor: ConfigurationExtractor | None = None,
        embedded_content_extractor: EmbeddedContentExtractor | None = None,
        security_extractor: SecurityInfoExtractor | None = None,
        tracker_detector: TrackerDetector | None = None,
        components_extractor: ComponentsExtractor | None = None,
    ) -> None:
        self._apk_loader = apk_loader or ApkLoader()
        self._dex_reader = dex_reader or DexReader()
        self._icon_extractor = icon_extractor or IconExtractor()
        self._manifest_formatter = manifest_formatter or ManifestFormatter()
        self._application = application_extractor or ApplicationInfoExtractor()
        self._configuration = configuration_extractor or ConfigurationExtractor()
        self._embedded_content = embedded_content_extractor or EmbeddedContentExtractor()
        self._security = security_extractor or SecurityInfoExtractor()
        self._trackers = tracker_detector or TrackerDetector()
        self._components = components_extractor or ComponentsExtractor()

    def inspect(self, apk_path: str) -> ApkInspection:
        apk = self._apk_loader.load(apk_path)
        dex = self._dex_reader.read(apk)  # shared by every extractor that needs the code
        return ApkInspection(
            application=self._application.extract(apk),
            configuration=self._configuration.extract(apk),
            embedded_content=self._embedded_content.extract(dex),
            security=self._security.extract(apk),
            third_party=self._trackers.extract(apk, dex),
            components=self._components.extract(apk),
            icon_png=self._icon_extractor.extract(apk),
            manifest_xml=self._manifest_formatter.format(apk),
        )
