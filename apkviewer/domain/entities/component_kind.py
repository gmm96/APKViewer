"""
The kinds of component an Android manifest can declare.
"""

from enum import Enum


class ComponentKind(Enum):
    ACTIVITY = "Activity"
    ACTIVITY_ALIAS = "Activity alias"
    SERVICE = "Service"
    RECEIVER = "Receiver"
    PROVIDER = "Provider"
