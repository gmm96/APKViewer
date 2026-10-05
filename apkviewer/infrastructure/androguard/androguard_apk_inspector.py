"""
Androguard-backed implementation of the ApkInspector port. It loads the
APK once, reads its DEX files once, runs every extractor and maps their
results into a single ApkInspection entity.

Each extractor runs guarded: if one of them fails, the rest of the
analysis still completes and a warning says what is missing, instead of
the whole APK being rejected or the section silently coming up empty.
"""

from collections.abc import Callable
from typing import TypeVar

from loguru import logger

from apkviewer.domain.entities.analysis_warning import AnalysisArea
from apkviewer.domain.entities.apk_inspection import ApkInspection
from apkviewer.domain.entities.application_info import ApplicationInfo
from apkviewer.domain.entities.components import DeclaredComponents
from apkviewer.domain.entities.configuration_info import ConfigurationInfo
from apkviewer.domain.entities.embedded_content import EmbeddedContent
from apkviewer.domain.entities.security_info import SecurityInfo
from apkviewer.domain.entities.third_party_info import ThirdPartyInfo
from apkviewer.domain.interfaces.apk_inspector import ApkInspector
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.apk_loader import ApkLoader
from apkviewer.infrastructure.androguard.dex_reader import DexContents, DexReader
from apkviewer.infrastructure.androguard.extractors.app_info_extractor import ApplicationInfoExtractor
from apkviewer.infrastructure.androguard.extractors.components_extractor import ComponentsExtractor
from apkviewer.infrastructure.androguard.extractors.configuration_extractor import ConfigurationExtractor
from apkviewer.infrastructure.androguard.extractors.embedded_content_extractor import EmbeddedContentExtractor
from apkviewer.infrastructure.androguard.extractors.security_info_extractor import SecurityInfoExtractor
from apkviewer.infrastructure.androguard.extractors.tracker_detector import TrackerDetector
from apkviewer.infrastructure.androguard.icon_extractor import IconExtractor
from apkviewer.infrastructure.androguard.manifest_formatter import ManifestFormatter

logger.disable("androguard")  # it logs thousands of DEBUG lines per APK

T = TypeVar("T")


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
        warnings = AnalysisWarningCollector()
        apk = self._apk_loader.load(apk_path)  # an APK that can't even be opened is a real error
        guard = self._guarded

        info, sec, comp = AnalysisArea.INFO, AnalysisArea.SECURITY, AnalysisArea.COMPONENTS
        dex = guard(warnings, "The code (DEX) of the app", (info, sec),
                    lambda: self._dex_reader.read(apk, warnings), DexContents())
        return ApkInspection(
            application=guard(
                warnings, "The application data", (info,),
                lambda: self._application.extract(apk),
                ApplicationInfo("", "", None, None, None, None, None, None, None, None, None),
            ),
            configuration=guard(
                warnings, "The configuration", (info,),
                lambda: self._configuration.extract(apk, warnings),
                ConfigurationInfo((), (), (), ()),
            ),
            embedded_content=guard(
                warnings, "The embedded content", (info,),
                lambda: self._embedded_content.extract(dex), EmbeddedContent(()),
            ),
            security=guard(
                warnings, "The permissions and signatures", (sec,),
                lambda: self._security.extract(apk, warnings), SecurityInfo((), (), ()),
            ),
            third_party=guard(
                warnings, "The third-party code", (sec,),
                lambda: self._trackers.extract(apk, dex), ThirdPartyInfo((), ()),
            ),
            components=guard(
                warnings, "The components", (comp,),
                lambda: self._components.extract(apk, warnings), DeclaredComponents(),
            ),
            icon_png=guard(
                warnings, "The icon", (AnalysisArea.ICON,),
                lambda: self._icon_extractor.extract(apk, warnings), None,
            ),
            manifest_xml=guard(
                warnings, "The manifest", (comp,),
                lambda: self._manifest_formatter.format(apk), "",
            ),
            warnings=warnings.as_tuple(),
        )

    @staticmethod
    def _guarded(
        warnings: AnalysisWarningCollector,
        what: str,
        areas: tuple[AnalysisArea, ...],
        read: Callable[[], T],
        default: T,
    ) -> T:
        try:
            return read()
        except Exception as exc:  # pylint: disable=broad-except
            warnings.add(f"{what} could not be read ({type(exc).__name__}: {exc}).", *areas)
            return default
