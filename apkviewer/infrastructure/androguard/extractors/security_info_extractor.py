"""
Extracts permissions, custom app-ops and signing certificate info.
"""

from typing import Any

from androguard.core.apk import APK

from apkviewer.domain.entities.security_info import Certificate, SecurityInfo


class SecurityInfoExtractor:
    def extract(self, apk: APK) -> SecurityInfo:
        perms: list[str] = []
        appops: list[str] = []
        for permission in apk.get_permissions():
            (perms if permission.startswith("android.permission.") else appops).append(permission)

        return SecurityInfo(
            permissions=tuple(sorted(perms)),
            custom_permissions=tuple(sorted(appops)),
            certificates=tuple(self._to_certificate(cert) for cert in apk.get_certificates()),
        )

    @staticmethod
    def _to_certificate(cert: Any) -> Certificate:
        try:
            return Certificate(
                issuer=cert.issuer.human_friendly,
                subject=cert.subject.human_friendly,
            )
        except Exception:
            return Certificate(issuer=None, subject=None)
