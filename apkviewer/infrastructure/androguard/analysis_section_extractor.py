"""
Contract shared by the Androguard-based extractors: each one turns a
loaded APK into a display section (a plain label -> value dict). A new
section is added by writing a new extractor, without touching the
inspector that runs them (Open/Closed principle).

This lives in the infrastructure layer because it is expressed in terms of
Androguard's APK type, which the rest of the application never sees.
"""

from abc import ABC, abstractmethod
from typing import Any

from androguard.core.apk import APK


class AnalysisSectionExtractor(ABC):
    @abstractmethod
    def extract(self, apk: APK) -> dict[str, Any]:
        raise NotImplementedError
