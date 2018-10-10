bl_info = {
    "name": "Unreal Engine 4 Export Helper",
    "author": "Yusuf Umar",
    "version": (0, 0, 0),
    "blender": (2, 79, 0),
    "location": "View 3D > Tool Shelf > UE4 Helper",
    "description": "Tool to help exporting something to UE4 less pain in the a**",
    "wiki_url": "http://twitter.com/ucupumar",
    "category": "Import-Export",
}

if "bpy" not in locals():
    from . import common, ue4, hero_tpp
else:
#if "bpy" in locals():
    import imp
    imp.reload(common)
    imp.reload(ue4)
    imp.reload(hero_tpp)

import bpy

def register():
    ue4.register()
    hero_tpp.register()

def unregister():
    ue4.unregister()
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
