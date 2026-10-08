"""
Permissions an APK requests or declares, split the way the UI shows them:
framework permissions, "app op" permissions (special access the user grants
from Settings) and custom permissions (anything Android itself doesn't define).
"""

from dataclasses import dataclass
from enum import Enum

_BASE_LEVELS: dict[int, str] = {0: "normal", 1: "dangerous", 2: "signature", 3: "signatureOrSystem"}
_LEVEL_FLAGS: tuple[tuple[int, str], ...] = (
    (0x10, "privileged"), (0x20, "development"), (0x40, "appop"), (0x80, "pre23"),
    (0x100, "installer"), (0x200, "verifier"), (0x400, "preinstalled"), (0x800, "setup"),
    (0x1000, "instant"), (0x2000, "runtime"), (0x4000, "oem"), (0x8000, "vendorPrivileged"),
)
_LEVEL_TITLES: dict[str, str] = {
    "normal": "Normal",
    "dangerous": "Dangerous",
    "signature": "Signature",
    "signatureorsystem": "Signature or system",
}


def parse_protection_level(raw: str | None) -> str | None:
    """
    Normalize a protection level to the 'base|flag|flag' form Android documents.
    Accepts that form already, or the number a compiled manifest stores
    (e.g. '0x00000012' -> 'signature|privileged'). None if it can't be read.
    """
    if raw is None or not raw.strip():
        return None
    text = raw.strip()
    try:
        value = int(text, 0)
    except ValueError:
        return text  # already names
    base = _BASE_LEVELS.get(value & 0xF)
    if base is None:
        return None
    flags = [name for bit, name in _LEVEL_FLAGS if value & bit]
    return "|".join([base, *flags])


def protection_text(protection: str | None) -> str:
    """Readable form: 'Dangerous', 'Signature (privileged, appop)', 'Unknown'."""
    if not protection:
        return "Unknown"
    tokens = protection.split("|")
    base = next((token for token in tokens if token.lower() in _LEVEL_TITLES), None)
    if base is None:
        return protection
    flags = [token for token in tokens if token != base]
    title = _LEVEL_TITLES[base.lower()]
    return f"{title} ({', '.join(flags)})" if flags else title


class PermissionOrigin(Enum):
    REQUESTED = "Requested"
    DECLARED = "Declared by this app"
    DECLARED_AND_REQUESTED = "Declared and requested"


@dataclass(frozen=True)
class Permission:
    name: str
    protection: str | None = None  # None when nothing defines it
    label: str | None = None       # short summary of what it allows
    max_sdk: str | None = None     # maxSdkVersion of the <uses-permission>
    origin: PermissionOrigin = PermissionOrigin.REQUESTED

    @property
    def is_dangerous(self) -> bool:
        return self.protection is not None and "dangerous" in self.protection.split("|")

    @property
    def is_app_op(self) -> bool:
        return self.protection is not None and "appop" in self.protection.split("|")

    @property
    def type_text(self) -> str:
        return protection_text(self.protection)


@dataclass(frozen=True)
class PermissionsInfo:
    permissions: tuple[Permission, ...] = ()         # requested, defined by Android, not app-op
    app_ops: tuple[Permission, ...] = ()             # requested, special access ("appop" level)
    custom_permissions: tuple[Permission, ...] = ()  # not defined by Android: requested or declared here
