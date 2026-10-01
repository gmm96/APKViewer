"""
Scans DEX classes to extract hardcoded HTTP/HTTPS URLs.
"""

import re
from typing import Any

from androguard.core.apk import APK
from androguard.core.dex import DEX
from apkviewer.infrastructure.androguard.analysis_section_extractor import AnalysisSectionExtractor


class EmbeddedContentExtractor(AnalysisSectionExtractor):
    _URL_REGEX: re.Pattern = re.compile(r"https?://[\w\-\.\:]+(?:/[\w\-\.\:\/\?\=\&\%\#\+]*)?")

    def extract(self, apk: APK) -> dict[str, Any]:
        return {
            "Discovered URLs": self._extract_urls(apk)
        }

    def _extract_urls(self, apk: APK) -> list[str]:
        urls = set()
        for dex_bytes in apk.get_all_dex():
            try:
                for string_data in DEX(dex_bytes).get_strings():
                    text = string_data if isinstance(string_data, str) else string_data.decode("utf-8", errors="ignore")

                    if "http://" in text or "https://" in text:
                        urls.update(self._URL_REGEX.findall(text))
            except Exception:
                pass

        return sorted(urls)
