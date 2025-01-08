"""Cerebus - a tool for creating Carrier Command 2 mods"""
import getpass
from argparse import ArgumentParser, Namespace
from .localconfig import CFG
from .mod_xml import ModXml
from .thumbnail import make_thumb
from .sdk.utils import slug_string
from .sim import cc2


def list_local_mods(opts: Namespace):
    enabled = CFG.active_mod_folders()
    local_mods = CFG.local_mod_folders()
    for item in local_mods:
        folder_name = item.name
        mod = ModXml()
        mod.read(item)
        enabled_mod = " "
        if item in enabled:
            enabled_mod = "*"
        print(f"{enabled_mod} {folder_name} ({mod.name})")


def new_mod(opts: Namespace):
    slug = slug_string(opts.NAME)
    mods = CFG.mods
    mod_folder = mods / slug
    mod_folder.mkdir()
    xml = ModXml(mod_folder)
    xml.name = opts.NAME
    xml.author = getpass.getuser()
    xml.description = "A new CC2 Mod"
    xml.write()
    (mod_folder / "content").mkdir()

    thumb = make_thumb(opts.NAME)
    thumb_png = mod_folder / "thumbnail.png"
    thumb.save(thumb_png)


def start_sim(opts: Namespace):
    sim = cc2.Simulator()
    mods = opts.mod
    if not mods:
        mods = CFG.active_mod_folders()
    sim.load(mods)
    sim.run(f"{opts.SCREEN}.lua")


parser = ArgumentParser(description=__doc__)
subs = parser.add_subparsers()

parser_list_local = subs.add_parser("local-mods")
parser_list_local.set_defaults(func=list_local_mods)

parser_new = subs.add_parser("new")
parser_new.add_argument("NAME", type=str, help="Name for your new mod")
parser_new.set_defaults(func=new_mod)

parser_sim = subs.add_parser("sim")
parser_sim.add_argument("--mod", type=str, action="append")
parser_sim.add_argument("SCREEN", choices=cc2.SCREENS)
parser_sim.set_defaults(func=start_sim)


def run(args=None):
    opts = parser.parse_args()
    if hasattr(opts, "func"):
        func = opts.func
        if func:
            func(opts)
    else:
        parser.print_usage()


if __name__ == "__main__":
    run()
