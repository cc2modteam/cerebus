"""Simulate the CC2 lua API and runtime"""
import time
import pygame
from typing import List, Optional, Tuple
from pathlib import Path
import lupa.lua53 as lupa
from ..localconfig import CFG
from .vehicles import Vehicle
from .altas_icons import get_icon_name, get_icon, get_icon_number


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
    "screen_propulsion",
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
                if suffix in [".lua", ".csv", ".ttf"]:
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
    for item in fslist:
        for fileitem in item.files:
            if fileitem.name.lower() == path.lower():
                return item.root / fileitem
    return None


class Color8:
    def __init__(self, r, g, b, a=255):
        self._r = r % 256
        self._g = g % 256
        self._b = b % 256
        self._a = a % 256

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
        self.font_x_offset = 1
        self.font_y_offset = -1
        self.visible = True
        self.screen_script = None
        self.logic_tick = 0
        self.last_tick = 0
        self.w = 128
        self.h = 128
        self.screen_vehicle: Vehicle = Vehicle(1, 0)
        self.vehicles = {}
        self.vehicles[self.screen_vehicle.get_id()] = self.screen_vehicle
        self.screen_team = 1
        self.icons = {}
        self.offset_stack = []

    def update_get_screen_team_id(self):
        return self.screen_team

    def load(self, mods: List[Path]):
        self.mods = get_filesystems(mods)

    def update_get_map_vehicle_count(self) -> int:
        return len(self.vehicles)

    def update_get_map_vehicle_by_index(self, idx) -> Optional[Vehicle]:
        vids = sorted(self.vehicles.keys())
        if idx < len(vids):
            return self.vehicles[vids[idx]]
        return None

    def update_get_logic_tick(self):
        return self.logic_tick

    def update_ui_set_back_color(self, col):
        color = col.to_color()
        self.surface.fill(color)

    def update_set_is_visible(self, truth):
        self.visible = truth

    def update_ui_pop_alpha(self):
        self.alpha_stack.pop(0)

    def update_ui_push_alpha(self, alpha):
        self.alpha_stack.insert(0, alpha)

    def update_ui_push_offset(self, x, y):
        self.offset_stack.insert(0, (x, y))

    def update_ui_pop_offset(self):
        self.offset_stack.pop(0)

    def _noop_func(self, *args, **kwargs):
        pass

    def get_offset_xy(self, x, y) -> Tuple[int, int]:
        if self.offset_stack:
            for offsets in self.offset_stack:
                x = offsets[0] + x
                y = offsets[1] + y
        return x, y

    def update_ui_get_text_size(self, text, cols, lines):
        return min(cols, 24) * 10, lines * 8

    def update_self_destruct_override(self, screen_w, screen_h):
        return False

    def update_get_screen_vehicle(self) -> Vehicle:
        return self.screen_vehicle

    def update_get_vehicle_by_id(self, vid) -> Optional[Vehicle]:
        return self.vehicles.get(vid, None)

    def get_loaded_image(self, icon_name) -> pygame.Surface:
        if icon_name not in self.icons:
            icon_file = get_icon(CFG.mod_dev_kit, icon_name)
            loaded_img = pygame.image.load(icon_file)
            self.icons[icon_name] = loaded_img
        return self.icons[icon_name]

    def update_ui_image(self, x: int, y: int, img: int, col: Color8, unused):
        # 0, 0, atlas_icons.screen_compass_background, color_white, 0)
        x, y = self.get_offset_xy(x, y)
        icon_name = get_icon_name(img)
        icon = self.get_loaded_image(icon_name)
        color = col.to_color()
        blend = pygame.BLEND_RGBA_MIN
        if icon_name == "screen_propulsion_carrier":
            # hack
            blend = pygame.BLEND_RGB_ADD
        icon.fill(color, special_flags=blend)

        self.surface.blit(icon, (x, y))

    def update_ui_image_rot(self, x: int, y: int, img: int, col: Color8, angle: float):
        x, y = self.get_offset_xy(x, y)
        icon_name = get_icon_name(img)
        icon = self.get_loaded_image(icon_name)
        color = col.to_color()
        icon.fill(color, special_flags=pygame.BLEND_RGBA_MIN)

        rotated = pygame.transform.rotate(icon, angle)
        new_rect = rotated.get_rect(
            center=icon.get_rect(center=(x + self.font_x_offset, y + self.font_y_offset)).topleft)

    def update_ui_text(self, x, y, text, w, j, color, rot):
        if isinstance(text, int):
            text = self.update_get_loc(text)
        col = color.to_color()
        x, y = self.get_offset_xy(x, y)
        lpad = 0
        span = int(w / 8)
        length = len(text)
        if j == 1:
            # center
            lpad = int((span - length) / 2)
        if j == 2:
            # right
            lpad = int(span - length)
        lpad = lpad * 4
        text = f"{' '*lpad}{text}"
        surf = self.fonts[0].render(text, False, col)

        if rot > 0:
            rotated = pygame.transform.rotate(surf, -90 * rot)
            new_rect = rotated.get_rect(bottomleft=surf.get_rect(topleft=(x + self.font_x_offset - 2, y + self.font_y_offset)).topleft)
        else:
            rotated = surf
            new_rect = rotated.get_rect(topleft=(x + self.font_x_offset, y + self.font_y_offset))
        self.surface.blit(rotated, new_rect)

    def clear(self):
        pygame.draw.rect(self.surface, (0, 0, 0),
                         pygame.Rect(0, 0, self.w, self.h))

    def update_ui_rectangle(self, x, y, w, h, col):
        x, y = self.get_offset_xy(x, y)
        color = col.to_color()
        pygame.draw.rect(self.surface, color,
                         pygame.Rect(x, y, w, h))

    def update_ui_line(self, ax, ay, bx, by, col):
        ax, ay = self.get_offset_xy(ax, ay)
        bx, by = self.get_offset_xy(bx, by)
        pygame.draw.line(self.surface, col.to_color(), (ax, ay), (bx, by), 1)

    def begin_get_ui_region_index(self, name):
        return get_icon_number(name)

    def update_ui_rectangle_outline(self, x, y, w, h, col):
        x, y = self.get_offset_xy(x, y)
        pygame.draw.rect(self.surface, col.to_color(),
                         pygame.Rect(x, y, w, h), 1)

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

    def update_get_active_input_type(self):
        # keyboard = 0
        # gamepad = 1
        return 0

    def update_get_screen_input(self, device):
        return False

    def update_ui_set_text_color(self, number, color):
        self.text_color[number] = color

    def call_update(self):
        self.logic_tick = self.logic_tick + 1
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
        lanapixel = get_file(self.mods, "lanapixel.ttf")
        # font = pygame.font.SysFont("dejavusansmono", 12)
        font = pygame.font.Font(lanapixel, 10)
        self.fonts[0] = font

        ticker = pygame.time.Clock()
        self.surface = pygame.display.set_mode((self.w, self.h),
                                               pygame.SWSURFACE | pygame.DOUBLEBUF | pygame.SCALED | pygame.RESIZABLE)

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
        globals.update_self_destruct_override = self.update_self_destruct_override
        globals.update_get_screen_vehicle = self.update_get_screen_vehicle
        globals.update_get_vehicle_by_id = self.update_get_vehicle_by_id
        globals.update_ui_image = self.update_ui_image
        globals.update_ui_image_rot = self.update_ui_image_rot
        globals.begin_get_ui_region_index = self.begin_get_ui_region_index
        globals.update_get_loc = self.update_get_loc
        globals.update_get_active_input_type = self.update_get_active_input_type
        globals.update_ui_push_offset = self.update_ui_push_offset
        globals.update_ui_pop_offset = self.update_ui_pop_offset
        globals.update_get_screen_input = self.update_get_screen_input
        globals.update_get_logic_tick = self.update_get_logic_tick
        globals.update_ui_line = self.update_ui_line
        globals.update_get_map_vehicle_count = self.update_get_map_vehicle_count
        globals.update_get_screen_team_id = self.update_get_screen_team_id
        globals.update_get_map_vehicle_by_index = self.update_get_map_vehicle_by_index

        # noops
        globals.update_ui_push_clip = self._noop_func
        globals.update_ui_pop_clip = self._noop_func
        globals.update_set_screen_background_type = self._noop_func
        globals.update_set_screen_camera_pos_orientation = self._noop_func
        globals.update_set_screen_camera_attach_vehicle = self._noop_func

        for lua_file in files:
            lua.execute(lua_file.read_text(), name=str(lua_file.name))

        lua.execute(screen_script.read_text(), name=screen_script.name)

        try:
            globals.begin()
        except (lupa.LuaError, TypeError):
            pass

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
            try:
                self.clear()
                self.call_update()
            except lupa.LuaError as err:
                print(err)
            pygame.display.update()
            ticker.tick(fps)
            if self.loading_frames > 0:
                self.loading_frames -= 1
            globals.g_is_loading = self.loading_frames > 0


        assert True