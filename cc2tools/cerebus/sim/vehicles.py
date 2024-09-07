import time
import math

def variable_generator(div, vmin, vmax) -> float:
    v = math.fabs(math.sin(time.monotonic())) / div
    v = min(v, vmax)
    v = max(v, vmin)
    return v

class Vehicle:

    def __init__(self, vid: int = 0, vdef = 0, team = 1):
        self._id = vid
        self._vdef = vdef
        self._team = team

    def get_team(self) -> int:
        return self._team

    def get_id(self) -> int:
        return self._id

    def get(self) -> bool:
        return True

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

    def get_definition_index(self) -> int:
        return self._vdef

    def get_waypoint_count(self) -> int:
        return 0


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