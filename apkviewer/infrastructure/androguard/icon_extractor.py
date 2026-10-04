"""
Resolves the best-available launcher icon of an APK and returns it as
PNG bytes, so nothing outside this layer needs an imaging library to
handle it.

The icon is found by following the manifest's icon reference through the
resource table (which works even when the file names are obfuscated, e.g.
`res/tG.png`). Looking for a file called `ic_launcher` is only the fallback.
"""

import io
import os
from typing import Any

from androguard.core.apk import APK
from PIL import Image

from apkviewer.infrastructure.androguard.config.android import ANDROID_NS, DPI_SCORES

_RASTER: tuple[str, ...] = (".png", ".webp", ".jpg", ".jpeg")
# Densities from this value up are "anydpi"/"nodpi": not a real screen density.
_NON_DENSITY: int = 0xFFFE


class IconExtractor:
    """Finds the highest-resolution launcher icon declared by an APK."""

    _PNG_SAFE_MODES: tuple[str, ...] = ("RGB", "RGBA", "L", "LA", "P")

    def __init__(self, dpi_scores: dict[str, int] | None = None) -> None:
        self._dpi_scores: dict[str, int] = dpi_scores or DPI_SCORES

    def extract(self, apk: APK) -> bytes | None:
        """Return the icon (original resolution) encoded as PNG, or None if unavailable."""
        try:
            image = self._find_icon(apk)
            return self._encode_png(image) if image is not None else None
        except Exception:
            return None

    def resolve_candidates(self, apk: APK) -> list[str]:
        """Raster files the manifest's icon resolves to, best (highest density) first."""
        reference = self._icon_reference(apk)
        if not reference:
            return []
        if not reference.startswith("@"):
            return [reference]  # already a file path

        resources = apk.get_android_resources()
        if not resources:
            return []
        try:
            res_id = int(reference[1:].split(":")[-1], 16)
            resolved = resources.get_resolved_res_configs(res_id)
        except Exception:
            return []

        ranked = sorted(
            (
                (self._density_rank(config), name)
                for config, name in resolved
                if isinstance(name, str) and name.lower().endswith(_RASTER)
            ),
            key=lambda item: item[0],
            reverse=True,  # stable: equal densities keep the resource table's order
        )
        return [name for _, name in ranked]

    # --- Resolution ---------------------------------------------------------------

    def _find_icon(self, apk: APK) -> Image.Image | None:
        for path in self.resolve_candidates(apk):
            image = self._try_load(apk, path)
            if image is not None:
                return image
        return self._find_best_icon_by_name(apk, self._resolve_icon_base_name(apk))

    @staticmethod
    def _icon_reference(apk: APK) -> str | None:
        """The icon the launcher shows: the main activity's, else the application's."""
        try:
            main_activity = apk.get_main_activity()
            reference = None
            if main_activity:
                reference = apk.get_attribute_value("activity", "icon", name=main_activity)
            return reference or apk.get_attribute_value("application", "icon")
        except Exception:
            return None

    @staticmethod
    def _density_rank(config: Any) -> int:
        try:
            density = int(config.get_density())
        except Exception:
            return 0
        return -1 if density >= _NON_DENSITY else density

    @staticmethod
    def _try_load(apk: APK, path: str) -> Image.Image | None:
        try:
            data = apk.get_file(path)
            return IconExtractor._load(data) if data else None
        except Exception:
            return None

    def _resolve_icon_base_name(self, apk: APK) -> str:
        xml_elem = apk.get_android_manifest_xml()
        if xml_elem is not None:
            app_tag = xml_elem.find(".//application")
            if app_tag is not None:
                icon_ref = app_tag.get(f"{ANDROID_NS}icon") or app_tag.get(f"{ANDROID_NS}roundIcon")
                if icon_ref and "/" in icon_ref:
                    return icon_ref.split("/")[-1]
        return "ic_launcher"

    def _find_best_icon_by_name(self, apk: APK, base_name: str) -> Image.Image | None:
        matches = [
            f for f in apk.get_files()
            if os.path.splitext(os.path.basename(f))[0] == base_name
            and f.lower().endswith(_RASTER)
        ]
        matches.sort(
            key=lambda p: next((score for dpi, score in self._dpi_scores.items() if dpi in p.lower()), 0),
            reverse=True,
        )
        for match in matches:
            image = self._try_load(apk, match)
            if image is not None:
                return image
        return None

    # --- Images -------------------------------------------------------------------------

    @staticmethod
    def _load(icon_bytes: bytes) -> Image.Image:
        img = Image.open(io.BytesIO(icon_bytes))
        img.load()  # decode now so corrupt images fail here, not later
        return img

    @classmethod
    def _encode_png(cls, image: Image.Image) -> bytes:
        prepared = image if image.mode in cls._PNG_SAFE_MODES else image.convert("RGBA")
        buffer = io.BytesIO()
        prepared.save(buffer, format="PNG")
        return buffer.getvalue()
