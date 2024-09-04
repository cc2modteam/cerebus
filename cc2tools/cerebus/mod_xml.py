"""Read/Write/Update mod.xml files"""
from typing import Optional
from pathlib import Path
from xml.etree import ElementTree


class ModXml:

    def __init__(self, folder: Optional[Path] = None):
        self.folder: Optional[Path] = folder
        self.tree: ElementTree = ElementTree.ElementTree(
            ElementTree.Element("data", {})
        )
        self.author = ""
        self.description = ""
        self.name = ""

    def read(self, folder: Path):
        mod_xml = folder / "mod.xml"
        tree: ElementTree = ElementTree.parse(mod_xml)
        self.tree = tree

    def write(self):
        mod_xml = self.folder / "mod.xml"
        self.tree.write(mod_xml, xml_declaration=True, encoding="UTF-8")

    @property
    def data(self) -> ElementTree.Element:
        return self.tree.getroot()

    @property
    def name(self):
        return self.data.get("name", "My Mod")

    @name.setter
    def name(self, value: str):
        self.data.set("name", value)

    @property
    def author(self):
        return self.data.get("author", "Altus Gauge")

    @author.setter
    def author(self, value: str):
        self.data.set("author", value)

    @property
    def description(self):
        return self.data.get("description", "My new CC2 Mod")

    @description.setter
    def description(self, value: str):
        self.data.set("description", value)
