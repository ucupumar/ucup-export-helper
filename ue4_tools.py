bl_info = {
    "name": "Unreal Engine 4 Export Helper",
    "author": "Yusuf Umar",
    "version": (0, 0, 0),
    "blender": (2, 74, 0),
    "location": "View 3D > Tool Shelf > UE4 Helper",
    "description": "Tool to help exporting something to UE4 less pain in the a**",
    "wiki_url": "http://twitter.com/ucupumar",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    if "export_fbx_bin" in locals():
        importlib.reload(export_fbx_bin)

import bpy
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, BoolProperty, IntProperty, EnumProperty, StringProperty
from io_scene_fbx import export_fbx_bin
from bpy_extras.io_utils import (ExportHelper,
                                 #orientation_helper_factory,
                                 #path_reference_mode,
                                 axis_conversion,
                                 ) 

#IOFBXOrientationHelper = orientation_helper_factory("IOFBXOrientationHelper", axis_forward='-Z', axis_up='Y')

class SourceData():
    rigify_object = None
    mesh_objects = []
    failed_mesh_objects = []

class SaveState():
    def __init__(self, context):
        self.active = context.object
        self.select = context.selected_objects
        self.mode = context.mode
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
    
    def load(self, context):
        scene = context.scene
        for obj in bpy.data.objects:
            if obj in self.select:
                obj.select = True
            else: obj.select = False
        scene.objects.active = self.active
        bpy.ops.object.mode_set(mode=self.mode)
        scene.frame_start = self.frame_start
        scene.frame_end = self.frame_end

parent_dict = {
        'DEF-hips' : 'root',
        'DEF-spine' : 'DEF-hips',
        #'DEF-chest' : 'DEF-spine',
        'DEF-chest.01' : 'DEF-spine',
        'DEF-chest.02' : 'DEF-chest.01',
        #'DEF-neck' : 'DEF-chest',
        'DEF-neck' : 'DEF-chest.02',
        'DEF-head' : 'DEF-neck',
        
        # LEFT

        'DEF-shoulder.L' : 'DEF-chest.02',
        'DEF-upper_arm.01.L' : 'DEF-shoulder.L',
        'DEF-upper_arm.02.L' : 'DEF-upper_arm.01.L',
        'DEF-forearm.01.L' : 'DEF-upper_arm.02.L',
        'DEF-forearm.02.L' : 'DEF-forearm.01.L',
        'DEF-hand.L' : 'DEF-forearm.02.L',
        
        'DEF-palm.04.L' : 'DEF-hand.L',
        'DEF-palm.03.L' : 'DEF-hand.L',
        'DEF-palm.02.L' : 'DEF-hand.L',
        'DEF-palm.01.L' : 'DEF-hand.L',
        
        'DEF-f_pinky.01.L.01' : 'DEF-palm.04.L',
        'DEF-f_pinky.01.L.02' : 'DEF-f_pinky.01.L.01',
        'DEF-f_pinky.02.L' : 'DEF-f_pinky.01.L.02',
        'DEF-f_pinky.03.L' : 'DEF-f_pinky.02.L',
        
        'DEF-f_ring.01.L.01' : 'DEF-palm.03.L',
        'DEF-f_ring.01.L.02' : 'DEF-f_ring.01.L.01',
        'DEF-f_ring.02.L' : 'DEF-f_ring.01.L.02',
        'DEF-f_ring.03.L' : 'DEF-f_ring.02.L',
        
        'DEF-f_middle.01.L.01' : 'DEF-palm.02.L',
        'DEF-f_middle.01.L.02' : 'DEF-f_middle.01.L.01',
        'DEF-f_middle.02.L' : 'DEF-f_middle.01.L.02',
        'DEF-f_middle.03.L' : 'DEF-f_middle.02.L',

        'DEF-f_index.01.L.01' : 'DEF-palm.01.L',
        'DEF-f_index.01.L.02' : 'DEF-f_index.01.L.01',
        'DEF-f_index.02.L' : 'DEF-f_index.01.L.02',
        'DEF-f_index.03.L' : 'DEF-f_index.02.L',

        'DEF-thumb.01.L.01' : 'DEF-hand.L',
        'DEF-thumb.01.L.02' : 'DEF-thumb.01.L.01',
        'DEF-thumb.02.L' : 'DEF-thumb.01.L.02',
        'DEF-thumb.03.L' : 'DEF-thumb.02.L',
        
        'DEF-thigh.01.L' : 'DEF-hips',
        'DEF-thigh.02.L' : 'DEF-thigh.01.L',
        'DEF-shin.01.L' : 'DEF-thigh.02.L',
        'DEF-shin.02.L' : 'DEF-shin.01.L',
        
        'DEF-foot.L' : 'DEF-shin.02.L',
        'DEF-toe.L' : 'DEF-foot.L',

        # RIGHT

        'DEF-shoulder.R' : 'DEF-chest.02',
        'DEF-upper_arm.01.R' : 'DEF-shoulder.R',
        'DEF-upper_arm.02.R' : 'DEF-upper_arm.01.R',
        'DEF-forearm.01.R' : 'DEF-upper_arm.02.R',
        'DEF-forearm.02.R' : 'DEF-forearm.01.R',
        'DEF-hand.R' : 'DEF-forearm.02.R',
        
        'DEF-palm.04.R' : 'DEF-hand.R',
        'DEF-palm.03.R' : 'DEF-hand.R',
        'DEF-palm.02.R' : 'DEF-hand.R',
        'DEF-palm.01.R' : 'DEF-hand.R',
        
        'DEF-f_pinky.01.R.01' : 'DEF-palm.04.R',
        'DEF-f_pinky.01.R.02' : 'DEF-f_pinky.01.R.01',
        'DEF-f_pinky.02.R' : 'DEF-f_pinky.01.R.02',
        'DEF-f_pinky.03.R' : 'DEF-f_pinky.02.R',
        
        'DEF-f_ring.01.R.01' : 'DEF-palm.03.R',
        'DEF-f_ring.01.R.02' : 'DEF-f_ring.01.R.01',
        'DEF-f_ring.02.R' : 'DEF-f_ring.01.R.02',
        'DEF-f_ring.03.R' : 'DEF-f_ring.02.R',
        
        'DEF-f_middle.01.R.01' : 'DEF-palm.02.R',
        'DEF-f_middle.01.R.02' : 'DEF-f_middle.01.R.01',
        'DEF-f_middle.02.R' : 'DEF-f_middle.01.R.02',
        'DEF-f_middle.03.R' : 'DEF-f_middle.02.R',

        'DEF-f_index.01.R.01' : 'DEF-palm.01.R',
        'DEF-f_index.01.R.02' : 'DEF-f_index.01.R.01',
        'DEF-f_index.02.R' : 'DEF-f_index.01.R.02',
        'DEF-f_index.03.R' : 'DEF-f_index.02.R',

        'DEF-thumb.01.R.01' : 'DEF-hand.R',
        'DEF-thumb.01.R.02' : 'DEF-thumb.01.R.01',
        'DEF-thumb.02.R' : 'DEF-thumb.01.R.02',
        'DEF-thumb.03.R' : 'DEF-thumb.02.R',
        
        'DEF-thigh.01.R' : 'DEF-hips',
        'DEF-thigh.02.R' : 'DEF-thigh.01.R',
        'DEF-shin.01.R' : 'DEF-thigh.02.R',
        'DEF-shin.02.R' : 'DEF-shin.01.R',
        
        'DEF-foot.R' : 'DEF-shin.02.R',
        'DEF-toe.R' : 'DEF-foot.R',
        }

retarget_dict = {
        'root'                : 'Root'          , 
        'DEF-hips'            : 'pelvis'        , 
        'DEF-spine'           : 'spine_01'      , 
        'DEF-chest.01'        : 'spine_02'      , 
        'DEF-chest.02'        : 'spine_03'      , 
        'DEF-neck'            : 'neck_01'       , 
        'DEF-head'            : 'head'          , 

        # LEFT                                   
        'DEF-shoulder.L'      : 'clavicle_l'    , 
        'DEF-upper_arm.01.L'  : 'upperarm_l'    , 
        'DEF-forearm.01.L'    : 'lowerarm_l'    , 
        'DEF-hand.L'          : 'hand_l'        , 
        'DEF-f_pinky.01.L.01' : 'pinky_01_l'    , 
        'DEF-f_pinky.02.L'    : 'pinky_02_l'    , 
        'DEF-f_pinky.03.L'    : 'pinky_03_l'    , 
        'DEF-f_ring.01.L.01'  : 'ring_01_l'     , 
        'DEF-f_ring.02.L'     : 'ring_02_l'     , 
        'DEF-f_ring.03.L'     : 'ring_03_l'     , 
        'DEF-f_middle.01.L.01': 'middle_01_l'   , 
        'DEF-f_middle.02.L'   : 'middle_02_l'   , 
        'DEF-f_middle.03.L'   : 'middle_03_l'   , 
        'DEF-f_index.01.L.01' : 'index_01_l'    , 
        'DEF-f_index.02.L'    : 'index_02_l'    , 
        'DEF-f_index.03.L'    : 'index_03_l'    , 
        'DEF-thumb.01.L.01'   : 'thumb_01_l'    , 
        'DEF-thumb.02.L'      : 'thumb_02_l'    , 
        'DEF-thumb.03.L'      : 'thumb_03_l'    , 
        'DEF-thigh.01.L'      : 'thigh_l'       , 
        'DEF-shin.01.L'       : 'calf_l'        , 
        'DEF-foot.L'          : 'foot_l'        , 
        'DEF-toe.L'           : 'ball_l'        , 
        
        # RIGHT                                  
        'DEF-shoulder.R'      : 'clavicle_r'    , 
        'DEF-upper_arm.01.R'  : 'upperarm_r'    , 
        'DEF-forearm.01.R'    : 'lowerarm_r'    , 
        'DEF-hand.R'          : 'hand_r'        , 
        'DEF-f_pinky.01.R.01' : 'pinky_01_r'    , 
        'DEF-f_pinky.02.R'    : 'pinky_02_r'    , 
        'DEF-f_pinky.03.R'    : 'pinky_03_r'    , 
        'DEF-f_ring.01.R.01'  : 'ring_01_r'     , 
        'DEF-f_ring.02.R'     : 'ring_02_r'     , 
        'DEF-f_ring.03.R'     : 'ring_03_r'     , 
        'DEF-f_middle.01.R.01': 'middle_01_r'   , 
        'DEF-f_middle.02.R'   : 'middle_02_r'   , 
        'DEF-f_middle.03.R'   : 'middle_03_r'   , 
        'DEF-f_index.01.R.01' : 'index_01_r'    , 
        'DEF-f_index.02.R'    : 'index_02_r'    , 
        'DEF-f_index.03.R'    : 'index_03_r'    , 
        'DEF-thumb.01.R.01'   : 'thumb_01_r'    , 
        'DEF-thumb.02.R'      : 'thumb_02_r'    , 
        'DEF-thumb.03.R'      : 'thumb_03_r'    , 
        'DEF-thigh.01.R'      : 'thigh_r'       , 
        'DEF-shin.01.R'       : 'calf_r'        , 
        'DEF-foot.R'          : 'foot_r'        , 
        'DEF-toe.R'           : 'ball_r'        , 
        }

def make_constraint(context, rigify_object, export_rig_object):

    # Deselect all and select the rig
    bpy.ops.object.select_all(action='DESELECT')
    context.scene.objects.active = export_rig_object
    export_rig_object.select = True

    # Go to armature pose mode
    bpy.ops.object.mode_set(mode='POSE')

    pose_bones = export_rig_object.pose.bones
    bones = export_rig_object.data.bones

    # Set constraint
    for bone in bones:
        #pose_bones.active = bone
        bones.active = bone
        
        bpy.ops.pose.constraint_add(type="COPY_LOCATION")
        bpy.ops.pose.constraint_add(type="COPY_ROTATION")
        bpy.ops.pose.constraint_add(type="COPY_SCALE")
        
        # Add constraint target based by rig source object
        pose_bones[bone.name].constraints["Copy Location"].target = rigify_object
        pose_bones[bone.name].constraints["Copy Location"].subtarget = bone.name
        pose_bones[bone.name].constraints["Copy Rotation"].target = rigify_object
        pose_bones[bone.name].constraints["Copy Rotation"].subtarget = bone.name
        pose_bones[bone.name].constraints["Copy Scale"].target = rigify_object
        pose_bones[bone.name].constraints["Copy Scale"].subtarget = bone.name
        pose_bones[bone.name].constraints["Copy Scale"].target_space = 'LOCAL_WITH_PARENT'
        pose_bones[bone.name].constraints["Copy Scale"].owner_space = 'WORLD'
    
    # Back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

def get_vertex_group_names(objects):
    vg_names = []
    for obj in objects:
        for vg in obj.vertex_groups:
            if vg.name not in vg_names:
                vg_names.append(vg.name)
    return vg_names

def get_objects_using_rig(rig_object):

    mesh_objects = []

    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object == rig_object:
                mesh_objects.append(obj)
    
    return mesh_objects

def extract_export_rig(context, rigify_object, scale, meshes_to_evaluate = []):

    scene = context.scene

    # Check if this object is a proxy or not
    if rigify_object.proxy:
        rigify_object = rigify_object.proxy

    # Set to object mode
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Duplicate Rigify Object
    export_rig_ob = rigify_object.copy()
    export_rig_ob.name =(rigify_object.name + '_export')
    export_rig_ob.data = export_rig_ob.data.copy()
    export_rig_ob.scale *= scale
    export_rig = export_rig_ob.data
    scene.objects.link(export_rig_ob)

    # Deselect all and select the rig
    bpy.ops.object.select_all(action='DESELECT')
    scene.objects.active = export_rig_ob
    export_rig_ob.select = True

    # Go to armature edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Edit bones
    edit_bones = export_rig.edit_bones
    
    # Delete other than deform bones
    for bone in edit_bones:
        if 'DEF-' not in bone.name and bone.name != 'root':
            edit_bones.remove(bone)
    
    for bone in edit_bones:
        # Set parent
        if bone.name in parent_dict:
            bone.parent = edit_bones.get(parent_dict[bone.name])
        
        # Change active bone layers to layer 0
        for i, layer in enumerate(bone.layers):
            if i == 0: bone.layers[i] = True
            else: bone.layers[i] = False

    # Cleaning up unused bones based usage of meshes
    if any(meshes_to_evaluate):
        vg_names = get_vertex_group_names(meshes_to_evaluate)
        for bone in edit_bones:
            if bone.name not in vg_names and bone.name != 'root':
                edit_bones.remove(bone)

    # Change active armature layers to layer 0
    for i, layer in enumerate(export_rig.layers):
        if i == 0: export_rig.layers[i] = True
        else: export_rig.layers[i] = False
            
    # BEGIN: EVALUATE VALID RIGIFY

    # There can be only one root, check them for validity
    no_parents = []
    for bone in edit_bones:
        if not bone.parent:
            no_parents.append(bone)

    # If not found a bone or have many roots, it's counted as not valid
    if len(edit_bones) == 0 or len(no_parents) > 1:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.delete()
        return "FAILED! The rig is not a valid rigify!"

    # END: EVALUATE VALID RIGIFY

    # Go to pose mode
    bpy.ops.object.mode_set(mode='POSE')

    # Select all pose bones
    bpy.ops.pose.select_all(action='SELECT')

    # Clear all constraints
    bpy.ops.pose.constraints_clear()

    # Clear locking bones
    pose_bones = export_rig_ob.pose.bones
    for bone in pose_bones:
        bone.lock_location = [False, False, False]
        bone.lock_rotation = [False, False, False]
        bone.lock_rotation_w = False
        bone.lock_rotations_4d = False
        bone.lock_scale = [False, False, False]
    
    # Go back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply transform
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    return export_rig_ob

def extract_export_meshes(context, source_data, export_rig_ob, scale):
    
    scene = context.scene

    # Set to object mode
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect for safety purpose
    bpy.ops.object.select_all(action='DESELECT')

    # Duplicate Meshes
    export_objs = []
    for obj in source_data.mesh_objects:
        new_obj = obj.copy()
        new_obj.data = new_obj.data.copy()
        scene.objects.link(new_obj)

        # New objects scaling
        if new_obj.parent != source_data.rigify_object:
            new_obj.scale *= scale

        # Populate exported meshes list
        export_objs.append(new_obj)

        # Select this mesh
        new_obj.select = True

        # Change armature object to exported rig
        mod_armature = [mod for mod in new_obj.modifiers if mod.type == 'ARMATURE'][0]
        mod_armature.object = export_rig_ob

    # Apply transform to exported rig and mesh
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    return export_objs

def retarget_bone_name(rig_object):
    for bone in rig_object.data.bones:
        new_name = retarget_dict.get(bone.name)
        if new_name:
            bone.name = new_name


def evaluate_and_get_source_data(objects):

    source_data = SourceData()

    # If only select armature object
    if len(objects) == 1 and objects[0].type == 'ARMATURE':
        source_data.rigify_object = objects[0]
        source_data.mesh_objects = [o for o in bpy.data.objects if (
            o.type == 'MESH' and
            any(mod for mod in o.modifiers if (
                    mod.type == 'ARMATURE' and 
                    mod.object == source_data.rigify_object
                ))
            )]
    else:

        # Selected armatures
        armature_objs = [o for o in objects if o.type == 'ARMATURE']

        # If select more than one armatures
        if len(armature_objs) > 1:
            return "FAILED! You cannot export more than one armatures"
        
        # If select at least one armature
        elif len(armature_objs) == 1:
            source_data.rigify_object = armature_objs[0]

            # Evaluating mesh to be exported or not
            for obj in objects:
                if any([mod for mod in obj.modifiers if (
                    mod.type == 'ARMATURE' and mod.object == source_data.rigify_object)]):
                    source_data.mesh_objects.append(obj)
                elif obj.type == 'MESH':
                    source_data.failed_mesh_objects.append(obj)

        # If not select any armatures, search for possible armature
        elif len(armature_objs) == 0:

            # List to check of possibility armature modifier using different object
            armature_object_list = []

            for obj in objects:
                armature_mod = [mod for mod in obj.modifiers if (
                    mod.type == 'ARMATURE' and mod.object)]

                # If object has armature modifier
                if any(armature_mod):
                    # This object is legit to export
                    source_data.mesh_objects.append(obj)

                    # Add armature object used to list
                    armature_mod = armature_mod[0]
                    if armature_mod.object not in armature_object_list:
                        armature_object_list.append(armature_mod.object)

                # If object didn't have armature modifier or didn't set armature object,
                # do not export
                else:
                    source_data.failed_mesh_objects.append(obj)
                
            # If no armature found
            if not any(armature_object_list):
                return "FAILED! No armature found! Make sure have properly set your armature modifier."

            # If more than one armature object found
            elif len(armature_object_list) > 1:
                return "FAILED! There are more than one armature object variation on selected objects"

            source_data.rigify_object = armature_object_list[0]
    
    # If not found any mesh to be export
    if not(source_data.mesh_objects):
        return "FAILED! No objects valid to export! Make sure your armature modifiers are properly set."

    return source_data

def move_root(scene, obj):

    # Deselect all and select the rig
    bpy.ops.object.select_all(action='DESELECT')
    scene.objects.active = obj
    obj.select = True

    # Bake first
    bpy.ops.nla.bake(frame_start=scene.frame_start, 
            frame_end=scene.frame_end, 
            only_selected=False, 
            visual_keying=True, 
            clear_constraints=True, 
            bake_types={'POSE'})

    obj.animation_data.action.name = 'ZZ_EXPORT_TEMP_0'

    # Duplicate export rig
    temp_ob = obj.copy()
    temp_ob.data = obj.data.copy()
    scene.objects.link(temp_ob)
    temp_ob.select = False

    # Go to pose mode
    bpy.ops.object.mode_set(mode='POSE')

    # Shorten path
    bones = obj.data.bones
    pose_bones = obj.pose.bones
    
    # Root follow hips but only x and y axis
    bones.active = bones['root']
    bpy.ops.pose.constraint_add(type="COPY_LOCATION")
    pose_bones['root'].constraints['Copy Location'].target = temp_ob
    pose_bones['root'].constraints['Copy Location'].subtarget = 'DEF-hips'
    pose_bones['root'].constraints['Copy Location'].use_z = False
    
    # Hips follow original hips
    bones.active = bones['DEF-hips']
    bpy.ops.pose.constraint_add(type="COPY_LOCATION")
    pose_bones['DEF-hips'].constraints['Copy Location'].target = temp_ob
    pose_bones['DEF-hips'].constraints['Copy Location'].subtarget = 'DEF-hips'
    
    # Bake again!
    bpy.ops.nla.bake(frame_start=scene.frame_start, 
            frame_end=scene.frame_end, 
            only_selected=False, 
            visual_keying=True, 
            clear_constraints=True, 
            bake_types={'POSE'})   

    obj.animation_data.action.name = 'ZZ_EXPORT_TEMP_1'

    # Back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Select temp object
    scene.objects.active = temp_ob
    obj.select = False
    temp_ob.select = True

    # Delete temp object
    bpy.ops.object.delete()

    # Select back original object
    scene.objects.active = obj
    obj.select = True

class UE4HelperPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "objectmode"
    bl_label = "UE4 Export Helper"
    bl_category = "UE4 Helper"

    def draw(self, context):
        scene = context.scene

        #obj = context.active_object
        c = self.layout.column()
        c.label(text="Export mesh:")
        c.operator("export_mesh.rigify_fbx")
        c.label(text="Export animation:")
        c.operator("export_anim.rigify_fbx")
        #c.label(text="Custom export path:")
        #c.prop(scene, 'ue4helper_output_path', "")
        #c.label(text="Custom export name:")
        #c.prop(scene, 'ue4helper_filename', "")
        #c.label(text="Export setting:")
        #c.prop(scene, 'ue4helper_meshes_selection')
        #c.prop(scene, 'ue4helper_scaling')
        #c.prop(scene, 'ue4helper_all_meshes')

#class ExportRigifyAnim(bpy.types.Operator, ):
class ExportRigifyAnim(bpy.types.Operator, ExportHelper): #, IOFBXOrientationHelper): 
    """Nice Useful Tooltip"""
    bl_idname = "export_anim.rigify_fbx"
    bl_label = "Export Rigify action"
    bl_description = "Export active action as FBX file"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    global_scale = FloatProperty(
            name="Scale",
            min=0.001, max=1000.0,
            default=100.0,
            )

    remove_unused_bones = BoolProperty(
            name="Remove unused bones",
            description="Remove unused bones based from meshes usage", 
            default=True,
            )

    use_humanoid_name = BoolProperty(
            name="Use Unreal humanoid bone name",
            description="Use standard unreal humanoid bone name for easy retargeting", 
            default=True,
            )

    timeframe = EnumProperty(
            name = "Timeframe of the action",
            description="Option to select meshes to export", 
            items=(
                ('SCENE', "Scene timeframe", ""),
                ('ACTION', "Action length", ""),
                ('ACTION_MINUS_ONE', "Action length - 1 frame (loop animation)", ""),
                ), 
            default='ACTION',
            )

    hip_to_root = BoolProperty(
            name="Convert Hip XY location to Root location",
            description="Useful if you want to use root motion on UE4", 
            default=False,
            )

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select and obj.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "global_scale")
        layout.prop(self, "remove_unused_bones")
        layout.prop(self, "use_humanoid_name")
        layout.label(text="Timeframe of the action:")
        layout.prop(self, "timeframe", "")
        layout.prop(self, "hip_to_root")

    def execute(self, context):
        if not self.filepath:
            raise Exception("filepath not set")

        # Create save system to save current selection, mode, and active object
        state = SaveState(context)

        scene = context.scene

        # Active object is source rigify object
        rig_obj = context.object

        # Go to object mode first
        #bpy.ops.object.mode_set(mode='OBJECT')

        # Check action
        action = rig_obj.animation_data.action

        if not action:
            self.report({'ERROR'}, "FAILED! Please activate an action you want to export.")
            return{'CANCELLED'}

        # Extract export rig from rigify
        if self.remove_unused_bones:
            # If using linked lib
            mesh_objects = []
            if rig_obj.proxy_group:
                for obj in rig_obj.proxy_group.dupli_group.objects:
                    if obj.type == 'MESH':
                        mesh_objects.append(obj)
            else:
                mesh_objects = get_objects_using_rig(rig_obj)
            export_rig_ob = extract_export_rig(context, rig_obj, self.global_scale, mesh_objects)
        else: export_rig_ob = extract_export_rig(context, rig_obj, self.global_scale)

        # Scale original rig
        rig_obj.scale *= self.global_scale

        # Make constraint
        make_constraint(context, rig_obj, export_rig_ob)

        # Select only export rig
        bpy.ops.object.select_all(action='DESELECT')
        export_rig_ob.select = True
        scene.objects.active = export_rig_ob

        # Set timeframe
        #if self.timeframe == 'SCENE':
        #    start = scene.frame_start
        #    end = scene.frame_end
        #else:
        if self.timeframe != 'SCENE':
            scene.frame_start = action.frame_range[0]
            scene.frame_end = action.frame_range[1]
            if self.timeframe == 'ACTION_MINUS_ONE':
                scene.frame_end -= 1

        # Manual bake action if want to edit root bone
        if self.hip_to_root:
            move_root(scene, export_rig_ob)

        # Retarget bone name
        if self.use_humanoid_name:
            retarget_bone_name(export_rig_ob)

        # Set Global Matrix
        forward = '-Y'
        up = 'Z'
        global_matrix = (Matrix.Scale(1.0, 4) * axis_conversion(to_forward=forward, to_up=up,).to_4x4()) 

        # EXPORT!
        export_fbx_bin.save_single(self, scene, self.filepath,
                global_matrix=global_matrix,
                axis_up=up,
                axis_forward=forward,
                context_objects=context.selected_objects,
                object_types={'ARMATURE', 'MESH'},
                use_mesh_modifiers=True,
                mesh_smooth_type='EDGE',
                use_armature_deform_only=False,
                bake_anim=True,
                bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=False,
                bake_anim_use_all_actions=False,
                bake_anim_step=1.0,
                bake_anim_simplify_factor=0.0,
                add_leaf_bones=False,
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                use_metadata=True,
                path_mode='AUTO',
                use_mesh_edges=True,
                use_tspace=True,
                embed_textures=False,
                use_custom_props=False,
                bake_space_transform=False
                ) 

        # Delete exported object
        bpy.ops.object.delete()

        # Descale original rig
        rig_obj.scale /= self.global_scale

        # Load original state
        state.load(context)

        return {'FINISHED'}

class ExportRigifyMesh(bpy.types.Operator, ExportHelper):
    """Nice Useful Tooltip"""
    bl_idname = "export_mesh.rigify_fbx"
    bl_label = "Export Rigify mesh"
    bl_description = "Export rigify mesh as skeletal mesh FBX file"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    global_scale = FloatProperty(
            name="Scale",
            min=0.001, max=1000.0,
            default=100.0,
            )

    remove_unused_bones = BoolProperty(
            name="Remove unused bones",
            description="Remove unused bones based from meshes usage", 
            default=True,
            )

    use_humanoid_name = BoolProperty(
            name="Use Unreal humanoid bone name",
            description="Use standard unreal humanoid bone name for easy retargeting", 
            default=True,
            )

    @classmethod
    def poll(cls, context):
        objs = [obj for obj in context.selected_objects if (
            obj.proxy == None and # You can't export if object is linked
            (obj.type == 'MESH' or obj.type == 'ARMATURE') # Only mesh or armature can be exported
            )]
        return any(objs)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "global_scale")
        layout.prop(self, "remove_unused_bones")
        layout.prop(self, "use_humanoid_name")

    def execute(self, context):
        if not self.filepath:
            raise Exception("filepath not set")

        # Create save system to save current selection, mode, and active object
        state = SaveState(context)

        # Evaluate selected objects to export
        source_data = evaluate_and_get_source_data(context.selected_objects)

        # If evaluate returns string it means error
        if type(source_data) is str:
            state.load(context)
            self.report({'ERROR'}, source_data)
            return{'CANCELLED'}

        # Get export rig
        if self.remove_unused_bones:
            export_rig_ob = extract_export_rig(context, source_data.rigify_object, self.global_scale, source_data.mesh_objects)
        else: export_rig_ob = extract_export_rig(context, source_data.rigify_object, self.global_scale)

        # If returns string it means error
        if type(export_rig_ob) is str:
            state.load(context)
            self.report({'ERROR'}, export_rig_ob)
            return{'CANCELLED'}

        # Get export mesh objects
        export_mesh_objs = extract_export_meshes(context, source_data, export_rig_ob, self.global_scale)

        # Set to object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Select export objects
        export_rig_ob.select = True
        for obj in export_mesh_objs:
            obj.select = True

        # Retarget bone name
        if self.use_humanoid_name:
            retarget_bone_name(export_rig_ob)
        
        # Set Global Matrix
        forward = '-Y'
        up = 'Z'
        global_matrix = (Matrix.Scale(1.0, 4) * axis_conversion(to_forward=forward, to_up=up,).to_4x4()) 

        # EXPORT!
        export_fbx_bin.save_single(self, context.scene, self.filepath,
                global_matrix=global_matrix,
                axis_up=up,
                axis_forward=forward,
                context_objects=context.selected_objects,
                object_types={'ARMATURE', 'MESH'},
                use_mesh_modifiers=True,
                mesh_smooth_type='EDGE',
                use_armature_deform_only=False,
                bake_anim=False,
                bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=True,
                bake_anim_use_all_actions=True,
                bake_anim_step=1.0,
                bake_anim_simplify_factor=1.0,
                add_leaf_bones=False,
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                use_metadata=True,
                path_mode='AUTO',
                use_mesh_edges=True,
                use_tspace=True,
                embed_textures=False,
                use_custom_props=False,
                bake_space_transform=False
                ) 

        # Delete exported objects
        bpy.ops.object.delete()

        # Bring back original selection
        state.load(context)

        # Failed export objects
        #if any(source_data.failed_mesh_objects):
        #    obj_names = ''
        #    for i, obj in enumerate(source_data.failed_mesh_objects):
        #        obj_names += obj.name
        #        if i != len(source_data.failed_mesh_objects) - 1:
        #            obj_names += ', '
        #    
        #    self.report({'INFO'}, "INFO: Cannot export mesh [" + obj_names + "] because of reasons")

        self.report({'INFO'}, "INFO: What does the fox say?")

        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)

    # Settings
    #bpy.types.Scene.ue4helper_scaling = FloatProperty(
    #    name="Scaling",
    #    description="Export scale, For UE4, it's usually 100.0",
    #    min=0.1, max=200.0,
    #    default=100.0,
    #    step=2.0,
    #    precision=1
    #)

    #bpy.types.Scene.ue4helper_output_path = StringProperty(
    #    name = "Export path",
    #    description = "Path where to export, blank means blend directory",
    #    default = "", 
    #    maxlen = 1024,
    #    subtype = "DIR_PATH"
    #)   

    #bpy.types.Scene.ue4helper_filename = StringProperty(
    #    name = "File name",
    #    description = "Name of exported files, blank means object name",
    #    default = "", 
    #    maxlen = 1024,
    #    #subtype = "FILE_PATH"
    #)   

    #bpy.types.Scene.ue4helper_all_meshes = BoolProperty(
    #    name="All meshes using same rig",
    #    description="Export all meshes using same rig", 
    #    default=False,
    #    )

    #bpy.types.Scene.ue4helper_meshes_selection = EnumProperty(
    #        name = "Meshes to export",
    #        description="Option to select meshes to export", 
    #        items=(
    #            ('ALL_USE', "All objects using the rig", ""),
    #            ('ONLY_SELECTED', "Only selected objects", ""),
    #            ), 
    #        default='ALL_USE',
    #        )

def unregister():
	bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
