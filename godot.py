import bpy, sys
from bpy.props import *
from bpy_extras.io_utils import (ExportHelper,
                                 #orientation_helper_factory,
                                 #path_reference_mode,
                                 axis_conversion,
                                 ) 
from .common import *

class ExportRigifyDAE(bpy.types.Operator, ExportHelper):
    bl_idname = "export_mesh.rigify_dae"
    bl_label = "Export Godot Skeleton"
    bl_description = "Export rigify mesh as Godot skeleton DAE file"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".dae"
    filter_glob = StringProperty(default="*.dae", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return get_current_armature_object()

    def execute(self, context):

        scene_props = context.scene.gr_props

        if not hasattr(bpy.types, "EXPORT_SCENE_OT_dae"):
            self.report({'ERROR'}, "Better Collada addon need to be installed")
            return {'CANCELLED'}

        #print(sys.modules[bpy.types.EXPORT_SCENE_OT_dae.__module__].__file__)
        #print(sys.modules[bpy.types.EXPORT_SCENE_OT_dae.__module__].__path__[0])

        # Create save system to save current selection, mode, and active object
        state = SaveState(context)

        # Import better collada module
        #sys.path.append(sys.modules[bpy.types.EXPORT_SCENE_OT_dae.__module__].__path__[0])
        #import export_dae

        #print(locals())
        #print(export_dae.DaeExporter)

        # Evaluate selected objects to export
        rig_object, mesh_objects, failed_mesh_objects, error_messages = evaluate_and_get_source_data(
                context.scene, context.selected_objects)

        # If valid mesh isn't found
        #if not mesh_objects:
        if error_messages != '':
            state.load(context)
            self.report({'ERROR'}, error_messages)
            return{'CANCELLED'}

        # Remember rig object original matrices and original action
        quaternions = {}
        scales = {}
        locations = {}
        for pb in rig_object.pose.bones:
            quaternions[pb.name] = pb.rotation_quaternion.copy()
            scales[pb.name] = pb.scale.copy()
            locations[pb.name] = pb.location.copy()
        if rig_object.animation_data:
            ori_action = rig_object.animation_data.action
        else: ori_action = None

        # Scale of the objects
        scale = 1

        # Check if armature using rigify
        use_rigify = check_use_rigify(rig_object.data)

        # Get export rig
        export_rig_ob = extract_export_rig(context, rig_object, scale, use_rigify)

        # Get export mesh objects
        export_mesh_objs = extract_export_meshes(context, mesh_objects, export_rig_ob, scale)

        # Set to object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Select rig export object
        context.scene.objects.active = export_rig_ob
        export_rig_ob.select = True

        # To store actions
        actions = []
        skipped_actions = []
        baked_actions = []

        # Deals with animations
        if scene_props.export_animations:

            # Make sure animation data is exists
            if not rig_object.animation_data:
                rig_object.animation_data_create()

            # Get valid actions
            for action in bpy.data.actions:
                if action.name.endswith('-noexp'): continue
                
                # Add -noexp to skipped actions
                if not action.rigify_export_props.enable_export:
                    action.name += '-noexp'
                    skipped_actions.append(action)
                else:
                    actions.append(action)

            # Bake all valid actions
            for action in actions:

                action_props = action.rigify_export_props

                # Set active action
                rig_object.animation_data.action = action

                # Remember active action name
                action_name = action.name

                # Set active action name to use -noexp, so it won't be exported
                action.name += '-noexp'

                # Make constraint
                make_constraint(context, rig_object, export_rig_ob)

                # Frame start and end
                frame_start = action.frame_range[0]
                frame_end = action.frame_range[1]
                if action_props.enable_loop and action_props.enable_skip_last_frame:
                    frame_end -= 1

                # Bake animations
                bpy.ops.nla.bake(
                        frame_start=frame_start,
                        frame_end=frame_end,
                        only_selected=True, 
                        visual_keying=True, 
                        clear_constraints=True, 
                        use_current_action=True, 
                        bake_types={'POSE'})

                # Rename baked action so it will be exported
                baked_action = export_rig_ob.animation_data.action
                baked_action.name = action_name

                if not baked_action.name.endswith('-loop') and action_props.enable_loop:
                    baked_action.name += '-loop'

                # Remember baked actions so it can be removed later
                baked_actions.append(baked_action)

                # Set active action back to None
                export_rig_ob.animation_data.action = None

        # Select export objects
        for obj in export_mesh_objs:
            obj.select = True

        #return {'FINISHED'}

        ## EXPORT!
        bpy.ops.export_scene.dae(
                filepath = self.filepath,
                object_types = {'ARMATURE', 'MESH'},
                use_export_selected = True,
                use_mesh_modifiers = scene_props.apply_modifiers,
                use_exclude_armature_modifier = True,
                use_tangent_arrays = scene_props.export_tangent,
                use_triangles = False,
                use_copy_images = scene_props.copy_images,
                use_active_layers = True,
                use_exclude_ctrl_bones = False,
                use_anim = scene_props.export_animations,
                use_anim_action_all = True,
                use_anim_skip_noexp = True,
                use_anim_optimize = True,
                use_shape_key_export = False,
                anim_optimize_precision = 6.0,
                use_metadata = True
                )

        # Delete exported object
        bpy.ops.object.delete()

        # Delete baked actions
        for action in baked_actions:
            bpy.data.actions.remove(action)

        # Recover original action names
        actions.extend(skipped_actions)
        for action in actions:
            action.name = action.name[:-6]

        # Descale original rig
        rig_object.scale /= scale

        # Load original state
        state.load(context)

        # Recover bone matrices and active action
        for pb in rig_object.pose.bones:
            pb.rotation_quaternion = quaternions[pb.name]
            pb.scale = scales[pb.name]
            pb.location = locations[pb.name]
        if rig_object.animation_data:
            rig_object.animation_data.action = ori_action 

        # Failed export objects
        if any(failed_mesh_objects):
            obj_names = ''
            for i, obj in enumerate(failed_mesh_objects):
                obj_names += obj.name
                if i != len(failed_mesh_objects) - 1:
                    obj_names += ', '
            
            self.report({'INFO'}, "INFO: Cannot export object [" + obj_names + "] because of reasons")

        return {'FINISHED'}

class ToggleGodotRigifyOptions(bpy.types.Operator):
    bl_idname = "scene.toggle_godot_rigify_options"
    bl_label = "Toggle Godot Rigify Export Options"
    bl_description = "Toggle Godot Rigify Export Options"
    #bl_options = {'REGISTER', 'UNDO'}

    prop = StringProperty(default='show_rig_export_options')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        props = context.scene.gr_props

        if self.prop not in dir(props) or not self.prop.startswith('show_'):
            return {'CANCELLED'}

        cur_value = getattr(props, self.prop)
        setattr(props, self.prop, not cur_value)

        return {'FINISHED'}

class GodotRigifySkeletonPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "objectmode"
    bl_label = "Godot Skeleton"
    bl_category = "UE4 Helper"

    def draw(self, context):
        scene_props = context.scene.gr_props

        c = self.layout.column(align=True)
        r = c.row(align=True)
        r.operator('export_mesh.rigify_dae', text='Export Skeleton Mesh', icon='MOD_ARMATURE')

        if scene_props.show_rig_export_options: r.alert = True
        r.operator('scene.toggle_godot_rigify_options', text='', icon='SCRIPTWIN').prop = 'show_rig_export_options'

        if scene_props.show_rig_export_options:
            box = c.box()
            col = box.column(align=True)
            col.prop(scene_props, 'export_animations')
            col.prop(scene_props, 'apply_modifiers')
            col.prop(scene_props, 'export_tangent')
            col.prop(scene_props, 'copy_images')

class SceneGodotRigifyProps(bpy.types.PropertyGroup):
    show_rig_export_options = BoolProperty(default=False)

    export_animations = BoolProperty(default=True, 
            name='Export Animations', description='Export all animations, except whose name ends  with -noexp')

    apply_modifiers = BoolProperty(default=True, 
            name='Apply Modifiers', description='Apply all modifiers')

    export_tangent = BoolProperty(default=False, 
            name='Export Tangent', description="Export Tangent and Binormal arrays (for normalmapping)")

    copy_images = BoolProperty(default=False, 
            name='Copy Images', description="Copy Images (create images/ subfolder)")

def register():
    bpy.utils.register_class(ExportRigifyDAE)
    bpy.utils.register_class(ToggleGodotRigifyOptions)
    bpy.utils.register_class(GodotRigifySkeletonPanel)
    bpy.utils.register_class(SceneGodotRigifyProps)

    bpy.types.Scene.gr_props = PointerProperty(type=SceneGodotRigifyProps)

def unregister():
    bpy.utils.unregister_class(ExportRigifyDAE)
    bpy.utils.unregister_class(ToggleGodotRigifyOptions)
    bpy.utils.unregister_class(GodotRigifySkeletonPanel)
    bpy.utils.unregister_class(SceneGodotRigifyProps)
