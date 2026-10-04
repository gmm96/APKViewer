"""
Whether a component can be reached from other apps, and HOW we know it.

Android decides this from the `android:exported` attribute when it is
declared and from SDK-dependent defaults when it is not. That defaulting
is the only place where the rules live.
"""

from enum import Enum

from apkviewer.domain.entities.component_kind import ComponentKind

# Providers declared without `exported` are exported when the app targets this API or lower.
_LEGACY_PROVIDER_MAX_TARGET_SDK: int = 16


class ExportState(Enum):
    EXPORTED = "exported"                        # android:exported="true"
    NOT_EXPORTED = "not exported"                # android:exported="false"
    IMPLICIT_EXPORTED = "implicitly exported"    # not declared; the default makes it exported
    IMPLICIT_NOT_EXPORTED = "implicitly not exported"
    UNRESOLVED = "unresolved"                    # declared as a resource reference we can't read

    @property
    def may_be_exported(self) -> bool:
        """True unless we are sure it is private (an unresolved value is not hidden)."""
        return self not in (ExportState.NOT_EXPORTED, ExportState.IMPLICIT_NOT_EXPORTED)

    @classmethod
    def resolve(
        cls,
        kind: ComponentKind,
        declared: str | None,
        has_intent_filters: bool,
        target_sdk: int | None,
    ) -> "ExportState":
        """
        `declared` is the raw `android:exported` value (None when absent).
        `target_sdk` is the app's targetSdkVersion (None when it can't be read,
        which Android itself treats as a very old app).
        """
        value = (declared or "").strip().lower()
        if value in ("true", "1"):
            return cls.EXPORTED
        if value in ("false", "0"):
            return cls.NOT_EXPORTED
        if value:
            return cls.UNRESOLVED  # e.g. "@bool/exported" / "@7f050001"

        if kind is ComponentKind.PROVIDER:
            legacy = target_sdk is None or target_sdk <= _LEGACY_PROVIDER_MAX_TARGET_SDK
            return cls.IMPLICIT_EXPORTED if legacy else cls.IMPLICIT_NOT_EXPORTED
        return cls.IMPLICIT_EXPORTED if has_intent_filters else cls.IMPLICIT_NOT_EXPORTED
