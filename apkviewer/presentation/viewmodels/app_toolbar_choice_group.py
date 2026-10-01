from collections.abc import Sequence
from dataclasses import dataclass

from .app_toolbar_choice import AppToolbarChoice


@dataclass(frozen=True)
class AppToolbarChoiceGroup:
    """Mutually exclusive options shown under a (disabled) title inside a menu."""
    key: str
    title: str
    choices: Sequence[AppToolbarChoice]
    selected_key: str
