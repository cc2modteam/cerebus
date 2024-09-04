"""Cerebus - a tool for creating Carrier Command 2 mods"""
from argparse import ArgumentParser, Namespace
from .localconfig import CFG
from .mod_xml import ModXml
from .thumbnail import make_thumb
from .sdk.utils import slug_string


def list_local_mods(opts: Namespace):
    mods_dir = CFG.mods
    enabled = CFG.active_mod_folders()
    local_mods = CFG.local_mod_folders()
    for item in local_mods:
        mod_xml = item / "mod.xml"
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
    xml.write()
    (mod_folder / "content").mkdir()

    thumb = make_thumb(opts.NAME)
    thumb_png = mod_folder / "thumbnail.png"
    thumb.save(thumb_png)


parser = ArgumentParser(description=__doc__)
subs = parser.add_subparsers()

parser_list_local = subs.add_parser("local-mods")
parser_list_local.set_defaults(func=list_local_mods)

parser_new = subs.add_parser("new")
parser_new.add_argument("NAME", type=str, help="Name for your new mod")
parser_new.set_defaults(func=new_mod)


def run(args=None):
    opts = parser.parse_args()
    func = opts.func
    if func:
        func(opts)


if __name__ == "__main__":
    run()
