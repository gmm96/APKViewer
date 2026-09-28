from collections.abc import Callable
from dataclasses import dataclass

@dataclass(frozen=True)
class AppToolbarItem:
    key: str
    label: str
    command: Callable[[], None]
    icon_path: str | None = None
    accelerator: str | None = None
    shortcut: str | None = None
