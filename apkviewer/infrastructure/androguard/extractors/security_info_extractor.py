"""
Extracts the signing certificates and the APK signature schemes in use.
"""

import hashlib
from datetime import datetime
from typing import Any

from androguard.core.apk import APK

from apkviewer.domain.entities.analysis_warning import AnalysisArea
from apkviewer.domain.entities.security_info import Certificate, SecurityInfo
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector


class SecurityInfoExtractor:
    # (label shown, androguard method). v3.1 only exists in recent androguard versions.
    _SCHEMES: tuple[tuple[str, str], ...] = (
        ("v1 (JAR)", "is_signed_v1"),
        ("v2", "is_signed_v2"),
        ("v3", "is_signed_v3"),
        ("v3.1", "is_signed_v31"),
    )

    def extract(self, apk: APK, warnings: AnalysisWarningCollector | None = None) -> SecurityInfo:
        return SecurityInfo(
            certificates=tuple(self._to_certificate(cert) for cert in apk.get_certificates()),
            signature_schemes=self._signature_schemes(apk, warnings),
        )

    def _signature_schemes(
        self, apk: APK, warnings: AnalysisWarningCollector | None
    ) -> tuple[str, ...]:
        found: list[str] = []
        for label, method_name in self._SCHEMES:
            method = getattr(apk, method_name, None)
            if method is None:
                continue
            try:
                if method():
                    found.append(label)
            except Exception as exc:
                if warnings is not None:
                    warnings.add(
                        f"The {label} signature could not be checked ({type(exc).__name__}).",
                        AnalysisArea.SECURITY,
                    )
        return tuple(found)

    @classmethod
    def _to_certificate(cls, cert: Any) -> Certificate:
        """Each field is read on its own: one unreadable detail must not hide the others."""
        der = cls._attempt(cert.dump)
        validity = cls._attempt(lambda: cert["tbs_certificate"]["validity"])
        return Certificate(
            issuer=cls._attempt(lambda: cert.issuer.human_friendly),
            subject=cls._attempt(lambda: cert.subject.human_friendly),
            serial_number=cls._attempt(lambda: f"{cert.serial_number:X}"),
            md5=cls._fingerprint("md5", der),
            sha1=cls._fingerprint("sha1", der),
            sha256=cls._fingerprint("sha256", der),
            signature_algorithm=cls._attempt(lambda: cls._signature_algorithm(cert)),
            public_key=cls._attempt(lambda: cls._public_key(cert)),
            valid_from=cls._attempt(lambda: cls._moment(validity["not_before"])),
            valid_until=cls._attempt(lambda: cls._moment(validity["not_after"])),
        )

    @staticmethod
    def _attempt(read: Any) -> Any:
        try:
            return read()
        except Exception:
            return None

    @staticmethod
    def _fingerprint(algorithm: str, der: bytes | None) -> str | None:
        if not der:
            return None
        digest = hashlib.new(algorithm, der).hexdigest().upper()
        return ":".join(digest[i:i + 2] for i in range(0, len(digest), 2))

    @staticmethod
    def _moment(value: Any) -> datetime | None:
        moment = value.native
        return moment if isinstance(moment, datetime) else None

    @staticmethod
    def _signature_algorithm(cert: Any) -> str:
        scheme = {"rsassa_pkcs1v15": "RSA", "rsassa_pss": "RSASSA-PSS", "ecdsa": "ECDSA", "dsa": "DSA"}
        return f"{cert.hash_algo.upper()}with{scheme.get(cert.signature_algo, cert.signature_algo.upper())}"

    @staticmethod
    def _public_key(cert: Any) -> str:
        key = cert.public_key
        name = {"rsa": "RSA", "ec": "EC", "dsa": "DSA"}.get(key.algorithm, key.algorithm.upper())
        text = f"{name} {key.bit_size}-bit"
        if key.algorithm == "ec":
            curve = key.curve
            text += f" ({curve[1] if isinstance(curve, tuple) else curve})"
        return text
