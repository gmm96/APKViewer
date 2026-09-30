"""
A single file stored inside an archive, as reported by an ArchiveReader.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ArchiveEntry:
    path: str
    size: int
    compressed_size: int
    modified: datetime | None = None
