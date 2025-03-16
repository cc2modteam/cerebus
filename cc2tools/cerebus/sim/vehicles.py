import time
import math
from .common_types import Vec2, Waypoint, RUNTIME, Attachment


def variable_generator(div, vmin, vmax) -> float:
    v = math.fabs(math.sin(time.monotonic())) / div
    v = min(v, vmax)
    v = max(v, vmin)
    return v

class Vehicle:

    hud_mode = False

    def __init__(self, vid: int = 0, vdef = 0, team = 1):
        self._id = vid
        self._vdef = vdef
        self._team = team
        self.parent = 0
        self.hitpoints = 100
        self.max_hitpoints = 100
        self.fuel = 420
        self.max_fuel = 1000
        self.ammo = 120
        self.max_ammo = 200
        self._x = 0
        self._z = 0
        self._alt = 5
        self.waypoints = []

    def get_ammo_factor(self):
        return self.ammo / self.max_ammo

    def get_fuel_factor(self):
        return self.fuel / self.max_fuel

    def get_hitpoints(self):
        return self.hitpoints

    def get_total_hitpoints(self):
        return self.max_hitpoints

    def get_team(self) -> int:
        return self._team

    def get_id(self) -> int:
        return self._id

    def get(self) -> bool:
        return True

    def get_definition_index(self) -> int:
        return self._vdef

    def get_is_observation_revealed(self) -> bool:
        return True

    def get_is_visible(self) -> bool:
        return True

    def get_damage_indicator_factor(self) -> float:
        return self.hitpoints / self.max_hitpoints

    def get_controlling_peer_id(self):
        return 0


class HudVehicle(Vehicle):
    hud_mode = True


class ScreenVehicle(Vehicle):
    def get_self_destruct_mode(self) -> int:
        #     locked = 0,
        #     input = 1,
        #     ready = 2,
        #     countdown = 3,
        return 0

    def get_rotation_x(self) -> float:
        return variable_generator(10, -0.9, 0.9)

    def get_rotation_y(self) -> float:
        return variable_generator(10, -0.9, 0.9)

    def get_rotation_z(self) -> float:
        return variable_generator(10, -0.9, 0.9)

    def get_is_visible_by_enemy(self) -> bool:
        now = int(time.time())  % 40
        return now > 30

    def get_is_hold_fire(self):
        return False

    def get_resupply_vehicle_id(self):
        return 0

    def get_power_system_state(self, pwr_sys):
        # pwr_sys =
        # repair,
        # propulsion
        # weapons,
        # crane,
        # radar
        now = time.monotonic()
        value = math.sin(now % (360 + 3 * pwr_sys)) * 0.5

        return value, value

    def get_carrier_is_reverse(self) -> bool:
        return (time.monotonic() % 20) > 18

    def get_carrier_is_side_thruster(self) -> bool:
        return (time.monotonic() % 30) > 22

    def get_velocity_magnitude(self) -> float:
        return 0.52 + (time.monotonic() % 7) / 10

    def get_carrier_control_factors(self):
        return ControlFactors(variable_generator(7.0, 0.1, 0.5),
                              variable_generator(3.0, 0.1, 0.9),
                              variable_generator(4.0, 0.1, 0.8))

    def get_carrier_is_engine_on(self) -> bool:
        return time.monotonic() % 200 > 10

    def get_waypoint_count(self) -> int:
        return len(self.waypoints)

    def get_waypoint_by_id(self, wid):
        for w in self.waypoints:
            if w._id == wid:
                return w
        return Waypoint(invalid=True)

    def get_waypoint(self, idx):
        return self.waypoints[idx]

    def add_waypoint(self, x, z):
        w = Waypoint()
        w._x = x
        w._z = z
        self.waypoints.append(w)
        return w.get_id()

    def set_waypoint_attack_target_target_id(self, wid, tid):
        pass

    def set_waypoint_attack_target_attack_type(self, wid, tidx, atype):
        pass

    def get_attack_target_type(self):
        return 0 # none

    def clear_waypoints(self):
        self.waypoints.clear()

    def clear_waypoints_from(self, wid):
        old = list(self.waypoints)
        self.clear_waypoints()
        stop = False
        for w in old:
            if w.get_id() != wid:
                self.waypoints.append(w)
                stop = True
            elif stop:
                self.waypoints.append(w)
                break

    def get_waypoint_path(self):
        path = RUNTIME.runtime.table()
        for w in self.waypoints:
            path[1 + len(path)] = w.get_position_xz()
        return path

    def clear_attack_target(self):
        pass

    def get_position_xz(self) -> Vec2:
        return Vec2(self._x, self._z)

    def get_attached_parent_id(self) -> int:
        return self.parent

    def get_attached_vehicle_id(self, bay) -> int:
        return 0

    def get_supporting_vehicle_id(self) -> int:
        return 0

    def get_dock_queue_vehicle_id(self):
        return 0

    def get_resupplying_vehicle_id_count(self):
        return 0

    def get_special_id(self):
        return 0

    def get_direction(self) -> Vec2:
        x = variable_generator(1, -1, 1)
        size = abs(x)
        z = 1 - size
        return Vec2(x, z)

    def get_is_docked(self) -> bool:
        return self.parent != 0

    def get_dock_state(self):
        return 0 # undocked

    def get_attachment_count(self) -> int:
        return 0

    def get_attachment_type(self, idx):
        return 0

    def get_attachment(self, idx):
        return Attachment()

    def get_repair_factor(self):
        return self.get_damage_indicator_factor()

    def get_is_observation_type_revealed(self):
        return True

    def get_is_observation_fully_revealed(self):
        return True

    def get_is_observation_weapon_revealed(self):
        return True


class StaleVehicle(Vehicle):
    def get(self):
        return False


class ControlFactors:
    def __init__(self, x, y, w):
        self._x = x
        self._y = y
        self._w = w

    def w(self):
        return self._w

    def x(self):
        return self._x

    def y(self):
        return self._y