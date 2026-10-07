"""
Signing certificates and signature schemes of an APK.
"""

from dataclasses import dataclass
from datetime import datetime, timezone


def _utc_text(moment: datetime) -> str:
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc)
    return moment.strftime("%Y-%m-%d %H:%M:%S UTC")


@dataclass(frozen=True)
class Certificate:
    """A signing certificate. Every field is None when it could not be read."""
    issuer: str | None
    subject: str | None
    serial_number: str | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    signature_algorithm: str | None = None  # e.g. "SHA256withRSA"
    public_key: str | None = None           # e.g. "RSA 2048-bit"
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    @property
    def is_readable(self) -> bool:
        return self.issuer is not None or self.subject is not None

    def is_expired(self, now: datetime) -> bool:
        return self.valid_until is not None and self.valid_until < now

    def valid_from_text(self) -> str | None:
        return _utc_text(self.valid_from) if self.valid_from else None

    def valid_until_text(self, now: datetime | None = None) -> str | None:
        if self.valid_until is None:
            return None
        text = _utc_text(self.valid_until)
        expired = now is not None and self.is_expired(now if now.tzinfo else now.replace(tzinfo=timezone.utc))
        return f"{text} (expired)" if expired else text

    def fields(self, now: datetime | None = None) -> list[tuple[str, str]]:
        """(label, value) of every field that could be read, in display order."""
        candidates = (
            ("Subject", self.subject),
            ("Issuer", self.issuer),
            ("Serial number", self.serial_number),
            ("Valid from", self.valid_from_text()),
            ("Valid until", self.valid_until_text(now)),
            ("Public key", self.public_key),
            ("Signature algorithm", self.signature_algorithm),
            ("SHA-256", self.sha256),
            ("SHA-1", self.sha1),
            ("MD5", self.md5),
        )
        return [(label, value) for label, value in candidates if value]

    def as_text(self) -> str:
        if not self.is_readable:
            return "Unknown / Encrypted Certificate"
        return "\n".join(f"{label}: {value}" for label, value in self.fields())


@dataclass(frozen=True)
class SecurityInfo:
    certificates: tuple[Certificate, ...]
    # APK signature schemes present, e.g. ("v1 (JAR)", "v2", "v3"). v4 lives in a separate
    # .idsig file, so it can't be detected from the APK alone.
    signature_schemes: tuple[str, ...] = ()
