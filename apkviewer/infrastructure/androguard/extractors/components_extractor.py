"""
Extracts the components declared by the APK (activities, services,
receivers and providers).
"""

from typing import Any

from androguard.core.apk import APK

from apkviewer.infrastructure.androguard.analysis_section_extractor import AnalysisSectionExtractor


class ComponentsExtractor(AnalysisSectionExtractor):
    def extract(self, apk: APK) -> dict[str, Any]:
        return {
            "Activities": sorted(apk.get_activities()),
            "Services": sorted(apk.get_services()),
            "Receivers": sorted(apk.get_receivers()),
            "Providers": sorted(apk.get_providers()),
        }
