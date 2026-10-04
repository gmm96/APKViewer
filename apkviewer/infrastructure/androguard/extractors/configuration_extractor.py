"""
Extracts build configurations: ABIs, hardware requirements, locales, and screen densities.

Locales and densities are read from the resource table (resources.arsc).
The table's own package names are used, not the manifest's: they differ in
repackaged apps, and file names can't be trusted either (resource
obfuscation turns `drawable-xxhdpi` into `res/tG.png`).
"""

import re
from collections.abc import Callable
from typing import Any

from androguard.core.apk import APK
from babel import Locale
from babel.core import UnknownLocaleError

from apkviewer.domain.entities.configuration_info import ConfigurationInfo


class ConfigurationExtractor:
    _DENSITY_PATTERN: re.Pattern = re.compile(r"-(ldpi|mdpi|hdpi|xhdpi|xxhdpi|xxxhdpi|tvdpi|anydpi|nodpi)")
    _REGION_PREFIX_PATTERN: re.Pattern = re.compile(r"-r([A-Z]{2,3})$")

    _LEGACY_LOCALES: dict[str, str] = {
        "in": "id",  # Indonesian
        "iw": "he",  # Hebrew
        "ji": "yi",  # Yiddish
    }

    _DENSITY_NAMES: dict[int, str] = {
        120: "ldpi", 160: "mdpi", 213: "tvdpi", 240: "hdpi", 320: "xhdpi",
        480: "xxhdpi", 640: "xxxhdpi", 65534: "anydpi", 65535: "nodpi",
    }

    _DENSITY_MEANINGS: dict[str, str] = {
        "ldpi": "~120dpi (Low)",
        "mdpi": "~160dpi (Medium)",
        "hdpi": "~240dpi (High)",
        "xhdpi": "~320dpi (X-High)",
        "xxhdpi": "~480dpi (XX-High)",
        "xxxhdpi": "~640dpi (XXX-High)",
        "tvdpi": "~213dpi (TV)",
        "anydpi": "Scales automatically",
        "nodpi": "No scaling",
    }

    def extract(self, apk: APK) -> ConfigurationInfo:
        return ConfigurationInfo(
            architectures=self._architectures(apk),
            hardware_requirements=tuple(sorted(apk.get_features())),
            locales=self._extract_locales(apk),
            screen_densities=self._extract_densities(apk),
        )

    @staticmethod
    def _architectures(apk: APK) -> tuple[str, ...]:
        archs = {
            parts[1]
            for parts in (f.split("/") for f in apk.get_files() if f.startswith("lib/"))
            if len(parts) > 2
        }
        return tuple(sorted(archs))

    @classmethod
    def _extract_locales(cls, apk: APK) -> tuple[str, ...]:
        locales: set[str] = set()
        for raw_locales in cls._per_package(apk, lambda arsc, package: arsc.get_locales(package)):
            for loc in raw_locales:
                if isinstance(loc, bytes):
                    loc = loc.decode("utf-8", errors="ignore")
                loc = loc.strip("\x00").strip()
                if loc:
                    locales.add(cls._format_locale_name(loc))
        return tuple(sorted(locales))

    @staticmethod
    def _per_package(apk: APK, read: Callable[[Any, str], Any]) -> list[Any]:
        """Apply `read(arsc, package)` to every package of the resource table, skipping failures."""
        try:
            arsc = apk.get_android_resources()
            packages = arsc.get_packages_names() if arsc else []
        except Exception:
            return []
        results: list[Any] = []
        for package in packages:
            try:
                results.append(read(arsc, package))
            except Exception:
                continue
        return results

    @classmethod
    def _format_locale_name(cls, raw_locale: str) -> str:
        # Android writes regions as 'pt-rBR'; Babel expects 'pt_BR'.
        fixed_loc = cls._REGION_PREFIX_PATTERN.sub(r"-\1", raw_locale)
        babel_loc = fixed_loc.replace("-", "_")

        lang_part = babel_loc.split("_")[0]
        if lang_part in cls._LEGACY_LOCALES:
            babel_loc = babel_loc.replace(lang_part, cls._LEGACY_LOCALES[lang_part], 1)

        try:
            parsed = Locale.parse(babel_loc)
            return f"{parsed.english_name} ({fixed_loc})"
        except (UnknownLocaleError, ValueError):
            return fixed_loc

    @classmethod
    def _extract_densities(cls, apk: APK) -> tuple[str, ...]:
        names = set()
        for type_configs in cls._per_package(apk, lambda arsc, package: arsc.get_type_configs(package)):
            for configs in type_configs.values():
                for config in configs:
                    name = cls._DENSITY_NAMES.get(config.get_density())
                    if name:
                        names.add(name)
        if not names:  # no resource table: fall back to the folder names
            for filename in apk.get_files():
                match = filename.startswith("res/") and cls._DENSITY_PATTERN.search(filename)
                if match:
                    names.add(match.group(1))
        return tuple(sorted(f"{name} ({cls._DENSITY_MEANINGS.get(name, 'Unknown')})" for name in names))
