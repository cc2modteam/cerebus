"""Simulate the CC2 lua API and runtime"""
import sys
import time

import pygame
from typing import List, Optional, Tuple
from pathlib import Path
import lupa.lua53 as lupa

from .inputs import e_input, e_input_action, e_active_input
from ..localconfig import CFG
from .vehicles import Vehicle, HudVehicle, ScreenVehicle, StaleVehicle
from .altas_icons import get_icon_name, get_icon, get_icon_number
from .common_types import Vec2, Tile, Color8, RUNTIME, StaleTile
from .inventory import update_get_resource_inventory_category_count, update_get_resource_inventory_category_data

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
    "screen_vehicle_control",
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


class Simulator:
    def __init__(self):
        self.mods: List[FileSystem] = []
        self.lua = None
        self.screen_surface = None
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
        self.screen_name = "screen_name"
        self.logic_tick = 0
        self.last_tick = 0
        self.w = 128
        self.h = 128
        self.screen_vehicle = None
        self.vehicles = {}
        self.screen_team = 1
        self.icons = {}
        self.offset_stack = []
        self.called_begin = False
        self.cam_pos = Vec2(0, 0)
        self.cam_size = 10000
        self.interactions = {}
        self.tiles = [
            Tile(0, 0, 1),
            Tile(9000, 12340, 2),
        ]
        self.mouse_down = False
        self.mouse_down_start = (0, 0)
        self.mouse_pos = (0, 0)

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
        return StaleVehicle()

    def update_get_map_vehicle_by_id(self, v_id) -> Optional[Vehicle]:
        for v in self.vehicles.values():
            if v.get_id() == v_id:
                return v
        return StaleVehicle()

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

    def update_ui_get_offset(self):
        return self.get_offset_xy(0, 0)

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

    def update_ui_text(self, x, y, text, w, j, color, rot) -> int:
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
        return 8

    def clear(self):
        self.surface.fill((0, 0, 0, 255))
        #pygame.draw.rect(self.surface, (0, 0, 0, 255),
        #                 pygame.Rect(0, 0, self.w, self.h))

    def update_ui_rectangle(self, x, y, w, h, col):
        x, y = self.get_offset_xy(x, y)
        color = col.to_color()
        pygame.draw.rect(self.surface, color,
                         pygame.Rect(x, y, w, h))

    def update_ui_line(self, ax, ay, bx, by, col):
        ax, ay = self.get_offset_xy(ax, ay)
        bx, by = self.get_offset_xy(bx, by)
        pcol = col.to_color()
        pygame.draw.line(self.surface, pcol, (ax, ay), (bx, by), 1)

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
        text = self.locale.get(message_num)
        if text:
            return text["text"]
        return bytes()

    def update_get_active_input_type(self):
        # keyboard = 0
        # gamepad = 1
        return 0

    def update_get_screen_input(self, device):
        return False

    def update_ui_set_text_color(self, number, color):
        self.text_color[number] = color

    def is_screen(self) -> bool:
        return "screen_" in self.screen_script

    def is_hud(self) -> bool:
        return "vehicle_hud" in self.screen_script

    def call_update(self):
        self.logic_tick = self.logic_tick + 1
        lua_globals = self.lua.globals()
        if self.is_screen():
            delta_ticks = self.logic_tick - self.last_tick
            lua_globals.update(self.w, self.h, delta_ticks)


        self.screen_surface.fill((0,0,0,255))
        self.screen_surface.blit(self.surface, (0, 0))
        self.screen_surface.fill((24, 24, 24), special_flags=pygame.BLEND_RGB_ADD)
        self.logic_tick += 1

    def update_get_tile_count(self):
        return len(self.tiles)

    def update_get_tile_by_index(self, idx):
        assert idx < len(self.tiles)
        return self.tiles[idx]

    def update_get_tile_by_id(self, tile_id):
        for tile in self.tiles:
            if tile.get_id() == tile_id:
                return tile
        return StaleTile(999, 999, 999)

    def update_get_team_color(self, team_idx) -> Color8:
        if team_idx == 0:
            return Color8(255, 0, 0, 255)
        return Color8(0 + 16 * team_idx, 0 + 32 * team_idx, 48 + 8 * team_idx, 255)

    def run(self, screen: str):
        self.screen_script = screen
        fps = 30
        if self.is_screen() and "control" in screen:
            self.w = 256
            self.h = 256

        pygame.init()
        pygame.font.init()
        lanapixel = get_file(self.mods, "lanapixel.ttf")
        # font = pygame.font.SysFont("dejavusansmono", 12)
        font = pygame.font.Font(lanapixel, 10)
        self.fonts[0] = font

        ticker = pygame.time.Clock()

        self.screen_surface = pygame.display.set_mode((self.w, self.h),
                                               pygame.SWSURFACE | pygame.DOUBLEBUF | pygame.SCALED | pygame.RESIZABLE | pygame.SRCALPHA)
        self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        screen_script = get_file(self.mods, screen)

        if self.is_hud():
            self.screen_vehicle = HudVehicle(3, 10) # manta
        else:
            self.screen_vehicle: Vehicle = ScreenVehicle(1, 0)  # carrier
            barge = ScreenVehicle(31, 16)
            barge._x = -3000
            barge._z = 450
            self.vehicles[barge.get_id()] = barge

            fish = ScreenVehicle(19, 77)
            fish._x = 4000
            fish._z = 1900
            self.vehicles[fish.get_id()] = fish

        self.vehicles[self.screen_vehicle.get_id()] = self.screen_vehicle

        # now get the library files
        files = []
        for item in LIBRARY_ORDER:
            files.append(get_file(self.mods, item))

        lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        RUNTIME.runtime = lua

        self.lua = lua
        lua_globals = lua.globals()
        lua_globals.color8 = Color8
        lua_globals.vec2 = Vec2
        lua_globals.update_ui_set_back_color = self.update_ui_set_back_color
        lua_globals.update_set_is_visible = self.update_set_is_visible
        lua_globals.update_ui_pop_alpha = self.update_ui_pop_alpha
        lua_globals.update_ui_push_alpha = self.update_ui_push_alpha
        lua_globals.update_ui_get_text_size = self.update_ui_get_text_size
        lua_globals.update_ui_set_text_color = self.update_ui_set_text_color
        lua_globals.update_ui_text = self.update_ui_text
        lua_globals.update_ui_rectangle = self.update_ui_rectangle
        lua_globals.update_ui_rectangle_outline = self.update_ui_rectangle_outline
        lua_globals.update_self_destruct_override = self.update_self_destruct_override
        lua_globals.update_get_screen_vehicle = self.update_get_screen_vehicle
        lua_globals.update_get_vehicle_by_id = self.update_get_vehicle_by_id
        lua_globals.update_ui_image = self.update_ui_image
        lua_globals.update_ui_image_rot = self.update_ui_image_rot
        lua_globals.begin_get_ui_region_index = self.begin_get_ui_region_index
        lua_globals.update_get_loc = self.update_get_loc
        lua_globals.update_get_active_input_type = self.update_get_active_input_type
        lua_globals.update_ui_push_offset = self.update_ui_push_offset
        lua_globals.update_ui_pop_offset = self.update_ui_pop_offset
        lua_globals.update_ui_get_offset = self.update_ui_get_offset
        lua_globals.update_get_screen_input = self.update_get_screen_input
        lua_globals.update_get_logic_tick = self.update_get_logic_tick
        lua_globals.update_ui_line = self.update_ui_line
        lua_globals.update_get_map_vehicle_count = self.update_get_map_vehicle_count
        lua_globals.update_get_screen_team_id = self.update_get_screen_team_id
        lua_globals.update_get_map_vehicle_by_index = self.update_get_map_vehicle_by_index
        lua_globals.update_get_map_vehicle_by_id = self.update_get_map_vehicle_by_id

        lua_globals.update_get_team_color = self.update_get_team_color
        lua_globals.update_get_map_destroyed_vehicle_count = self.zero_func
        lua_globals.update_get_is_multiplayer = lambda : True

        # tiles
        lua_globals.update_get_tile_count = self.update_get_tile_count
        lua_globals.update_get_tile_by_index = self.update_get_tile_by_index
        lua_globals.update_get_tile_by_id = self.update_get_tile_by_id


        # noops
        lua_globals.update_ui_push_clip = self._noop_func
        lua_globals.update_ui_pop_clip = self._noop_func
        lua_globals.update_set_screen_background_type = self._noop_func
        lua_globals.update_set_screen_camera_pos_orientation = self._noop_func
        lua_globals.update_set_screen_camera_attach_vehicle = self._noop_func
        lua_globals.update_get_missile_count = self.zero_func
        lua_globals.update_ui_begin_triangles = self._noop_func
        lua_globals.update_ui_add_triangle = self._noop_func
        lua_globals.update_ui_end_triangles = self._noop_func
        lua_globals.update_get_is_vr = lambda : False
        lua_globals.update_interaction_ui = self._noop_func
        if self.is_screen():
            self.add_screen_funcs(lua_globals)

        self.add_interaction_funcs(lua_globals)

        for lua_file in files:
            lua.execute(lua_file.read_text(), name=str(lua_file.name))

        lua.execute(screen_script.read_text(), name=screen_script.name)

        try:
            lua_globals.begin()
            self.called_begin = True
        except (lupa.LuaError, TypeError) as err:
            print(err)
            sys.exit(1)

        last_mouse_pos = (0, 0)
        while True:
            wheel = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.mouse_down:
                        btn = pygame.mouse.get_pressed(5)
                        if btn[0]:
                            self.mouse_down = True
                            self.mouse_down_start = pygame.mouse.get_pos()
                            self.mouse_pos = self.mouse_down_start
                            lua_globals.input_event(e_input.pointer_1, e_input_action.press)
                elif event.type == pygame.MOUSEBUTTONUP:
                    btn = pygame.mouse.get_pressed(5)
                    if self.mouse_down and not btn[0]:
                        self.mouse_down = False
                        lua_globals.input_event(e_input.pointer_1, e_input_action.release)
                elif event.type == pygame.MOUSEMOTION:
                    mouse = pygame.mouse.get_pos()
                    self.mouse_pos = mouse

                elif event.type == pygame.MOUSEWHEEL:
                    if event.y != 0:
                        wheel = event.y


            if not self.is_hud():
                hover = last_mouse_pos == self.mouse_pos
                lua_globals.input_pointer(hover, self.mouse_pos[0], self.mouse_pos[1])
                last_mouse_pos = self.mouse_pos
                if wheel:
                    lua_globals.input_scroll(wheel)

            try:
                self.clear()
                self.call_update()
            except lupa.LuaError as err:
                print(err)
                sys.exit(1)

            pygame.display.update()
            ticker.tick(fps)
            if self.loading_frames > 0:
                self.loading_frames -= 1
            lua_globals.g_is_loading = self.loading_frames > 0


    def zero_func(self) -> int:
        return 0

    def begin_get_screen_name(self):
        return self.screen_name

    def update_set_screen_map_position_scale(self, cam_x, cam_y, cam_size):
        self.cam_pos._x = cam_x
        self.cam_pos._y = cam_y
        self.cam_size = cam_size

    def add_screen_funcs(self, lua_globals):
        lua_globals.update_get_resource_inventory_item_count = lambda: 0   # cargo
        lua_globals.e_input = e_input
        lua_globals.e_input_action = e_input_action
        lua_globals.e_active_input = e_active_input
        lua_globals.update_get_resource_inventory_category_count = update_get_resource_inventory_category_count
        lua_globals.update_get_resource_inventory_category_data = update_get_resource_inventory_category_data
        lua_globals.begin_get_screen_name = self.begin_get_screen_name
        lua_globals.update_set_screen_vehicle_control_id = self._noop_func
        lua_globals.update_set_screen_map_position_scale = self.update_set_screen_map_position_scale
        lua_globals.update_set_screen_background_is_render_islands = self._noop_func
        lua_globals.update_get_is_focus_local = lambda : True
        lua_globals.update_get_weapon_line_count = lambda : 0
        lua_globals.update_get_peer_is_admin = lambda x: False

    def update_add_ui_interaction(self, text, keystroke):
        if text not in self.interactions:
            self.interactions[text] = keystroke
            print(f"UI {text} {keystroke}")

    def update_add_ui_interaction_special(self, text, keystroke):
        if text not in self.interactions:
            self.interactions[text] = keystroke
            print(f"UI special {text} {keystroke}")

    def add_interaction_funcs(self, lua_globals):
        lua_globals.update_add_ui_interaction = self.update_add_ui_interaction
        lua_globals.update_add_ui_interaction_special = self.update_add_ui_interaction_special