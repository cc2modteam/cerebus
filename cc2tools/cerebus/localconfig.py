"""Read/Write cerebus configuration data"""
import os
import yaml
from xml.etree import ElementTree
from typing import Dict, Union, List
from pathlib import Path
from .sdk.utils import DEFAULT_STEAMAPP_GAME_PATH, DEFAULT_STEAMAPP_WORKSHOP_CONTENT_PATH


class Configuration:
    """Proxy for reading/writing cerebus config"""
    data = {}

    @property
    def cfg_path(self) -> Path:
        cfg_file = Path(os.path.expanduser("~")) / "cc2-cerebus.yml"
        return cfg_file

    def read(self) -> Dict[str, Union[int, str]]:
        if not self.data:
            if self.cfg_path.exists():
                with self.cfg_path.open("r") as fd:
                    data = yaml.safe_load(fd)
                self.data = data
        return self.data

    def write(self, data: Dict[str, Union[int, str]]):
        with self.cfg_path.open("w") as fd:
            yaml.safe_dump(data, fd, sort_keys=True, indent=2)
        self.data.clear()
        self.read()

    @property
    def game(self) -> Path:
        return Path(self.read().get("game", DEFAULT_STEAMAPP_GAME_PATH))

    @game.setter
    def game(self, value: Path):
        data = self.read()
        data["game"] = str(value.absolute())
        self.write(data)

    @property
    def workshop(self):
        return Path(self.read().get("workshop", DEFAULT_STEAMAPP_WORKSHOP_CONTENT_PATH))

    @property
    def appdata(self):
        return Path(os.path.expandvars("%APPDATA%")) / "Carrier Command 2"

    @property
    def mods(self):
        return self.appdata / "mods"

    @property
    def mods_xml(self):
        return self.appdata / "mods.xml"

    @property
    def mod_dev_kit(self) -> Path:
        return self.game / "mod_dev_kit"

    @property
    def rom_0(self) -> Path:
        return self.game / "rom_0"

    def active_mod_folders(self) -> List[Path]:
        enabled = []
        data = ElementTree.parse(self.mods_xml).getroot()
        paths = data.findall("./active_mod_folders//")
        for path in paths:
            enabled.append(Path(path.get("value")))
        return enabled

    def local_mod_folders(self) -> List[Path]:
        folders = []
        found = self.mods.glob("*")
        for item in sorted(found):
            if item.is_dir():
                mod_xml = item / "mod.xml"
                if mod_xml.exists():
                    folders.append(item)
        return folders


CFG = Configuration()
