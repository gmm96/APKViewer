"""
Extracts the app dashboard data: identity, versions, SDK range,
architectures and hardware features.
"""

from typing import Any

from androguard.core.apk import APK

from apkviewer.infrastructure.androguard.analysis_section_extractor import AnalysisSectionExtractor


class AppInfoExtractor(AnalysisSectionExtractor):
    def extract(self, apk: APK) -> dict[str, Any]:
        return {
            "App name": apk.get_app_name(),
            "Package name": apk.get_package(),
            "Version": apk.get_androidversion_name(),
            "Version code": apk.get_androidversion_code(),
            "Min SDK": apk.get_min_sdk_version(),
            "Target SDK": apk.get_target_sdk_version(),
            "Architectures": self._format_architectures(apk),
            "Hardware Features": sorted(apk.get_features()),
        }

    @staticmethod
    def _format_architectures(apk: APK) -> str:
        archs = {
            parts[1]
            for parts in (f.split("/") for f in apk.get_files() if f.startswith("lib/"))
            if len(parts) > 2
        }
        return ", ".join(sorted(archs)) if archs else "None / Unknown"
