
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