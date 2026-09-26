"""
Resolves and loads the best-available launcher icon for an APK.
"""

import io
import os

from androguard.core.apk import APK
from PIL import Image

from apkviewer.config import ANDROID_NS, DPI_SCORES, ICON_SIZE


class IconExtractor:
    """Finds and loads the highest-resolution launcher icon declared by an APK."""

    def __init__(self, icon_size: tuple[int, int] = ICON_SIZE, dpi_scores: dict[str, int] | None = None) -> None:
        self._icon_size: tuple[int, int] = icon_size
        self._dpi_scores: dict[str, int] = dpi_scores or DPI_SCORES

    def extract(self, apk: APK) -> Image.Image | None:
        """Return a PIL Image for the app's icon, or None if unavailable."""
        try:
            icon_path = apk.get_app_icon(max_dpi=True)
            if icon_path and icon_path.lower().endswith((".png", ".webp", ".jpg")):
                icon_data = apk.get_file(icon_path)
                if icon_data:
                    return self._load_and_resize(icon_data)

            base_name = self._resolve_icon_base_name(apk, icon_path)
            return self._find_best_icon_by_name(apk, base_name)
        except Exception:
            return None

    def _resolve_icon_base_name(self, apk: APK, icon_path: str | None) -> str:
        if icon_path:
            return os.path.splitext(os.path.basename(icon_path))[0]
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
            and f.lower().endswith((".png", ".webp", ".jpg"))
        ]
        matches.sort(
            key=lambda p: next((score for dpi, score in self._dpi_scores.items() if dpi in p.lower()), 0),
            reverse=True,
        )
        for match in matches:
            try:
                return self._load_and_resize(apk.get_file(match))
            except Exception:
                continue
        return None

    def _load_and_resize(self, icon_bytes: bytes) -> Image.Image:
        img = Image.open(io.BytesIO(icon_bytes))
        return img.resize(self._icon_size, Image.Resampling.LANCZOS)
