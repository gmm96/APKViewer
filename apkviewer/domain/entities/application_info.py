"""
Identity, SDK range and physical file metrics of an analyzed APK.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ApplicationInfo:
    app_name: str
    package_name: str
    version_name: str | None
    version_code: str | None
    min_sdk: str | None
    target_sdk: str | None
    max_sdk: str | None
    file_name: str | None
    file_path: str | None
    file_size: int | None
    last_modified: datetime | None
