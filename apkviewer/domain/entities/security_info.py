"""
Permissions and signing certificates declared by an APK.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Certificate:
    """A signing certificate; both fields are None when it could not be read."""
    issuer: str | None
    subject: str | None

    def as_text(self) -> str:
        if self.issuer is None or self.subject is None:
            return "Unknown / Encrypted Certificate"
        return f"Issuer: {self.issuer}\nSubject: {self.subject}"


@dataclass(frozen=True)
class SecurityInfo:
    permissions: tuple[str, ...]
    custom_permissions: tuple[str, ...]
    certificates: tuple[Certificate, ...]
