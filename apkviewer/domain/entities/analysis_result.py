"""
Everything the presentation layer needs to render after analyzing one APK.
"""

from dataclasses import dataclass
from typing import Any
from androguard.core.apk import APK
from PIL import Image


@dataclass
class AnalysisResult:
    apk: APK
    icon: Image.Image | None
    sections: dict[str, dict[str, Any]]

    @property
    def package_name(self) -> str:
        """Package name of the app, or "app" when the APK does not declare one."""
        return self.apk.get_package() or "app"
