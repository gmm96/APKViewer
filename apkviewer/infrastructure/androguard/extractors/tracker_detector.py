"""
Scans DEX class packages for known analytics/ads/SDK signatures and lists
the third-party libraries declared by the APK.
"""

from androguard.core.apk import APK

from apkviewer.domain.entities.third_party_info import ThirdPartyInfo
from apkviewer.infrastructure.androguard.config.trackers import KNOWN_TRACKERS
from apkviewer.infrastructure.androguard.dex_reader import DexContents


class TrackerDetector:
    def __init__(self, tracker_signatures: dict[str, str] | None = None) -> None:
        self._tracker_signatures: dict[str, str] = tracker_signatures or KNOWN_TRACKERS

    def extract(self, apk: APK, dex: DexContents) -> ThirdPartyInfo:
        packages = self._collect_packages(dex)
        trackers = {
            f"{tracker_name} (Found in: {pkg})"
            for pkg in packages
            for key, tracker_name in self._tracker_signatures.items()
            if key in pkg.lower()
        }
        return ThirdPartyInfo(
            libraries=tuple(sorted(apk.get_libraries())),
            trackers=tuple(sorted(trackers)),
        )

    @staticmethod
    def _collect_packages(dex: DexContents) -> set[str]:
        packages = set()
        for name in dex.class_names:
            parts = name.removeprefix("L").split("/")
            if len(parts) > 1:
                packages.add(".".join(parts[:3] if len(parts) > 3 else parts[:-1]))
        return packages
