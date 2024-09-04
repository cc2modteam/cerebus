"""Simulate the CC2 lua API and runtime"""
import time
import pygame
from typing import List, Optional
from pathlib import Path
import lupa.lua53 as lupa
from ..localconfig import CFG


LIBRARY_ORDER = [
    "library_enum.lua",
    "library_util.lua",
    "library_vehicle.lua",
    "library_ui.lua",
]

SCREENS = [
    "pause_menu",
    "screen_carrier_camera",
    "overlay",
    "screen_power",
    "screen_navigation",
    "screen_radar",
    "screen_vehicle_camera",
    "screen_compass",
    "vehicle_hud",
    # TODO add the rest
]


class FileSystem:
    def __init__(self, root: Path):
        self.root = root
        self.files = []
        files = root.rglob("*")
        for item in files:
            if item.is_file():
                suffix = item.suffix.lower()
                if suffix in [".lua", ".csv"]:
                    self.files.append(item.relative_to(self.root))

    def __str__(self):
        return self.root.parent.name


def get_rom0_fs() -> FileSystem:
    fs = FileSystem(CFG.rom_0)
    return fs


def get_filesystems(mods: List[Path]) -> List[FileSystem]:
    mod_files = []
    for mod in mods:
        fs = FileSystem(mod / "content")
        if fs.files:
            mod_files.append(fs)

    mod_files.append(get_rom0_fs())

    return mod_files


def get_file(fslist: List[FileSystem], path: str) -> Optional[Path]:
    path_item = Path(path)
    for item in fslist:
        for fileitem in item.files:
            if fileitem.name.lower() == path.lower():
                return item.root / fileitem
    return None


class Color8:
    def __init__(self, r, g, b, a=255):
        self._r = r % 255
        self._g = g % 255
        self._b = b % 255
        self._a = a % 255

    def to_color(self) -> pygame.Color:
        return pygame.Color(self._r, self._g, self._b, a=self._a)

    def r(self):
        return self._r

    def g(self):
        return self._g

    def b(self):
        return self._b

    def a(self):
        return self._a


class Simulator:
    def __init__(self):
        self.mods: List[FileSystem] = []
        self.lua = None
        self.surface = None
        self.loading_frames = 120
        self.alpha_stack = []
        self.text_color = {}
        self.locale = {}
        self.fonts = {}
        self.visible = True
        self.screen_script = None
        self.logic_tick = 0
        self.last_tick = 0
        self.w = 128
        self.h = 128

    def load(self, mods: List[Path]):
        self.mods = get_filesystems(mods)

    def update_ui_set_back_color(self, col):
        color = col.to_color()
        self.surface.fill(color)

    def update_set_is_visible(self, truth):
        self.visible = truth

    def update_ui_pop_alpha(self):
        self.alpha_stack.pop(0)

    def update_ui_push_alpha(self, alpha):
        self.alpha_stack.insert(0, alpha)

    def update_ui_get_text_size(self, text, cols, lines):
        return min(cols, 24) * 10, lines * 8

    def update_ui_text(self, x, y, text, w, h, color, rot):
        if isinstance(text, int):
            text = self.update_get_loc(text)
        col = color.to_color()
        surf = self.fonts[0].render(text, False, col)
        self.surface.blit(surf, (x, y))

    def update_ui_rectangle(self, x, y, w, h, col):
        pass

    def update_ui_rectangle_outline(self, x, y, w, h, col):
        pass

    def read_locale(self):
        loc_db = get_file(self.mods, "localization.csv")
        with loc_db.open("rb") as fd:
            fd.readline()
            for line in fd.readlines():
                parts = line.split(b"\t")
                ident = int(parts[0])
                name = parts[1]
                en = parts[2]
                self.locale[ident] = {
                    "name": name,
                    "text": en,
                    "id": ident
                }

    def update_get_loc(self, message_num: int) -> str:
        if not self.locale:
            self.read_locale()
        return self.locale.get(message_num, {}).get("text", "")

    def update_ui_set_text_color(self, number, color):
        self.text_color[number] = color

    def call_update(self):
        globals = self.lua.globals()
        if "screen_" in self.screen_script:
            delta_ticks = self.logic_tick - self.last_tick
            globals.update(self.w, self.h, delta_ticks)

        self.logic_tick += 3

    def run(self, screen: str):
        self.screen_script = screen
        fps = 30

        pygame.init()
        pygame.font.init()

        self.fonts[0] = pygame.font.SysFont("couriernew", 8)

        ticker = pygame.time.Clock()
        self.surface = pygame.display.set_mode((self.w, self.h), pygame.SWSURFACE | pygame.DOUBLEBUF)
        screen_script = get_file(self.mods, screen)

        # now get the library files
        files = []
        for item in LIBRARY_ORDER:
            files.append(get_file(self.mods, item))

        lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        self.lua = lua
        globals = lua.globals()
        globals.color8 = Color8
        globals.update_ui_set_back_color = self.update_ui_set_back_color
        globals.update_set_is_visible = self.update_set_is_visible
        globals.update_ui_pop_alpha = self.update_ui_pop_alpha
        globals.update_ui_push_alpha = self.update_ui_push_alpha
        globals.update_ui_get_text_size = self.update_ui_get_text_size
        globals.update_ui_set_text_color = self.update_ui_set_text_color
        globals.update_ui_text = self.update_ui_text
        globals.update_ui_rectangle = self.update_ui_rectangle
        globals.update_ui_rectangle_outline = self.update_ui_rectangle_outline

        for lua_file in files:
            lua.execute(lua_file.read_text(), name=str(lua_file.name))

        lua.execute(screen_script.read_text(), name=screen_script.name)

        try:
            globals.begin()
        except lupa.LuaError:
            pass

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
            try:
                self.call_update()
            except lupa.LuaError as err:
                print(err)

            pygame.display.update()
            ticker.tick(fps)
            if self.loading_frames > 0:
                self.loading_frames -= 1
            globals.g_is_loading = self.loading_frames > 0


        assert True