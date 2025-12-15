import bpy, sys, time
from bpy.props import *
from mathutils import *
from bpy_extras.io_utils import (ExportHelper,
                                 #orientation_helper_factory,
                                 #path_reference_mode,
                                 axis_conversion,
                                 ) 
from .common import *

def export_gltf(filepath, scene_props, export_materials='EXPORT'):
    bpy.ops.export_scene.gltf(
            filepath=filepath,
            #check_existing=True, 
            #export_format='GLTF_EMBEDDED', 
            export_format=scene_props.gltf_format,
            #ui_tab='GENERAL', 
            #export_copyright='', 
            export_image_format='AUTO', 
            export_texture_dir='', 
            export_keep_originals=False, 
            export_texcoords=True, 
            export_normals=True, 
            #export_draco_mesh_compression_enable=False, 
            #export_draco_mesh_compression_level=6, 
            #export_draco_position_quantization=14, 
            #export_draco_normal_quantization=10, 
            #export_draco_texcoord_quantization=12, 
            #export_draco_color_quantization=10, 
            #export_draco_generic_quantization=12, 
            export_tangents = scene_props.export_tangent,
            export_materials=export_materials,
            # export_colors = scene_props.export_vcols,
            use_mesh_edges=False, 
            use_mesh_vertices=False, 
            export_cameras=False, 
            #export_selected=True, 
            use_selection=True, 
            use_visible=False, 
            use_renderable=False, 
            use_active_collection=False, 
            export_extras=False, 
            export_yup=True, 
            export_apply = scene_props.apply_modifiers,
            export_animations = scene_props.export_animations,
            export_frame_range=True, 
            export_frame_step=1, 
            export_force_sampling=True, 
            export_nla_strips = scene_props.export_animations,
            export_def_bones=False, 
            export_optimize_animation_size=True,
            export_anim_single_armature=False,
            export_current_frame=False, 
            export_skins=True, 
            export_all_influences=False, 
            export_morph=True, 
            export_morph_normal=True, 
            export_morph_tangent=True, 
            export_lights=False, 
            export_sampling_interpolation_fallback=scene_props.export_sampling_interpolation_fallback,
            #export_displacement=False, 
            #will_save_settings=False, 
            #filter_glob='*.glb;*.gltf'
            )

def get_deform_bones(obj, bone_name):
    bones = [b for b in obj.pose.bones if bone_name in b.name and 'DEF-' in b.name]

    if len(bones) == 1:
        pass

    elif bone_name == 'head':
        bone = obj.pose.bones.get('DEF-spine.006')
        if bone and bone not in bones: bones.append(bone)

    elif bone_name == 'neck':
        bone = obj.pose.bones.get('DEF-spine.005')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.pose.bones.get('DEF-spine.004')
        if bone and bone not in bones: bones.append(bone)

    elif bone_name == 'chest':
        bone = obj.pose.bones.get('DEF-spine.003')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.pose.bones.get('DEF-spine.002')
        if bone and bone not in bones: bones.append(bone)

    elif bone_name in {'torso', 'hips'}:
        bone = obj.pose.bones.get('DEF-spine.001')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.pose.bones.get('DEF-spine')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.pose.bones.get('DEF-pelvis.L')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.pose.bones.get('DEF-pelvis.R')
        if bone and bone not in bones: bones.append(bone)

    elif 'tweak_spine' in bone_name:
        bname = bone_name.replace('tweak_', '')
        bbones = [b for b in obj.pose.bones if bname in b.name and 'DEF-' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'upper_arm' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-upper_arm.L' in b.name]
        elif '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-upper_arm.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'forearm' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-forearm.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-forearm.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'hand' in bone_name:
        bone = None
        if '.L' in bone_name:
            bone = obj.pose.bones.get('DEF-hand.L')
        if '.R' in bone_name:
            bone = obj.pose.bones.get('DEF-hand.L')
        if bone and bone not in bones: bones.append(bone)

    elif 'palm' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-palm' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-palm' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'thumb' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-thumb' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-thumb' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'f_index' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-f_index' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-f_index' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'f_middle' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-f_middle' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-f_middle' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'f_ring' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-f_ring' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-f_ring' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'f_pinky' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-f_pinky' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-f_pinky' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'thigh' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-thigh.L' in b.name]
        elif '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-thigh.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'shin' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-shin.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-shin.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'foot' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-foot.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-foot.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'toe' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-toe.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.pose.bones if 'DEF-toe.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    return bones

def get_deform_edit_bones(obj, bone_name):
    bones = [b for b in obj.data.edit_bones if 'DEF-'+bone_name == b.name]

    if len(bones) == 1:
        pass

    elif bone_name == 'head':
        bone = obj.data.edit_bones.get('DEF-spine.006')
        if bone and bone not in bones: bones.append(bone)

    elif bone_name == 'neck':
        bone = obj.data.edit_bones.get('DEF-spine.005')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.data.edit_bones.get('DEF-spine.004')
        if bone and bone not in bones: bones.append(bone)

    elif bone_name == 'chest':
        bone = obj.data.edit_bones.get('DEF-spine.003')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.data.edit_bones.get('DEF-spine.002')
        if bone and bone not in bones: bones.append(bone)

    elif bone_name in {'torso', 'hips'}:
        bone = obj.data.edit_bones.get('DEF-spine.001')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.data.edit_bones.get('DEF-spine')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.data.edit_bones.get('DEF-pelvis.L')
        if bone and bone not in bones: bones.append(bone)
        bone = obj.data.edit_bones.get('DEF-pelvis.R')
        if bone and bone not in bones: bones.append(bone)

    elif 'tweak_spine' in bone_name:
        bname = bone_name.replace('tweak_', '')
        bbones = [b for b in obj.data.edit_bones if bname in b.name and 'DEF-' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'upper_arm' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-upper_arm.L' in b.name]
        elif '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-upper_arm.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'forearm' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-forearm.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-forearm.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'hand' in bone_name:
        bone = None
        if '.L' in bone_name:
            bone = obj.data.edit_bones.get('DEF-hand.L')
        if '.R' in bone_name:
            bone = obj.data.edit_bones.get('DEF-hand.L')
        if bone and bone not in bones: bones.append(bone)

    elif 'palm' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-palm' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-palm' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'thumb' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-thumb' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-thumb' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'f_index' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-f_index' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-f_index' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'f_middle' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-f_middle' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-f_middle' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'f_ring' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-f_ring' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-f_ring' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'f_pinky' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-f_pinky' in b.name and '.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-f_pinky' in b.name and '.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'thigh' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-thigh.L' in b.name]
        elif '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-thigh.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'shin' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-shin.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-shin.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'foot' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-foot.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-foot.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    elif 'toe' in bone_name:
        bbones = []
        if '.L' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-toe.L' in b.name]
        if '.R' in bone_name:
            bbones = [b for b in obj.data.edit_bones if 'DEF-toe.R' in b.name]
        for bone in bbones: 
            if bone and bone not in bones: bones.append(bone)

    return bones

def copy_some_bones(rig_object, active_export_rig_ob):

    ori_mode = active_export_rig_ob.mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')

    arm = active_export_rig_ob.data

    for pb in rig_object.pose.bones:
        if pb.gr_props.add_extra_copy_bone:

            # Get and select edit bone
            b = arm.edit_bones.get(pb.name)
            if not b: continue
            b.select=True
            arm.edit_bones.active = b

            # Duplicate edit bone
            copyb = arm.edit_bones.new(pb.name + COPY_SUFFIX)
            copyb.head = b.head
            copyb.tail = b.tail
            copyb.matrix = b.matrix.copy()
            copyb.parent = b.parent
            copyb.select = False

    bpy.ops.object.mode_set(mode=ori_mode)

def keep_parent_update(self, context: bpy.types.Context):
    edit_bones = context.selected_bones
    if len(edit_bones)>1 : 
        for bone in edit_bones:
            def_bone = get_deform_edit_bones(context.active_object, bone.name)
            if len(def_bone)>0:
                def_bone[0].gr_props["keep_parent"] = self.keep_parent

class ExportRigifyGLTF(bpy.types.Operator, ExportHelper):
    bl_idname = "export_mesh.rigify_gltf"
    bl_label = "Export Godot Skeleton"
    bl_description = "Export rigify mesh as GLTF file"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".glb"
    filter_glob : StringProperty(default="*.glb, *.gltf", options={'HIDDEN'})

    #custom_directory = StringProperty(default='')

    @classmethod
    def poll(cls, context):
        return get_current_armature_object()

    def invoke(self, context, event):
        obj =  get_current_armature_object()
        scene_props = context.scene.gr_props

        if scene_props.gltf_format == "GLTF_SEPARATE" :
            self.filename_ext = ".gltf"
        elif scene_props.gltf_format == "GLB":
            self.filename_ext = ".glb"

        directory = os.path.dirname(self.filepath)
        filename = os.path.splitext(os.path.basename(context.blend_data.filepath))[0]
        suffix = ''

        if scene_props.export_animations:
            if scene_props.export_only_selected_action:
                try: action = obj.animation_data.action
                except: action = None

                if action:
                    filename = action.name
            elif not scene_props.export_meshes:
                suffix = '_anim'

        if scene_props.remove_whitespaces:
            filename = filename.replace(' ', '')

        self.filepath = os.path.join(directory, filename + suffix + self.filename_ext)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):

        T = time.time()

        scene_props = context.scene.gr_props

        if not scene_props.export_animations and not scene_props.export_meshes:
            self.report({'ERROR'}, 'You should at least choose to export meshes or animations!')
            return{'CANCELLED'}

        # Create save system to save current selection, mode, and active object
        state = SaveState(context)

        # Get all possible objects
        objects = [o for o in context.selected_objects]
        if context.object and context.object not in objects:
            objects.append(context.object)

        use_export_meshes = scene_props.export_meshes and not (
                scene_props.export_animations and scene_props.export_only_selected_action)

        # Evaluate selected objects to export
        rig_object, mesh_objects, failed_mesh_objects, error_messages = evaluate_and_get_source_data(
                context.scene, objects, use_export_meshes)

        # If found error
        if error_messages != '':
            self.report({'ERROR'}, error_messages)
            state.load(context)
            return{'CANCELLED'}

        if not scene_props.export_apply_transform:
            #remember rig object transformation
            armature_quaternions = rig_object.rotation_quaternion.copy()
            armature_euler = rig_object.rotation_euler.copy()
            armature_location = rig_object.location.copy()
            armature_scale = rig_object.scale.copy()

            #reset rig translation
            rig_object.location = (0.0,0.0,0.0)
            rig_object.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
            rig_object.rotation_euler = (0.0,0.0,0.0)
            rig_object.scale = (1.0,1.0,1.0)

        if scene_props.export_animations and scene_props.export_only_selected_action:
            if not rig_object.animation_data or not rig_object.animation_data.action:
                self.report({'ERROR'}, 'No active action used on the rig!')
                state.load(context)
                return{'CANCELLED'}

        # Remember rig object original matrices and original action
        quaternions = {}
        eulers = {}
        scales = {}
        locations = {}
        for pb in rig_object.pose.bones:
            quaternions[pb.name] = pb.rotation_quaternion.copy()
            eulers[pb.name] = pb.rotation_euler.copy()
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
        unparent_all = True if scene_props.parental_mode == 'UNPARENT_ALL' else False
        export_rig_ob = extract_export_rig(context, rig_object, scale, use_rigify, unparent_all=unparent_all)

        # Set to object mode and deselect all
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # Get export mesh objects
        export_mesh_objs = []
        if use_export_meshes:
            export_mesh_objs = extract_export_meshes(context, mesh_objects, export_rig_ob, scale, scene_props.only_export_baked_vcols)

        # Export extra objects first because it doesn't need materials or armature
        for ob in export_mesh_objs:
            if ob.gr_props.add_clear_location_duplicate:
                set_active(ob)
                select_set(ob, True)

                # Remember things
                ori_show_viewports = [m.show_viewport for m in ob.modifiers]
                ori_show_renders = [m.show_render for m in ob.modifiers]
                ori_location = ob.location.copy()

                # Disable armature modifiers
                for mod in ob.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.show_viewport = False
                        mod.show_render = False

                # Clear location
                bpy.ops.object.location_clear(clear_delta=False)

                # Get filepath
                directory = os.path.dirname(self.filepath)
                filename = os.path.splitext(os.path.basename(self.filepath))[0]
                if ob.name.startswith(filename):
                    filename = ''
                else: filename += ' '

                filename += ob.name

                if scene_props.remove_whitespaces:
                    filename = filename.replace(' ', '')

                filepath = os.path.join(directory, filename + self.filename_ext)

                # Export gltf
                export_gltf(filepath, scene_props, 'PLACEHOLDER')

                # Recover modifiers
                for i, mod in enumerate(ob.modifiers):
                    if ori_show_viewports[i]:
                        mod.show_viewport = True
                    if ori_show_renders[i]:
                        mod.show_render = True

                # Recover location
                ob.location = ori_location

                # Deselect object
                select_set(ob, False)

        # Set ucupaint baked outside
        ori_not_use_baked = []
        ori_not_use_baked_outside = []
        use_yp_baked_outside = scene_props.ucupaint_baked_outside and hasattr(bpy.types.ShaderNodeTree, 'yp')
        if use_yp_baked_outside:
            for ob in export_mesh_objs:
                for i, ms in enumerate(ob.material_slots):
                    mat = ms.material
                    if not mat or not mat.node_tree: continue
                    for n in mat.node_tree.nodes:
                        if n.type == 'GROUP' and n.node_tree and n.node_tree.yp.is_ypaint_node:
                            yp = n.node_tree.yp
                            baked_found = any([c for c in yp.channels if n.node_tree.nodes.get(c.baked)])
                            if baked_found:

                                if not yp.use_baked or not yp.enable_baked_outside:
                                    set_active(ob)
                                    select_set(ob, True)
                                    ob.active_material_index = i
                                    mat.node_tree.nodes.active = n

                                if not yp.use_baked: 
                                    ori_not_use_baked.append(n.node_tree)
                                    yp.use_baked = True

                                if not yp.enable_baked_outside: 
                                    ori_not_use_baked_outside.append(n.node_tree)
                                    yp.enable_baked_outside = True

                select_set(ob, False)

        # Select rig export object
        set_active(export_rig_ob)
        select_set(export_rig_ob, True)

        # To store actions
        actions = []
        baked_actions = []
        original_frame_end = context.scene.frame_end

        # Go to pose mode
        bpy.ops.object.mode_set(mode='POSE')
        #bpy.ops.pose.select_all(action='SELECT')

        # Copy some bones if necessary
        copy_some_bones(rig_object, export_rig_ob)

        # Deals with animations
        if scene_props.export_animations:

            # Disable armature modifier first to make the bake action faster
            for obj in export_mesh_objs:
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.object = None

            if scene_props.export_only_selected_action:
                actions = [rig_object.animation_data.action]
            else: actions = [a for a in bpy.data.actions if a.rigify_export_props.enable_export]

            # Remove already available tracks
            if export_rig_ob.animation_data and len(export_rig_ob.animation_data.nla_tracks) > 0:
                for track in reversed(export_rig_ob.animation_data.nla_tracks):
                    export_rig_ob.animation_data.nla_tracks.remove(track)

            # Bake all valid actions
            for action in actions:

                action_props = action.rigify_export_props

                # Reset all bone transformations first
                reset_pose_bones(rig_object)
                if context.scene.rigify_export_props.sync_rigify_props:
                    reset_pose_bone_props(rig_object, context.scene, action)

                # Set active action
                rig_object.animation_data.action = action

                # Remember active action name
                action_name = action.name

                # Set active action name to use temporary name
                action.name += TEMP_SUFFIX

                # Make constraint
                make_constraint(context, rig_object, export_rig_ob)

                # Frame start and end
                if action.use_frame_range:
                    frame_start = int(action.frame_start)
                    frame_end = int(action.frame_end)
                else:
                    frame_start = int(action.frame_range[0])
                    frame_end = int(action.frame_range[1])
                if action_props.enable_loop and action_props.enable_skip_last_frame and not action.use_frame_range:
                    frame_end -= 1

                if frame_end > context.scene.frame_end:
                    context.scene.frame_end = frame_end

                print("INFO: Baking action '" + action_name + "'...")

                # Bake animations
                bpy.ops.nla.bake(
                        frame_start=frame_start,
                        frame_end=frame_end,
                        only_selected=False, #True,
                        visual_keying=True, 
                        clear_constraints=True, 
                        use_current_action=True, 
                        clean_curves = True,
                        bake_types={'POSE'})

                # Rename baked action so it will be exported
                baked_action = export_rig_ob.animation_data.action
                baked_action.name = action_name

                if not baked_action.name.endswith('-loop') and action_props.enable_loop:
                    baked_action.name += '-loop'

                if action_props.enable_remove_untransformed:
                    remove_non_transformed_keyframes(baked_action, tolerance=action_props.untransformed_tolerance)

                # Dealing with separated GLTFs
                if scene_props.export_action_as_separated_gltf and not scene_props.export_only_selected_action:
                    # Add nla track for the baked action
                    track = export_rig_ob.animation_data.nla_tracks.new()
                    strip = track.strips.new(baked_action.name, int(baked_action.frame_start), baked_action)

                    # Set the filepath based on action name
                    directory = os.path.dirname(self.filepath)

                    filename = action_name
                    if scene_props.remove_whitespaces:
                        filename = filename.replace(' ', '')

                    filepath = os.path.join(directory, filename + '.gltf')

                    # Export action as gltf file
                    bpy.ops.object.mode_set(mode='OBJECT')
                    export_gltf(filepath, scene_props)
                    bpy.ops.object.mode_set(mode='POSE')

                    # Remove nla track
                    track = export_rig_ob.animation_data.nla_tracks[0]
                    export_rig_ob.animation_data.nla_tracks.remove(track)

                # Remember baked actions so it can be removed later
                baked_actions.append(baked_action)

                # Set active action back to None
                export_rig_ob.animation_data.action = None

            # Recover armature modifiers
            for obj in export_mesh_objs:
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.object = export_rig_ob

        # Only add baked actions to NLA if not using separated gltf
        if baked_actions and (scene_props.export_only_selected_action or not scene_props.export_action_as_separated_gltf):

            # Add baked action to NLA tracks
            for ba in baked_actions:
                track = export_rig_ob.animation_data.nla_tracks.new()
                strip = track.strips.new(ba.name, int(ba.frame_start), ba)

        # Back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Select export mesh objects
        for obj in export_mesh_objs:
            select_set(obj, True)

        ## EXPORT!
        # No need to export if there's no meshes or actions
        if any(export_mesh_objs) or (export_rig_ob.animation_data and any(export_rig_ob.animation_data.nla_tracks)):
            export_gltf(self.filepath, scene_props)

        # Delete exported objects
        bpy.ops.object.delete()

        # Delete baked actions
        for action in baked_actions:
            bpy.data.actions.remove(action)

        context.scene.frame_end = original_frame_end
        # Recover original action names
        for action in bpy.data.actions:
            if action.name.endswith(TEMP_SUFFIX):
                action.name = action.name[:-len(TEMP_SUFFIX)]

        # Recover original mesh object names
        for obj in bpy.data.objects:
            if obj.name.endswith(TEMP_SUFFIX):
                obj.name = obj.name[:-len(TEMP_SUFFIX)]

        # Descale original rig
        rig_object.scale /= scale
        
        # Recover ucupaint use baked
        if use_yp_baked_outside and (any(ori_not_use_baked) or any(ori_not_use_baked_outside)):
            already_not_use_baked = []
            already_not_use_baked_outside = []
            for ob in context.view_layer.objects:
                for i, ms in enumerate(ob.material_slots):
                    mat = ms.material
                    if not mat or not mat.node_tree: continue
                    node_names = []
                    for n in mat.node_tree.nodes:
                        if n.type == 'GROUP' : node_names.append(n.name)
                    for node_name in node_names:
                        n = mat.node_tree.nodes.get(node_name)
                        if n.type == 'GROUP' and n.node_tree:
                            if ((n.node_tree in ori_not_use_baked and n.node_tree not in already_not_use_baked) or
                                (n.node_tree in ori_not_use_baked_outside and n.node_tree not in already_not_use_baked_outside)
                                ):
                                set_active(ob)
                                select_set(ob, True)
                                ob.active_material_index = i
                                mat.node_tree.nodes.active = n

                            if n.node_tree in ori_not_use_baked and n.node_tree not in already_not_use_baked:
                                n.node_tree.yp.use_baked = False
                                already_not_use_baked.append(n.node_tree)

                            if n.node_tree in ori_not_use_baked_outside and n.node_tree not in already_not_use_baked_outside:
                                n.node_tree.yp.enable_baked_outside = False
                                already_not_use_baked_outside.append(n.node_tree)

                select_set(ob, False)

        # Load original state
        state.load(context)

        if not scene_props.export_apply_transform:
            # recover object translation
            rig_object.rotation_quaternion = armature_quaternions
            rig_object.rotation_euler = armature_euler
            rig_object.location = armature_location
            rig_object.scale = armature_scale

        # Recover bone matrices and active action
        for pb in rig_object.pose.bones:
            pb.rotation_quaternion = quaternions[pb.name]
            pb.rotation_euler = eulers[pb.name]
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

        print('INFO:', 'Export finished at', '{:0.2f}'.format(time.time() - T), 'seconds!')

        return {'FINISHED'}

class ToggleGodotRigifyOptions(bpy.types.Operator):
    bl_idname = "scene.toggle_godot_rigify_options"
    bl_label = "Toggle Godot Rigify Export Options"
    bl_description = "Toggle Godot Rigify Export Options"
    #bl_options = {'REGISTER', 'UNDO'}

    prop : StringProperty(default='show_rig_export_options')

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

class GODOTHELPER_PT_RigifySkeletonPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_context = "objectmode"
    bl_label = "Godot Skeleton"
    bl_category = "Ucup Exporter"

    def draw(self, context):
        scene_props = context.scene.gr_props

        c = self.layout.column(align=True)
        r = c.row(align=True)
        r.operator('export_mesh.rigify_gltf', text='Export as GLTF', icon='MOD_ARMATURE')

        if scene_props.show_rig_export_options: r.alert = True
        icon = 'PREFERENCES' # if is_bl_newer_than(2, 80) else 'SCRIPTWIN'
        r.operator('scene.toggle_godot_rigify_options', text='', icon=icon).prop = 'show_rig_export_options'

        if scene_props.show_rig_export_options:
            box = c.box()
            col = box.column(align=True)

            use_export_meshes_visible = not ( scene_props.export_animations and 
                    scene_props.export_only_selected_action)
                    #(scene_props.export_only_selected_action or scene_props.export_action_as_separated_gltf))
            use_export_meshes = scene_props.export_meshes and use_export_meshes_visible

            row = col.row()
            row.active = use_export_meshes_visible
            row.prop(scene_props, 'export_meshes')

            col.prop(scene_props, 'export_animations')

            row = col.row()
            row.active = scene_props.export_animations
            row.prop(scene_props, 'export_only_selected_action')

            row = col.row()
            row.active = scene_props.export_animations and not scene_props.export_only_selected_action
            row.prop(scene_props, 'export_action_as_separated_gltf')

            col = box.column(align=True)
            col.active = use_export_meshes

            #row = col.split(factor=0.4)
            #row.label(text='Export Mode:')
            #row.prop(scene_props, 'export_mode', text='')
            col.prop(scene_props, 'apply_modifiers')
            col.prop(scene_props, 'export_tangent')
            #col.prop(scene_props, 'copy_images')
            col.prop(scene_props, 'export_vcols')

            row = col.row()
            row.active = scene_props.export_vcols
            row.prop(scene_props, 'only_export_baked_vcols')

            col.prop(scene_props, 'ucupaint_baked_outside')

            col = box.column(align=True)

            row = col.split(factor=0.4)
            row.label(text='Bone Parents:')
            row.prop(scene_props, 'parental_mode', text='')

            row = col.split(factor=0.4)
            row.label(text='GLTF Format:')
            row.prop(scene_props, 'gltf_format', text='')

            col.prop(scene_props, 'remove_whitespaces')
            col.prop(scene_props, 'export_apply_transform')

            col.prop(scene_props, 'export_sampling_interpolation_fallback')

            # For object settings
            subbox = box.box()
            subcol = subbox.column(align=False)
            obj = context.object
            obj_props = obj.gr_props
            obj_name = obj.name if obj else '-'

            r = subcol.row()
            rr = r.row(align=True)
            if scene_props.show_object_export_options: rr.alert = True
            icon = 'PREFERENCES'
            rr.operator('scene.toggle_godot_rigify_options', text='', icon=icon).prop = 'show_object_export_options'

            r.label(text='Object Settings (' + obj_name + ')')

            if scene_props.show_object_export_options:
                ssubbox = subcol.box()
                ssubbox.prop(obj_props, 'add_clear_location_duplicate')

            if obj and obj.mode == 'POSE':
                active_bone = obj.data.bones.active

                if active_bone:
                    pb = obj.pose.bones.get(active_bone.name)

                    def_bones = get_deform_bones(obj, pb.name)

                    r = subcol.row()
                    rr = r.row(align=True)
                    if scene_props.show_posebone_export_options: rr.alert = True
                    icon = 'PREFERENCES'
                    rr.operator('scene.toggle_godot_rigify_options', text='', icon=icon).prop = 'show_posebone_export_options'

                    r.label(text='Bone Settings (' + pb.name + ')')

                    if scene_props.show_posebone_export_options:
                        ssubbox = subcol.box()
                        ccol = ssubbox.column(align=True)
                        for db in def_bones:
                            title = 'Add Extra Copy Bone'
                            title += ' (' + db.name + ')'
                            ccol.prop(db.gr_props, 'add_extra_copy_bone', text=title)
                        if len(def_bones) == 0:
                            ccol.label(text='No related deform bones found!')
            
            if obj and obj.mode == 'EDIT':
                active_bone = obj.data.edit_bones.active
                if active_bone:
                    eb = obj.data.edit_bones.get(active_bone.name)

                    def_bones = get_deform_edit_bones(obj, eb.name)

                    r = subcol.row()
                    rr = r.row(align=True)
                    if scene_props.show_editbone_export_options: rr.alert = True
                    icon = 'PREFERENCES'
                    rr.operator('scene.toggle_godot_rigify_options', text='', icon=icon).prop = 'show_editbone_export_options'

                    r.label(text='Bone Settings (' + eb.name + ')')

                    if scene_props.show_editbone_export_options:
                        ssubbox = subcol.box()
                        ccol = ssubbox.column(align=True)
                        for db in def_bones:
                            title = 'Force Keep Parent'
                            title += ' (' + db.name + ')'
                            ccol.prop(db.gr_props, 'keep_parent', text=title)
                        if len(def_bones) == 0:
                            ccol.label(text='No related deform bones found!')

        #c = self.layout.column(align=True)
        #r = c.row(align=True)
        #r.operator('export_mesh.rigify_action_gltf', text='Export current Action', icon='ACTION')

class SceneGodotRigifyProps(bpy.types.PropertyGroup):
    show_rig_export_options : BoolProperty(default=False)
    show_object_export_options : BoolProperty(default=False)
    show_posebone_export_options : BoolProperty(default=False)
    show_editbone_export_options : BoolProperty(default=False)

    export_meshes : BoolProperty(default=True, 
            name='Export Meshes', description='Export all meshes used by the rigify rig')

    export_animations : BoolProperty(default=True, 
            name='Export Animations', description='Export animations with checkbox turned on')

    export_only_selected_action : BoolProperty(default=False, 
            name='Export Only Selected Action', description='Export only selected animation')

    export_action_as_separated_gltf : BoolProperty(default=False,
            name='Export Actions as separated GLTF', description='Export action(s) as separated GLTF')

    apply_modifiers : BoolProperty(default=True, 
            name='Apply Modifiers', description='Apply all modifiers')

    export_tangent : BoolProperty(default=False, 
            name='Export Tangent', description="Export Tangent and Binormal arrays (for normalmapping)")

    copy_images : BoolProperty(default=False, 
            name='Copy Images', description="Copy Images (create images/ subfolder)")

    export_vcols : BoolProperty(default=False,
            name='Export Vertex Colors', description="Export vertex colors")

    only_export_baked_vcols : BoolProperty(default=False,
            name='Only Export Baked Vertex Colors', description="Only export vertex colors which has 'Baked' prefix")

    ucupaint_baked_outside : BoolProperty(default=True,
            name='Use Baked Outside (Ucupaint)', description='Make sure ucupaint nodes use baked outside')

    parental_mode : EnumProperty(
            name = 'Export Rig Parental Mode',
            description = 'Export rig parental mode',
            items = (
                ('NO_CHANGES', 'No changes', 'No changes on deform bone parents'),
                ('UNPARENT_ALL', 'Unparent All', 'Unparent all deform bones'),
                ),
            default = 'NO_CHANGES')

    gltf_format : EnumProperty(
            name = 'GLTF Format',
            description = 'GLTF format',
            items = (
                ('GLB', 'GLTF Embedded', 'GLTF Embedded'),
                ('GLTF_SEPARATE', 'GLTF Separate', 'GLTF Separate'),
                ),
            default = 'GLB')

    remove_whitespaces : bpy.props.BoolProperty(
            name="Remove Whitespaces",
            description="Remove whitespaces from saved names",
            default=False
            )
    
    export_sampling_interpolation_fallback : EnumProperty(
        name= ' export sampling interpolation fallback',
        description= '',
        items= (
            ('LINEAR', 'Linear', 'Linear Interpolation'), ('STEP', 'Step', 'Stepping Interpolation')
        ),
        default= 'LINEAR'
    )

    export_apply_transform : bpy.props.BoolProperty(
        name="Apply Transform",
        description="Apply Transform",
        default=False
    )

class ObjectGodotRigifyProps(bpy.types.PropertyGroup):
    add_clear_location_duplicate : BoolProperty(default=False,
            name='Duplicate as Separated GLTF', description='Duplicate object as separated gltf with cleared location (useful for softbody attachment)')

class PoseBoneGodotRigifyProps(bpy.types.PropertyGroup):
    add_extra_copy_bone : BoolProperty(default=False,
            name='Add Extra Copy Bone', 
            description='Add extra copy bone on exported rig')
    
class EditBoneGodotRigifyProps(bpy.types.PropertyGroup):
    keep_parent : BoolProperty(default=False,
            name='Keep Bone Parent', 
            description='Keep Bone Parent for remove parent options',
            update=keep_parent_update)

def register():
    bpy.utils.register_class(ExportRigifyGLTF)
    bpy.utils.register_class(ToggleGodotRigifyOptions)
    bpy.utils.register_class(GODOTHELPER_PT_RigifySkeletonPanel)
    bpy.utils.register_class(SceneGodotRigifyProps)
    bpy.utils.register_class(ObjectGodotRigifyProps)
    bpy.utils.register_class(PoseBoneGodotRigifyProps)
    bpy.utils.register_class(EditBoneGodotRigifyProps)

    bpy.types.Scene.gr_props = PointerProperty(type=SceneGodotRigifyProps)
    bpy.types.Object.gr_props = PointerProperty(type=ObjectGodotRigifyProps)
    bpy.types.PoseBone.gr_props = PointerProperty(type=PoseBoneGodotRigifyProps)
    bpy.types.EditBone.gr_props = PointerProperty(type=EditBoneGodotRigifyProps)

def unregister():
    bpy.utils.unregister_class(ExportRigifyGLTF)
    bpy.utils.unregister_class(ToggleGodotRigifyOptions)
    bpy.utils.unregister_class(GODOTHELPER_PT_RigifySkeletonPanel)
    bpy.utils.unregister_class(SceneGodotRigifyProps)
    bpy.utils.unregister_class(ObjectGodotRigifyProps)
    bpy.utils.unregister_class(PoseBoneGodotRigifyProps)
    bpy.utils.unregister_class(EditBoneGodotRigifyProps)
