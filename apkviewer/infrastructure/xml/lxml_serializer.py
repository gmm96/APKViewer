"""
Default XmlSerializer implementation, backed by lxml.
"""

from lxml import etree

from apkviewer.domain.interfaces.xml_serializer import XmlSerializer


class LxmlSerializer(XmlSerializer):
    def serialize(self, xml_root) -> bytes:
        return etree.tostring(xml_root, encoding="utf-8")
