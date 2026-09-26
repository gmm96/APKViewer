"""
Port implemented by anything that turns a loaded APK into a display
section (a plain label -> value dict). Sharing this contract lets the
ApkAnalyzer use case treat every extractor interchangeably: a new section
is added by writing a new extractor, without touching the use case
(Open/Closed principle).
"""

from abc import ABC, abstractmethod
from typing import Any

from androguard.core.apk import APK


class AnalysisSectionExtractor(ABC):
    @abstractmethod
    def extract(self, apk: APK) -> dict[str, Any]:
        raise NotImplementedError
