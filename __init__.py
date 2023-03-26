bl_info = {
    "name": "Ucup Export Helper",
    "author": "Yusuf Umar, Przemysław Bągard",
    "version": (0, 0, 0),
    "blender": (3, 4, 0),
    "location": "View 3D > Tool Shelf > Ucup Exporter",
    "description": "Tool to help exporting things to Godot",
    "wiki_url": "http://twitter.com/ucupumar",
    "category": "Import-Export",
}

if "bpy" in locals():
    import imp
    imp.reload(common)
    imp.reload(ue4)
    imp.reload(godot)
    imp.reload(actions)
    imp.reload(hero_tpp)
else:
    from . import common, ue4, godot, actions, hero_tpp

import bpy

def register():
    ue4.register()
    godot.register()
    actions.register()
    hero_tpp.register()

def unregister():
    ue4.unregister()
    godot.unregister()
    actions.unregister()
    hero_tpp.unregister()

if __name__ == "__main__":
    register()

# TODO:
# Deals with double neck (V)
# Deals with single limb bone (V)
# Add humanoid metarig settings (X)
# - Number of limb bones
# - Number of neck bones
# - Fingers (thumb, other fingers, palms)
# - Breast 
# - Extra hip bones
# - Face
# Add exception bone option (V)
# Detect non rigify rig (V)
# Deals with non rigify bone (V)
# Add export mesh exception (V)
# Support for old rigify
# Batch export skeletal mesh and actions
# Support for static mesh
# Make UE4 TPP action can be used using original unreal TPP rig
