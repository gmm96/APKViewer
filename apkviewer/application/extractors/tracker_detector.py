"""
Scans DEX class packages for known analytics/ads/SDK signatures.
"""

from androguard.core.apk import APK
from androguard.core.dex import DEX

from apkviewer.config.trackers import KNOWN_TRACKERS
from apkviewer.domain.interfaces.analysis_section_extractor import AnalysisSectionExtractor


class TrackerDetector(AnalysisSectionExtractor):
    def __init__(self, tracker_signatures: dict[str, str] | None = None):
        self._tracker_signatures = tracker_signatures or KNOWN_TRACKERS

    def extract(self, apk: APK) -> dict[str, list[str]]:
        packages = self._collect_dex_packages(apk)
        trackers = {
            f"{tracker_name} (Found in: {pkg})"
            for pkg in packages
            for key, tracker_name in self._tracker_signatures.items()
            if key in pkg.lower()
        }
        return {
            "Hardware Features": apk.get_features(),
            "Libraries": apk.get_libraries(),
            "Trackers": sorted(trackers),
        }

    @staticmethod
    def _collect_dex_packages(apk: APK) -> set[str]:
        packages = set()
        for dex_bytes in apk.get_all_dex():
            try:
                for cls in DEX(dex_bytes).get_classes():
                    name = getattr(cls, "name", None)
                    if name is None:
                        name = cls.get_name()
                    parts = str(name).lstrip("L").split("/")
                    if len(parts) > 1:
                        packages.add(".".join(parts[:3] if len(parts) > 3 else parts[:-1]))
            except Exception:
                pass
        return packages
