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

    def __init__(
            self,
            icon_size: tuple[int, int] = ICON_SIZE,
            dpi_scores: dict[str, int] | None = None
        ) -> None:
        self._icon_size: tuple[int, int] = icon_size
        self._dpi_scores: dict[str, int] = dpi_scores or DPI_SCORES

    def extract(self, apk: APK) -> Image.Image | None:
        """Return the app's icon resized to the UI thumbnail size, or None if unavailable."""
        icon = self.extract_full_resolution(apk)
        if icon is None:
            return None
        return icon.resize(self._icon_size, Image.Resampling.LANCZOS)

    def extract_full_resolution(self, apk: APK) -> Image.Image | None:
        """Return the app's icon at its original (highest available) resolution, or None."""
        try:
            icon_path = apk.get_app_icon(max_dpi=True)
            if icon_path and icon_path.lower().endswith((".png", ".webp", ".jpg")):
                icon_data = apk.get_file(icon_path)
                if icon_data:
                    return self._load(icon_data)

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
                return self._load(apk.get_file(match))
            except Exception:
                continue
        return None

    @staticmethod
    def _load(icon_bytes: bytes) -> Image.Image:
        img = Image.open(io.BytesIO(icon_bytes))
        img.load()  # decode now so corrupt images fail here, not later at save/resize time
        return img
