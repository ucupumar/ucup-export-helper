import bpy
from .common import *

WIDGET_COLLECTION_NAME = 'HeroTPPWidgets'

def load_rigify_script():

    filepath = get_addon_filepath() + 'lib.blend'
    data_name = 'rig_ui.py'

    # Exist data
    exist_datas = [data.name for data in bpy.data.texts]

    # Load new data
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        # Append new data
        data_to.texts.append(data_name)

    # Check just added data
    data = None
    if data_name not in exist_datas:
        data = bpy.data.texts.get(data_name)
    else:
        # If data already available
        added_datas = [data for data in bpy.data.texts if data.name not in exist_datas]
        if added_datas:
            data = added_datas[0]

    return data

def load_ue4_hero_tpp():

    blendfile = get_addon_filepath() + 'lib.blend'
    mesh_obj = None
    metarig_obj = None

    metarig_name = 'hero_metarig'
    mesh_name = 'HeroTPP'

    with bpy.data.libraries.load(blendfile, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name in {metarig_name, mesh_name}]
    
    # 2. Link the imported object to the active scene collection
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)

            if obj.name.startswith(mesh_name):
                mesh_obj = obj
            elif obj.name.startswith(metarig_name):
                metarig_obj = obj
    
    return metarig_obj, mesh_obj

class AddHeroTPP(bpy.types.Operator):
    bl_idname = "object.add_standard_ue4_tpp"
    bl_label = "Add Standard UE4 TPP"
    bl_description = "Add standard UE4 Third Person Character with Rigify"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not hasattr(bpy.ops.pose, 'rigify_generate'):
            self.report({'ERROR'}, "Rigify addon need to be installed!")
            return {'CANCELLED'}

        scene = context.scene
        metarig_obj, mesh_obj = load_ue4_hero_tpp()

        # Select metarig
        set_active(metarig_obj)
        select_set(metarig_obj, True)
        select_set(mesh_obj, True)

        # Update metarig for Blender 4.0 or above
        if is_bl_newer_than(4):
            bpy.ops.armature.rigify_upgrade_layers()

        # Generate rigify
        bpy.ops.pose.rigify_generate()
        rig = context.object

        # Set armature
        mod = mesh_obj.modifiers.get('Armature')
        if mod: mod.object = rig
        mesh_obj.parent = rig

        # Set location
        rig.location = cursor_location_get().copy()

        # Remove metarig
        bpy.data.objects.remove(metarig_obj)

        return {'FINISHED'}

class UE4HELPER_PT_NewObjectsPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_context = "objectmode"
    bl_label = "Add New Objects"
    bl_category = "Ucup Exporter"

    def draw(self, context):
        c = self.layout.column(align=True)
        c.operator("object.add_standard_ue4_tpp", text="Add UE4 TPP Mesh", icon='ARMATURE_DATA')

def register():
    bpy.utils.register_class(AddHeroTPP)
    bpy.utils.register_class(UE4HELPER_PT_NewObjectsPanel)

def unregister():
    bpy.utils.unregister_class(AddHeroTPP)
    bpy.utils.unregister_class(UE4HELPER_PT_NewObjectsPanel)
