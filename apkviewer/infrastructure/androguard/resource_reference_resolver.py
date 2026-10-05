"""
Turns the resource references of the manifest (`@7F0B003F`) into something
readable using the app's resource table: the value when the resource is a
plain string / number / boolean, and always its name (`@style/Theme.Foo`).
"""

import re

from androguard.core.apk import APK

_REFERENCE = re.compile(r"@[0-9A-Fa-f]{8}")
_NAME = re.compile(r"@([^:/]+):(.+)")
_FILE_EXTENSIONS = (".xml", ".png", ".webp", ".jpg", ".jpeg")
_MAX_TEXT = 120


class ResourceReferenceResolver:
    def __init__(self, apk: APK) -> None:
        try:
            self._arsc = apk.get_android_resources()
            self._packages: set[str] = set(self._arsc.get_packages_names()) if self._arsc else set()
        except Exception:
            self._arsc, self._packages = None, set()
        self._cache: dict[str, tuple[str | None, str | None, int]] = {}

    @staticmethod
    def is_reference(value: str) -> bool:
        return bool(_REFERENCE.fullmatch(value))

    def describe(self, value: str) -> str:
        """`value (@type/name)` for plain resources, `@type/name` for styles, drawables..."""
        if not self.is_reference(value):
            return value
        name, default, distinct = self._lookup(value)
        if name is None:
            return value  # not in this app's table (e.g. an Android framework resource)
        if default is None:
            return name
        note = ""
        if distinct > 1 and name.startswith(("@bool/", "@integer/")):
            note = "; varies by configuration"
        return f"{self._shorten(default)} ({name}{note})"

    def literal(self, value: str, strict: bool = False) -> str | None:
        """The plain value a reference stands for; None if unknown (or, if `strict`, if it varies)."""
        if not self.is_reference(value):
            return value
        _, default, distinct = self._lookup(value)
        if default is None or (strict and distinct > 1):
            return None
        return default

    # --- Lookup ---------------------------------------------------------------------------

    def _lookup(self, reference: str) -> tuple[str | None, str | None, int]:
        """(name, value in the default configuration, number of distinct plain values)."""
        if reference not in self._cache:
            self._cache[reference] = self._read(reference)
        return self._cache[reference]

    def _read(self, reference: str) -> tuple[str | None, str | None, int]:
        if self._arsc is None:
            return None, None, 0
        res_id = int(reference[1:], 16)
        try:
            name = self._short_name(self._arsc.get_resource_xml_name(res_id))
        except Exception:
            name = None
        try:
            resolved = self._arsc.get_resolved_res_configs(res_id)
        except Exception:
            resolved = []

        values: list[str] = []
        default: str | None = None
        for config, value in resolved:
            if not isinstance(value, str) or self._is_file(value):
                continue  # styles/arrays come as lists, drawables as file paths
            values.append(value)
            if default is None and self._is_default(config):
                default = value
        if default is None and values:
            default = values[0]
        return name, default, len(set(values))

    def _short_name(self, full_name: str | None) -> str | None:
        """'@com.app:string/x' -> '@string/x' for the app's own resources."""
        if not full_name:
            return None
        match = _NAME.fullmatch(full_name)
        if match and match.group(1) in self._packages:
            return f"@{match.group(2)}"
        return full_name

    @staticmethod
    def _is_default(config: object) -> bool:
        try:
            return bool(config.is_default())  # type: ignore[attr-defined]
        except Exception:
            return False

    @staticmethod
    def _is_file(value: str) -> bool:
        return value.startswith("res/") or ("/" in value and value.lower().endswith(_FILE_EXTENSIONS))

    @staticmethod
    def _shorten(text: str) -> str:
        text = " ".join(text.split())
        return text if len(text) <= _MAX_TEXT else text[: _MAX_TEXT - 1] + "…"
