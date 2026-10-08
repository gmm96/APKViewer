"""
Declarative description of one column of a tree ("#0" is the tree column).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TreeColumn:
    id: str
    label: str
    width: int = 150      # fixed width, used by columns without a weight
    min_width: int = 80
    stretch: bool = False
    # Share of the width left over by the fixed columns: a column with weight 2 gets twice
    # the width of one with weight 1. Below `min_width` the table scrolls horizontally.
    weight: float | None = None
