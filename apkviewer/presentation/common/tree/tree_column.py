"""
Declarative description of one column of a tree ("#0" is the tree column).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TreeColumn:
    id: str
    label: str
    width: int = 150
    min_width: int = 80
    stretch: bool = False
