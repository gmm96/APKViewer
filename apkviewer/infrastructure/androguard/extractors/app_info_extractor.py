"""
Extracts general app metadata (name, package, version, SDK range, ABIs).
"""

from typing import Any

from androguard.core.apk import APK

from apkviewer.infrastructure.androguard.analysis_section_extractor import AnalysisSectionExtractor


class AppInfoExtractor(AnalysisSectionExtractor):
    def extract(self, apk: APK) -> dict[str, Any]:
        archs = {
            f.split("/")[1]
            for f in apk.get_files()
            if f.startswith("lib/") and len(f.split("/")) > 1
        }
        return {
            "App name": apk.get_app_name(),
            "Package name": apk.get_package(),
            "Version": apk.get_androidversion_name(),
            "Version code": apk.get_androidversion_code(),
            "Split / Multidex": "Yes" if apk.is_multidex() else "No",
            "Architectures": ", ".join(archs) if archs else "None / Unknown",
            "Min SDK": apk.get_min_sdk_version(),
            "Target SDK": apk.get_target_sdk_version(),
            "Max SDK": apk.get_max_sdk_version(),
            "Effective SDK": apk.get_effective_target_sdk_version(),
        }
