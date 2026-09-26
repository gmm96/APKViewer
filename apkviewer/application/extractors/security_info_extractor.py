"""
Extracts permissions, custom app-ops and signing certificate info.
"""

from typing import Any

from androguard.core.apk import APK

from apkviewer.domain.interfaces import AnalysisSectionExtractor


class SecurityInfoExtractor(AnalysisSectionExtractor):
    def extract(self, apk: APK) -> dict[str, Any]:
        perms, appops = [], []
        for p in apk.get_permissions():
            (perms if p.startswith("android.permission.") else appops).append(p)

        certs = []
        for cert in apk.get_certificates():
            try:
                certs.append(f"Issuer: {cert.issuer.human_friendly}\nSubject: {cert.subject.human_friendly}")
            except Exception:
                certs.append("Unknown / Encrypted Certificate")

        return {
            "Permissions": sorted(perms),
            "AppOps / Custom Perms": sorted(appops),
            "Certificates": certs,
        }
