"""
Port for formatting datetime objects into human-readable strings.
Living in the domain allows both Application (serializers) and Presentation (UI)
to depend on this abstraction without violating dependency rules.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class DateFormatter(ABC):
    @abstractmethod
    def format(self, dt: datetime) -> str:
        raise NotImplementedError
