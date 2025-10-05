import pygame


class Vec2:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x(self) -> float:
        return self._x

    def y(self) -> float:
        return self._y


class Tile:
    def __init__(self, x, z, tile_id):
        self.x = x
        self.z = z
        self.id = tile_id
        self.team = 1
        self.turret_spawns = [
            (x + 32, z + 1),
            (x - 45, z - 64),
            (x - 120, z + 80),
            (x + 500, z - 192)
        ]

    def get(self):
        return True

    def get_id(self) -> int:
        return self.id

    def get_team_control(self) -> int:
        return self.team

    def get_command_center_count(self) -> int:
        return 1

    def get_command_center_position(self, cc_idx):
        return Vec2(self.x + 120, self.z - 230)

    def get_facility_production_queue_defense_count(self) -> int:
        return 0

    def get_team_capture(self) -> bool:
        return False

    def get_team_capture_progress(self) -> float:
        return 0

    def get_position_xz(self):
        return Vec2(self.x, self.z)

    def get_name(self):
        return f"TILE {self.id}"

    def get_facility_category(self):
        return 0 # 0 = Warehouse

    def get_turret_spawn_count(self):
        return len(self.turret_spawns)

    def get_turret_spawn(self, idx):
        return idx, idx < len(self.turret_spawns)

    def get_marker_position(self, idx):
        assert idx < len(self.turret_spawns)
        return Vec2(self.turret_spawns[idx][0], self.turret_spawns[idx][1])

    def get_facility_production_queue_defense_count(self):
        return 0




class StaleTile(Tile):

    def get(self):
        return False


class Color8:
    def __init__(self, r, g, b, a):
        if a is None:
            a = 255
        self._r = r % 256
        self._g = g % 256
        self._b = b % 256
        self._a = a % 256

    def to_color(self) -> pygame.Color:
        value = pygame.Color(self._r, self._g, self._b)
        value.a = self.a()
        return value

    def r(self):
        return self._r

    def g(self):
        return self._g

    def b(self):
        return self._b

    def a(self):
        return self._a


class Waypoint:

    next_id = 0

    def __init__(self, invalid=False):
        self._x = 0
        self._z = 0
        self._alt = 0
        self._id = self.next_id
        self.next_id += 1
        if invalid:
            self._id = -1

        self.waits = {}

    def get(self):
        return self._id > -1

    def get_altitude(self):
        return self._alt

    def get_position_xz(self, *args):
        return Vec2(self._x, self._z)

    def get_id(self):
        return self._id

    def get_repeat_index(self):
        return -1

    def get_attack_target_count(self):
        return 0

    def get_type(self):
        return 0 # move

    def get_is_wait_group(self, grp):
        return self.waits.get(grp, False)


class Attachment:
    def __init__(self):
        self.adef = 0

    def get_definition_index(self):
        return self.adef

    def get(self):
        return False


class Team:
    def __init__(self, teamid = 1):
        self.id = teamid
        self.currency = 1200

    def get(self):
        return True

    def get_currency(self):
        return self.currency



class RT:
    def __init__(self):
        self.runtime = None


RUNTIME = RT()