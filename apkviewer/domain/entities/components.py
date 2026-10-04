"""
Components declared in the manifest, with the intent filters of each one.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.component_kind import ComponentKind
from apkviewer.domain.entities.export_state import ExportState
from apkviewer.domain.entities.exported_intent import ExportedIntent, IntentData


@dataclass(frozen=True)
class IntentFilter:
    actions: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    data: tuple[IntentData, ...] = ()
    auto_verify: bool = False  # android:autoVerify (API 23+): an App Link candidate


@dataclass(frozen=True)
class ManifestElement:
    """A child element of a component other than <intent-filter> (meta-data, layout, ...)."""
    tag: str
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Component:
    name: str
    kind: ComponentKind
    export_state: ExportState
    permission: str | None = None
    intent_filters: tuple[IntentFilter, ...] = ()
    # Every other attribute / child element the manifest declares for it, in manifest order.
    attributes: tuple[tuple[str, str], ...] = ()
    elements: tuple[ManifestElement, ...] = ()

    @property
    def may_be_exported(self) -> bool:
        return self.export_state.may_be_exported


@dataclass(frozen=True)
class DeclaredComponents:
    items: tuple[Component, ...] = ()

    def of_kind(self, *kinds: ComponentKind) -> tuple[Component, ...]:
        return tuple(component for component in self.items if component.kind in kinds)

    def exported_intents(self) -> tuple[ExportedIntent, ...]:
        """
        Every action of every filter of the components that may be exported,
        one entry each. Components whose exported value could not be resolved
        are included rather than hidden.
        """
        intents = {
            ExportedIntent(
                name=action,
                component_name=component.name,
                component_kind=component.kind,
                categories=intent_filter.categories,
                data=intent_filter.data,
                auto_verify=intent_filter.auto_verify,
            ): None
            for component in self.items
            if component.may_be_exported
            for intent_filter in component.intent_filters
            for action in intent_filter.actions
        }
        return tuple(sorted(intents, key=lambda i: (i.name.lower(), i.component_name)))
