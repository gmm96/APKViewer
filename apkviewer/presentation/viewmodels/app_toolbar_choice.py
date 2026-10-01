from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class AppToolbarChoice:
    key: str
    label: str
    command: Callable[[], None]
    icon_path: str | None = None
