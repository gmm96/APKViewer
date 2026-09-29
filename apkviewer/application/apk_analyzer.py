"""
Composition root for the analysis use case: wires an APK loader, an icon
extractor and a set of section extractors together, and exposes a single
`analyze()` entry point. Every dependency can be overridden by the caller
(constructor injection), which is what makes this class unit-testable
without touching real APK files.
"""

from apkviewer.domain.entities.analysis_result import AnalysisResult
from apkviewer.domain.interfaces.analysis_section_extractor import AnalysisSectionExtractor
from apkviewer.infrastructure.androguard.apk_loader import ApkLoader

from .extractors.app_info_extractor import AppInfoExtractor
from .extractors.components_extractor import ComponentsExtractor
from .extractors.security_info_extractor import SecurityInfoExtractor
from .extractors.tracker_detector import TrackerDetector

from .icon_extractor import IconExtractor


class ApkAnalyzer:
    def __init__(
        self,
        apk_loader: ApkLoader | None = None,
        icon_extractor: IconExtractor | None = None,
        section_extractors: dict[str, AnalysisSectionExtractor] | None = None,
    ) -> None:
        self._apk_loader: ApkLoader = apk_loader or ApkLoader()
        self._icon_extractor: IconExtractor = icon_extractor or IconExtractor()
        self._section_extractors: dict[str, AnalysisSectionExtractor] = section_extractors or self._default_section_extractors()

    @staticmethod
    def _default_section_extractors() -> dict[str, AnalysisSectionExtractor]:
        return {
            "App Information": AppInfoExtractor(),
            "Security & Operations": SecurityInfoExtractor(),
            "Components & Intents": ComponentsExtractor(),
            "Extras & Libraries": TrackerDetector(),
        }

    def analyze(self, apk_path: str) -> AnalysisResult:
        apk = self._apk_loader.load(apk_path)
        sections = {
            title: extractor.extract(apk)
            for title, extractor in self._section_extractors.items()
        }
        icon = self._icon_extractor.extract(apk)
        return AnalysisResult(apk=apk, icon=icon, sections=sections)
