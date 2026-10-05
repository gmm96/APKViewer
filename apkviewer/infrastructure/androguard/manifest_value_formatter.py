"""
Makes the raw values of manifest attributes readable: resource references
are resolved and the numeric forms of enums and flag masks that
androguard hands out (`launchMode="2"`, `configChanges="0x000004B0"`) are
turned back into their names.
"""

from apkviewer.infrastructure.androguard.resource_reference_resolver import ResourceReferenceResolver

_ENUMS: dict[str, dict[int, str]] = {
    "launchMode": {0: "standard", 1: "singleTop", 2: "singleTask", 3: "singleInstance",
                   4: "singleInstancePerTask"},
    "screenOrientation": {
        -1: "unspecified", 0: "landscape", 1: "portrait", 2: "user", 3: "behind", 4: "sensor",
        5: "nosensor", 6: "sensorLandscape", 7: "sensorPortrait", 8: "reverseLandscape",
        9: "reversePortrait", 10: "fullSensor", 11: "userLandscape", 12: "userPortrait",
        13: "fullUser", 14: "locked",
    },
    "documentLaunchMode": {0: "none", 1: "intoExisting", 2: "always", 3: "never"},
    "persistableMode": {0: "persistRootOnly", 1: "persistAcrossReboots", 2: "persistNever"},
}

_FLAGS: dict[str, dict[int, str]] = {
    "configChanges": {
        0x0001: "mcc", 0x0002: "mnc", 0x0004: "locale", 0x0008: "touchscreen", 0x0010: "keyboard",
        0x0020: "keyboardHidden", 0x0040: "navigation", 0x0080: "orientation", 0x0100: "screenLayout",
        0x0200: "uiMode", 0x0400: "screenSize", 0x0800: "smallestScreenSize", 0x1000: "density",
        0x2000: "layoutDirection", 0x4000: "colorMode", 0x8000: "grammaticalGender",
        0x10000000: "fontWeightAdjustment", 0x40000000: "fontScale",
    },
    "foregroundServiceType": {
        0x1: "dataSync", 0x2: "mediaPlayback", 0x4: "phoneCall", 0x8: "location",
        0x10: "connectedDevice", 0x20: "mediaProjection", 0x40: "camera", 0x80: "microphone",
        0x100: "health", 0x200: "remoteMessaging", 0x400: "systemExempted", 0x800: "shortService",
        0x1000: "fileManagement", 0x2000: "mediaProcessing", 0x40000000: "specialUse",
    },
}

_SOFT_INPUT_STATE: dict[int, str] = {
    1: "stateUnchanged", 2: "stateHidden", 3: "stateAlwaysHidden", 4: "stateVisible",
    5: "stateAlwaysVisible",
}
_SOFT_INPUT_ADJUST: dict[int, str] = {0x10: "adjustResize", 0x20: "adjustPan", 0x30: "adjustNothing"}


class ManifestValueFormatter:
    def __init__(self, resolver: ResourceReferenceResolver) -> None:
        self._resolver: ResourceReferenceResolver = resolver

    def format(self, attribute: str, value: str) -> str:
        if self._resolver.is_reference(value):
            return self._resolver.describe(value)
        number = self._to_int(value)
        if number is None:
            return value
        decoded = self._decode(attribute, number)
        return decoded if decoded else value

    def declared(self, value: str | None) -> str | None:
        """A boolean attribute (e.g. `exported`) as 'true'/'false' even when it is a resource reference."""
        if value is None:
            return None
        # A reference that changes with the configuration can't be known: leave it unresolved.
        return self._resolver.literal(value, strict=True) or value

    # --- Decoding -------------------------------------------------------------------------------

    @classmethod
    def _decode(cls, attribute: str, number: int) -> str | None:
        if attribute in _ENUMS:
            return _ENUMS[attribute].get(number)
        if attribute in _FLAGS:
            return cls._decode_flags(_FLAGS[attribute], number)
        if attribute == "windowSoftInputMode":
            names = [
                _SOFT_INPUT_STATE.get(number & 0x0F),
                _SOFT_INPUT_ADJUST.get(number & 0xF0),
            ]
            return " | ".join(name for name in names if name) or None
        return None

    @staticmethod
    def _decode_flags(names: dict[int, str], number: int) -> str | None:
        if number == 0:
            return None
        parts = [name for bit, name in sorted(names.items()) if number & bit]
        rest = number & ~sum(bit for bit in names if number & bit)
        if rest:
            parts.append(f"0x{rest:X}")
        return " | ".join(parts)

    @staticmethod
    def _to_int(value: str) -> int | None:
        try:
            number = int(value, 0)
        except ValueError:
            return None
        if 0x80000000 <= number <= 0xFFFFFFFF:  # negative ints (e.g. -1) come out as unsigned hex
            number -= 0x100000000
        return number
