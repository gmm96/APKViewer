"""
Port abstracting "how do we render a byte count for humans", so widgets
depend on an interface rather than a concrete formatting strategy. This is
what lets FilesPanel be unit-tested with a fake formatter, and would let a
different unit system be swapped in without touching any widget code.
"""

from abc import ABC, abstractmethod
from typing import Any


class SizeFormatter(ABC):
    @abstractmethod
    def format(self, num_bytes: Any) -> str:
        raise NotImplementedError

