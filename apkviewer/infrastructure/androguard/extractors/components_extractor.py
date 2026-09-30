"""
Extracts declared components (activities, services, receivers, providers)
and the exported intent-filter actions they respond to.
"""

from typing import Any

from androguard.core.apk import APK

from apkviewer.domain.entities.analysis_labels import FIELD_INTENT_ACTIONS
from apkviewer.domain.entities.intent_action_format import IntentActionFormat
from apkviewer.infrastructure.androguard.analysis_section_extractor import AnalysisSectionExtractor
from apkviewer.infrastructure.androguard.config.android import ANDROID_NS


class ComponentsExtractor(AnalysisSectionExtractor):
    def extract(self, apk: APK) -> dict[str, Any]:
        return {
            "Activities": sorted(apk.get_activities()),
            "Services": sorted(apk.get_services()),
            "Receivers": sorted(apk.get_receivers()),
            "Providers": sorted(apk.get_providers()),
            FIELD_INTENT_ACTIONS: sorted(self._extract_intent_actions(apk)),
        }

    def _extract_intent_actions(self, apk: APK) -> list[str]:
        pkg_name = apk.get_package()
        actions = set()
        try:
            xml_root = apk.get_android_manifest_xml()
            if xml_root is None:
                return []
            for tag in ("activity", "activity-alias", "service", "receiver", "provider"):
                for comp in xml_root.iter(tag):
                    if not self._is_exported(comp):
                        continue
                    comp_name = self._resolve_component_name(comp, pkg_name)
                    comp_type = tag.capitalize()

                    for filter_node in comp.iter("intent-filter"):
                        actions.update(self._actions_from_filter(filter_node, comp_type, comp_name))
        except Exception:
            pass
        return list(actions)

    @staticmethod
    def _is_exported(comp) -> bool:
        exported = comp.get(f"{ANDROID_NS}exported", "").lower()
        has_filters = comp.find("intent-filter") is not None
        return exported == "true" or (not exported and has_filters)

    @staticmethod
    def _resolve_component_name(comp, pkg_name: str) -> str:
        name = comp.get(f"{ANDROID_NS}name", "Unknown")
        if name.startswith("."):
            return pkg_name + name
        if "." not in name and name != "Unknown":
            return f"{pkg_name}.{name}"
        return name

    def _actions_from_filter(self, filter_node, comp_type: str, comp_name: str) -> set[str]:
        action_names = []
        extras = []

        for node in filter_node:
            if node.tag == "action":
                name = node.get(f"{ANDROID_NS}name")
                if name:
                    action_names.append(name)
            elif node.tag == "category":
                cat = node.get(f"{ANDROID_NS}name")
                if cat:
                    extras.append(
                        IntentActionFormat.format_extra("category", cat.replace("android.intent.category.", ""))
                    )
            elif node.tag == "data":
                extras.extend(self._data_node_extras(node))

        extras.append(IntentActionFormat.format_extra(comp_type, comp_name))
        return {IntentActionFormat.format(action, extras) for action in action_names}

    @staticmethod
    def _data_node_extras(node) -> list[str]:
        attr_labels = ("mimeType", "scheme", "host", "path", "pathPrefix")
        extras = []
        for attr in attr_labels:
            value = node.get(f"{ANDROID_NS}{attr}")
            if value:
                extras.append(IntentActionFormat.format_extra(attr, value))
        return extras
