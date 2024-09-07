import time
import math

class Vehicle:

    def __init__(self, vid: int = 0):
        self._id = vid

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
        return 0.0

    def get_rotation_y(self) -> float:
        return 0.0

    def get_rotation_z(self) -> float:
        return 0.0

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
