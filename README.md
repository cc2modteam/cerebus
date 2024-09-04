# Cerebus CC2 Mod Developer Tool

Cerebus is the name of an island from Carrier Command 2, it's probably a typo but it's
also the name of this tool.

Cerebus is intended to aid making and publishing Carrier Command 2 mods. It provides
a quick interface for bootstrapping a new CC2 mod, creating the mod.xml file, initial 
thumbnail image and some other basic helpers.

## Plan!

The plan is that you'll be able to do..

```
c:\>users\inb> cerberus my-mod
```
And cerberus will create a skeleton empty cc2 mod in your local cc2 mods folder (eg `C:\Users\Dave\AppData\Roaming\Carrier Command 2\mods`)
with a mod.xml description file and a generated thumbnail png image of othe right size.

Other ideas are:
* using mod_sdk files (or other mods) as templates.
* validate changes to game object xml files (eg make sure scripts or meshes exist)
* tweak game object xml
  * list/alter light colours/types
  * list/alter attachment slots
  * maybe merge xml changes?