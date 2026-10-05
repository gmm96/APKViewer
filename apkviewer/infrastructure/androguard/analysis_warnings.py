"""
Collects the warnings raised by the extractors while one APK is analyzed.
"""

from apkviewer.domain.entities.analysis_warning import AnalysisArea, AnalysisWarning


class AnalysisWarningCollector:
    def __init__(self) -> None:
        self._warnings: list[AnalysisWarning] = []

    def add(self, message: str, *areas: AnalysisArea) -> None:
        for area in areas:
            warning = AnalysisWarning(area, message)
            if warning not in self._warnings:
                self._warnings.append(warning)

    def as_tuple(self) -> tuple[AnalysisWarning, ...]:
        return tuple(self._warnings)
