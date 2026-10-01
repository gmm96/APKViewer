"""
Extracts build configurations: ABIs, hardware requirements, locales, and screen densities.
"""

import re
from typing import Any

from androguard.core.apk import APK
from babel import Locale
from babel.core import UnknownLocaleError

from apkviewer.infrastructure.androguard.analysis_section_extractor import AnalysisSectionExtractor


class ConfigurationExtractor(AnalysisSectionExtractor):
    _DENSITY_PATTERN: re.Pattern = re.compile(r"-(ldpi|mdpi|hdpi|xhdpi|xxhdpi|xxxhdpi|tvdpi|anydpi|nodpi)")

    _REGION_PREFIX_PATTERN: re.Pattern = re.compile(r"-r([A-Z]{2,3})$")

    _LEGACY_LOCALES: dict[str, str] = {
        "in": "id",  # Indonesian
        "iw": "he",  # Hebrew
        "ji": "yi",  # Yiddish
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

    def extract(self, apk: APK) -> dict[str, Any]:
        return {
            "Architectures": self._format_architectures(apk),
            "Hardware Requirements": sorted(apk.get_features()),
            "Supported Locales": self._extract_locales(apk),
            "Screen Densities": self._extract_densities(apk),
        }

    @staticmethod
    def _format_architectures(apk: APK) -> str:
        archs = {
            parts[1]
            for parts in (f.split("/") for f in apk.get_files() if f.startswith("lib/"))
            if len(parts) > 2
        }
        return ", ".join(sorted(archs)) if archs else "None / Unknown (Java only)"

    @classmethod
    def _extract_locales(cls, apk: APK) -> list[str]:
        try:
            arsc = apk.get_android_resources()
            pkg_name = apk.get_package()
            if not arsc or not pkg_name:
                return []

            valid_locales = set()
            for loc in arsc.get_locales(pkg_name):
                if isinstance(loc, bytes):
                    loc = loc.decode("utf-8", errors="ignore")

                loc = loc.strip("\x00").strip()
                if loc:
                    formatted_locale = cls._format_locale_name(loc)
                    valid_locales.add(formatted_locale)

            return sorted(valid_locales) if valid_locales else ["Default only"]
        except Exception:
            return ["Unknown"]

    @classmethod
    def _format_locale_name(cls, raw_locale: str) -> str:
        # 1. Remove the Android-specific 'r' in regions (pt-rBR -> pt-BR)
        fixed_loc = cls._REGION_PREFIX_PATTERN.sub(r"-\1", raw_locale)

        # 2. Prepare for Babel (expects underscores, e.g., pt_BR)
        babel_loc = fixed_loc.replace("-", "_")

        # 3. Translate legacy Java codes if necessary
        lang_part = babel_loc.split("_")[0]
        if lang_part in cls._LEGACY_LOCALES:
            babel_loc = babel_loc.replace(lang_part, cls._LEGACY_LOCALES[lang_part], 1)

        # 4. Resolve English display name dynamically using CLDR data
        try:
            parsed = Locale.parse(babel_loc)
            # english_name formats nicely, e.g., "Portuguese (Brazil)" or "Spanish"
            return f"{parsed.english_name} ({fixed_loc})"
        except UnknownLocaleError:
            # Fallback for completely custom or unparseable BCP-47 tags
            return fixed_loc

    @classmethod
    def _extract_densities(cls, apk: APK) -> list[str]:
        densities = set()
        for filename in apk.get_files():
            if filename.startswith("res/"):
                match = cls._DENSITY_PATTERN.search(filename)
                if match:
                    density_key = match.group(1)
                    meaning = cls._DENSITY_MEANINGS.get(density_key, "Unknown")
                    densities.add(f"{density_key} ({meaning})")

        return sorted(densities) if densities else ["Default / Unknown"]
