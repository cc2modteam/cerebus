"""Utility funcs and constants related to cc2"""

import re

DEFAULT_STEAMAPP_GAME_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2"
STEAM_GAME_ID = 1489630
DEFAULT_STEAMAPP_WORKSHOP_CONTENT_PATH = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\{}".format(
    STEAM_GAME_ID)


def slug_string(text: str) -> str:
    """Make a lower-case version of text without spaces or special chars"""
    return re.sub(r"[^a-z_\-0-9.]", "_", text.lower())
