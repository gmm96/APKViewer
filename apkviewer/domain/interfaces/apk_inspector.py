"""
Port for "look inside an APK and describe it". The concrete library used
to parse APKs is an implementation detail of the infrastructure layer.
"""

from abc import ABC, abstractmethod

from apkviewer.domain.entities.apk_inspection import ApkInspection


class ApkInspector(ABC):
    @abstractmethod
    def inspect(self, apk_path: str) -> ApkInspection:
        raise NotImplementedError
