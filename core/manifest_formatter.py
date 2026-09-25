"""
Formats an APK's AndroidManifest.xml into pretty-printed text.
"""
import os
import xml.dom.minidom as minidom
from abc import ABC, abstractmethod
from typing import Optional
from lxml import etree


class XmlSerializer(ABC):
    """Abstracts away which XML library actually serializes the manifest tree."""

    @abstractmethod
    def serialize(self, xml_root) -> bytes:
        raise NotImplementedError


class LxmlSerializer(XmlSerializer):
    def serialize(self, xml_root) -> bytes:
        return etree.tostring(xml_root, encoding="utf-8")


class ElementTreeSerializer(XmlSerializer):
    def serialize(self, xml_root) -> bytes:
        return etree.tostring(xml_root, encoding="utf-8")


def default_xml_serializer() -> XmlSerializer:
    return LxmlSerializer()


class ManifestFormatter:
    def __init__(self, serializer: Optional[XmlSerializer] = None):
        self._serializer = serializer or default_xml_serializer()

    def format(self, apk) -> str:
        try:
            xml_root = apk.get_android_manifest_xml()
            if xml_root is None:
                return "Manifest XML is missing or corrupted."

            raw_xml = self._serializer.serialize(xml_root)
            pretty = minidom.parseString(raw_xml).toprettyxml(indent="    ")
            return os.linesep.join(line for line in pretty.splitlines() if line.strip())
        except Exception as exc:
            return f"Error processing Manifest:\n{exc}"
