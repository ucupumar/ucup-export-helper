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

if "bpy" in locals():
    import importlib
    if "export_fbx_bin" in locals():
        importlib.reload(export_fbx_bin)

import bpy, math, os
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, BoolProperty, IntProperty, EnumProperty, StringProperty
from io_scene_fbx import export_fbx_bin
from bpy_extras.io_utils import (ExportHelper,
                                 #orientation_helper_factory,
                                 #path_reference_mode,
                                 axis_conversion,
                                 ) 

#IOFBXOrientationHelper = orientation_helper_factory("IOFBXOrientationHelper", axis_forward='-Z', axis_up='Y')

# Difference of scaling between Blender and Unreal
ABS_SCALE = 100.0

def get_addon_filepath():

    root = bpy.utils.script_path_user()
    sep = os.sep

    # get addons folder
    filepath = root + sep + "addons"

    # Dealing with two possible name for addon folder
    dirs = next(os.walk(filepath))[1]
    folder = [x for x in dirs if x == 'blender-ue4-tools' or x == 'blender-ue4-tools-master'][0]

    # Data necessary are in lib.blend
    return filepath + sep + folder + sep

def load_ue4_rig():

    filepath = get_addon_filepath() + 'lib.blend'
    armature_name = '__UE4_STANDARD_RIG'

    # Exist data
    exist_armatures = [arm.name for arm in bpy.data.armatures]

    # Load new data
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        # Append new data
        data_to.armatures.append(armature_name)

    # Check just added data
    arm = None
    if armature_name not in exist_armatures:
        arm = bpy.data.armatures.get(armature_name)
    else:
        # If data already available
        added_datas = [arm for arm in bpy.data.armatures if arm.name not in exist_armatures]
        if added_datas:
            arm = added_datas[0]

    return arm

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

    filepath = get_addon_filepath() + 'lib.blend'
    armature_name = 'HeroTPP_rig'
    mesh_name = 'HeroTPP'

    blendfile = get_addon_filepath() + 'lib.blend'
    section   = "\\Object\\"
    object    = "HeroTPP"
    
    filepath  = blendfile + section + object
    directory = blendfile + section
    filename  = object

    existed_objs = [obj.name for obj in bpy.data.objects]
    
    bpy.ops.wm.append(
        filepath=filepath, 
        filename=filename,
        directory=directory)

    wgt_objs = [obj for obj in bpy.data.objects if obj.name not in existed_objs and obj.name.startswith('WGT')]
    rig_obj = [obj for obj in bpy.data.objects if obj.name not in existed_objs and obj.name.startswith('HeroTPP_rig')][0]
    mesh_obj = [obj for obj in bpy.data.objects if obj.name not in existed_objs and obj.name.startswith('HeroTPP')][0]

    for wgt_obj in wgt_objs:
        wgt_obj.layers[19] = True
        for i in range(19):
            wgt_obj.layers[i] = False

    script = load_rigify_script()
    exec(script.as_string(), {})

    return rig_obj, mesh_obj

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

retarget_dict = {
        'root'                : 'Root'                  , 
        'DEF-spine'           : 'pelvis'                , 
        'DEF-spine.001'       : 'spine_01'              , 
        'DEF-spine.002'       : 'spine_02'              , 
        'DEF-spine.003'       : 'spine_03'              , 
        'DEF-spine.004'       : 'neck_01'               , 
        'DEF-spine.005'       : 'head'                  , 

        # LEFT                                           
        'DEF-shoulder.L'      : 'clavicle_l'            , 
        'DEF-upper_arm.L'     : 'upperarm_twist_01_l'   ,
        'DEF-upper_arm.L.001' : 'upperarm_l'            , 
        'DEF-forearm.L'       : 'lowerarm_l'            , 
        'DEF-forearm.L.001'   : 'lowerarm_twist_01_l'   , 
        'DEF-hand.L'          : 'hand_l'                , 
        'DEF-f_pinky.01.L'    : 'pinky_01_l'            , 
        'DEF-f_pinky.02.L'    : 'pinky_02_l'            , 
        'DEF-f_pinky.03.L'    : 'pinky_03_l'            , 
        'DEF-f_ring.01.L'     : 'ring_01_l'             , 
        'DEF-f_ring.02.L'     : 'ring_02_l'             , 
        'DEF-f_ring.03.L'     : 'ring_03_l'             , 
        'DEF-f_middle.01.L'   : 'middle_01_l'           , 
        'DEF-f_middle.02.L'   : 'middle_02_l'           , 
        'DEF-f_middle.03.L'   : 'middle_03_l'           , 
        'DEF-f_index.01.L'    : 'index_01_l'            , 
        'DEF-f_index.02.L'    : 'index_02_l'            , 
        'DEF-f_index.03.L'    : 'index_03_l'            , 
        'DEF-thumb.01.L'      : 'thumb_01_l'            , 
        'DEF-thumb.02.L'      : 'thumb_02_l'            , 
        'DEF-thumb.03.L'      : 'thumb_03_l'            , 
        'DEF-thigh.L'         : 'thigh_twist_01_l'      , 
        'DEF-thigh.L.001'     : 'thigh_l'               ,
        'DEF-shin.L'          : 'calf_l'                , 
        'DEF-shin.L.001'      : 'calf_twist_01_l'       , 
        'DEF-foot.L'          : 'foot_l'                , 
        'DEF-toe.L'           : 'ball_l'                , 
        
        # RIGHT                                          
        'DEF-shoulder.R'      : 'clavicle_r'            , 
        'DEF-upper_arm.R'     : 'upperarm_twist_01_r'   ,
        'DEF-upper_arm.R.001' : 'upperarm_r'            , 
        'DEF-forearm.R'       : 'lowerarm_r'            , 
        'DEF-forearm.R.001'   : 'lowerarm_twist_01_r'   , 
        'DEF-hand.R'          : 'hand_r'                , 
        'DEF-f_pinky.01.R'    : 'pinky_01_r'            , 
        'DEF-f_pinky.02.R'    : 'pinky_02_r'            , 
        'DEF-f_pinky.03.R'    : 'pinky_03_r'            , 
        'DEF-f_ring.01.R'     : 'ring_01_r'             , 
        'DEF-f_ring.02.R'     : 'ring_02_r'             , 
        'DEF-f_ring.03.R'     : 'ring_03_r'             , 
        'DEF-f_middle.01.R'   : 'middle_01_r'           , 
        'DEF-f_middle.02.R'   : 'middle_02_r'           , 
        'DEF-f_middle.03.R'   : 'middle_03_r'           , 
        'DEF-f_index.01.R'    : 'index_01_r'            , 
        'DEF-f_index.02.R'    : 'index_02_r'            , 
        'DEF-f_index.03.R'    : 'index_03_r'            , 
        'DEF-thumb.01.R'      : 'thumb_01_r'            , 
        'DEF-thumb.02.R'      : 'thumb_02_r'            , 
        'DEF-thumb.03.R'      : 'thumb_03_r'            , 
        'DEF-thigh.R'         : 'thigh_twist_01_r'      , 
        'DEF-thigh.R.001'     : 'thigh_r'               ,
        'DEF-shin.R'          : 'calf_r'                , 
        'DEF-shin.R.001'      : 'calf_twist_01_r'       , 
        'DEF-foot.R'          : 'foot_r'                , 
        'DEF-toe.R'           : 'ball_r'                , 
        }

def merge_vg(obj, vg1_name, vg2_name):
    vg1_index = -1
    vg2_index = -2
    
    #get index
    for group in obj.vertex_groups:
        if group.name == vg1_name:
            vg1_index = group.index
        elif group.name == vg2_name:
            vg2_index = group.index
    
    #select vertices
    for v in obj.data.vertices:
        for vg in v.groups:
            if vg.group == vg2_index:
                print(v.index)
                print(vg.weight)
                obj.vertex_groups[vg1_index].add([v.index],vg.weight,'ADD')
                
    vg2 = obj.vertex_groups.get(vg2_name)
    obj.vertex_groups.remove(vg2)

def make_root_constraint(context, rigify_object, export_rig_object):

    scene = context.scene

    # Goto object mode, deselect all and select the rig
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    scene.objects.active = export_rig_object
    export_rig_object.select = True

    # Make rigify at rest pose
    rigify_object.data.pose_position = 'REST'

    # Object constraint
    bpy.ops.object.constraint_add(type='CHILD_OF')
    export_rig_object.constraints['Child Of'].target = rigify_object
    export_rig_object.constraints['Child Of'].subtarget = 'root'

    # Context copy for inverse child of constraint
    context_copy = bpy.context.copy()
    context_copy['constraint'] = export_rig_object.constraints['Child Of']
    bpy.ops.constraint.childof_set_inverse(context_copy, constraint="Child Of", owner='OBJECT')

    # Revert rigify pose
    rigify_object.data.pose_position = 'POSE'

def make_humanoid_constraint(context, rigify_object, export_rig_object):
    
    scene = context.scene

    # Deselect all and select the rig
    bpy.ops.object.select_all(action='DESELECT')
    #scene.objects.active = export_rig_object
    #export_rig_object.select = True

    # Duplicate export rig as intermediate temporary rig
    temp_ob = export_rig_object.copy()
    temp_ob.data = export_rig_object.data.copy()
    temp_ob.data.name = '__TEMP__'
    scene.objects.link(temp_ob)
    scene.objects.active = temp_ob
    temp_ob.select = True

    rigify_object.data.pose_position = 'REST'

    # Go to edit mode to edit parent
    bpy.ops.object.mode_set(mode='EDIT')

    # Unparent all 
    for bone in temp_ob.data.edit_bones:
        #if bone.parent:
            #if bone.name != 'spine_03':
        bone.parent = None

    bpy.ops.object.mode_set(mode='POSE')

    # Shortcuts for temp object bones
    temp_bones = temp_ob.data.bones
    temp_pose_bones = temp_ob.pose.bones

    # Context copy
    context_copy = bpy.context.copy()

    # Temp object use child of constraint to all it's bones to rigify deform bones
    for bone in temp_bones:
        temp_bones.active = bone
        pose_bone = temp_pose_bones[bone.name]

        target_bone_name = [key for key, value in retarget_dict.items() if value == bone.name]

        if target_bone_name:
            target_bone_name = target_bone_name[0]
            bpy.ops.pose.constraint_add(type="CHILD_OF")
            pose_bone.constraints["Child Of"].target = rigify_object
            pose_bone.constraints["Child Of"].subtarget = target_bone_name

            context_copy['constraint'] = pose_bone.constraints['Child Of']
            bpy.ops.constraint.childof_set_inverse(context_copy, constraint="Child Of", owner='BONE')

    bpy.ops.object.mode_set(mode='OBJECT')

    # Select export rig
    scene.objects.active = export_rig_object
    export_rig_object.select = True

    bpy.ops.object.mode_set(mode='POSE')

    # Shortcuts
    pose_bones = export_rig_object.pose.bones
    bones = export_rig_object.data.bones

    for bone in bones:
        bones.active = bone
        pose_bone = pose_bones[bone.name]

        bpy.ops.pose.constraint_add(type="COPY_TRANSFORMS")
        pose_bone.constraints["Copy Transforms"].target = temp_ob
        pose_bone.constraints["Copy Transforms"].subtarget = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')

    rigify_object.data.pose_position = 'POSE'

    # Root constraint is really special case
    make_root_constraint(context, rigify_object, export_rig_object)

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

    # Root constraint is really special case
    make_root_constraint(context, rigify_object, export_rig_object)

def get_vertex_group_names(objects):
    vg_names = []
    for obj in objects:
        for vg in obj.vertex_groups:
            if vg.name not in vg_names:
                vg_names.append(vg.name)
    return vg_names

#def get_objects_using_rig(rig_object):
#
#    mesh_objects = []
#
#    for obj in bpy.data.objects:
#        for mod in obj.modifiers:
#            if mod.type == 'ARMATURE' and mod.object == rig_object:
#                mesh_objects.append(obj)
#    
#    return mesh_objects

#def extract_export_rig(context, rigify_object, scale, meshes_to_evaluate = []):
def extract_export_rig(context, rigify_object, scale):

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
    export_rig_ob.name = 'root'
    export_rig = export_rig_ob.data
    scene.objects.link(export_rig_ob)

    # Show x-ray for debugging
    export_rig_ob.show_x_ray = True

    # Deselect all and select the rig
    bpy.ops.object.select_all(action='DESELECT')
    scene.objects.active = export_rig_ob
    export_rig_ob.select = True

    # Go to armature edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Edit bones
    edit_bones = export_rig.edit_bones
    
    # Rearrange parent
    for bone in edit_bones:
        if bone.parent and bone.parent.name.startswith('ORG-'):
            parent_name = bone.parent.name.replace('ORG-', 'DEF-')
            parent = edit_bones.get(parent_name)
            bone.parent = parent

    # Delete other than deform bones
    for bone in edit_bones:
        #if 'DEF-' not in bone.name and bone.name != 'root':
        #if not bone.use_deform and bone.name != 'root':
        if not bone.use_deform:
            edit_bones.remove(bone)
    
    # Change active bone layers to layer 0
    for bone in edit_bones:
        for i, layer in enumerate(bone.layers):
            if i == 0: bone.layers[i] = True
            else: bone.layers[i] = False

    # Cleaning up unused bones based usage of meshes
    # Usually for deleting hand palm bones and some others
    #if any(meshes_to_evaluate):
    #    vg_names = get_vertex_group_names(meshes_to_evaluate)
    #    for bone in edit_bones:
    #        if bone.name not in vg_names and bone.name != 'root':
    #            edit_bones.remove(bone)

    # Change active armature layers to layer 0
    for i, layer in enumerate(export_rig.layers):
        if i == 0: export_rig.layers[i] = True
        else: export_rig.layers[i] = False

    # Go to pose mode
    bpy.ops.object.mode_set(mode='POSE')

    # Select all pose bones
    bpy.ops.pose.select_all(action='SELECT')

    # Clear all constraints
    bpy.ops.pose.constraints_clear()

    # Delete drivers
    #for driver in export_rig_ob.animation_data.drivers:
    #    print(driver.data_path)
    export_rig_ob.animation_data_clear()

    # Remove rig_id used by rigify rig_ui.py
    bpy.ops.wm.properties_remove(data_path = 'active_object.data', property = 'rig_id')

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

    # BEGIN: EVALUATE VALID RIGIFY

    # There can be only one root, check them for validity
    roots = []
    for bone in export_rig.bones:
        if not bone.parent:
            roots.append(bone)

    # If not found a bone or have many roots, it's counted as not valid
    if len(export_rig.bones) == 0 or len(roots) > 1:
        #bpy.ops.object.mode_set(mode='OBJECT')
        #bpy.ops.object.delete()
        return "FAILED! The rig is not a valid rigify!"

    # END: EVALUATE VALID RIGIFY

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
        #if new_obj.parent != source_data.rigify_object:
        #    print('aaaaaaaa')
        #    new_obj.scale *= scale

        # Select this mesh
        new_obj.select = True
        scene.objects.active = new_obj

        # Clear parent
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # Scale mesh
        new_obj.scale *= scale
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # Parent to export rig
        new_obj.parent = export_rig_ob

        # Populate exported meshes list
        export_objs.append(new_obj)

        # Change armature object to exported rig
        mod_armature = [mod for mod in new_obj.modifiers if mod.type == 'ARMATURE'][0]
        mod_armature.object = export_rig_ob

        new_obj.select = False

    # Apply transform to exported rig and mesh
    #bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    return export_objs

def convert_to_unreal_humanoid(rig_object, scale, mesh_objects = []):

    scene = bpy.context.scene

    # Set to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Load ue4 humanoid
    source_arm = load_ue4_rig()
    source_obj = bpy.data.objects.new('source_rig', source_arm)
    scene.objects.link(source_obj)
    source_obj.scale *= scale
    source_obj.show_x_ray = True

    # Get ue4 humanoid object matrices
    source_matrix = {}
    scene.objects.active = source_obj
    source_obj.select = True
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in source_arm.edit_bones:
        source_matrix[eb.name] = eb.matrix
    bpy.ops.object.mode_set(mode='OBJECT')

    # Rename bones
    for bone in rig_object.data.bones:
        new_name = retarget_dict.get(bone.name)
        if new_name:
            bone.name = new_name

    # Rename vertex groups
    for o in mesh_objects:
        for vg in o.vertex_groups:
            if vg.name in retarget_dict:
                vg.name = retarget_dict[vg.name]

    scene.objects.active = rig_object
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = rig_object.data.edit_bones

    # Unconnect all the bones
    for bone in edit_bones:
        bone.use_connect = False

    #    # Load ue4 humanoid matrix
    #    if bone.name in source_matrix:

    #        source_m = source_matrix[bone.name]
    #        
    #        # location of the bone
    #        loc = bone.matrix.to_translation()

    #        # UE4 Humanoid rig has standard upperarm close with the twist upperarm
    #        if bone.name in {'upperarm_l', 'upperarm_r'}:

    #            twist_name = bone.parent.name

    #            # delta of the upperarm and twist upperarm in original ue4 humanoid
    #            ori_loc = source_matrix[bone.name].to_translation()
    #            ori_twist_name = source_matrix[twist_name].to_translation()
    #            delta = ori_loc - ori_twist_name

    #            twist_loc = edit_bones.get(twist_name).matrix.to_translation()
    #            loc = twist_loc + delta

    #        # Use ue4 humanoid rotation but keep the location
    #        bone.matrix = Matrix([
    #            (source_m[0][0], source_m[0][1], source_m[0][2], loc.x),
    #            (source_m[1][0], source_m[1][1], source_m[1][2], loc.y),
    #            (source_m[2][0], source_m[2][1], source_m[2][2], loc.z),
    #            (0.0, 0.0, 0.0, 1.0),
    #            ])

    # Flip thigh and upperarm bones position with its twist
    for bone in edit_bones:
        if bone.name in {'thigh_l', 'thigh_r', 'upperarm_l', 'upperarm_r'}:
            twist_bone = bone.parent
            twist_pos = twist_bone.matrix.to_translation()
            pos = bone.matrix.to_translation()

            bone.matrix = Matrix([
                (bone.matrix[0][0], bone.matrix[0][1], bone.matrix[0][2], twist_pos.x),
                (bone.matrix[1][0], bone.matrix[1][1], bone.matrix[1][2], twist_pos.y),
                (bone.matrix[2][0], bone.matrix[2][1], bone.matrix[2][2], twist_pos.z),
                (0.0, 0.0, 0.0, 1.0),
                ])

            twist_bone.matrix = Matrix([
                (twist_bone.matrix[0][0], twist_bone.matrix[0][1], twist_bone.matrix[0][2], pos.x),
                (twist_bone.matrix[1][0], twist_bone.matrix[1][1], twist_bone.matrix[1][2], pos.y),
                (twist_bone.matrix[2][0], twist_bone.matrix[2][1], twist_bone.matrix[2][2], pos.z),
                (0.0, 0.0, 0.0, 1.0),
                ])

    # Edit some parents
    for bone in edit_bones:
        if any([p for p in {'upperarm_', 'thigh_'} if bone.name.startswith(p)]):
            bone.parent = None

    edit_bones['upperarm_twist_01_l'].parent = edit_bones['upperarm_l']
    edit_bones['upperarm_twist_01_r'].parent = edit_bones['upperarm_r']
    edit_bones['upperarm_l'].parent = edit_bones['clavicle_l']
    edit_bones['upperarm_r'].parent = edit_bones['clavicle_r']

    edit_bones['thigh_twist_01_l'].parent = edit_bones['thigh_l']
    edit_bones['thigh_twist_01_r'].parent = edit_bones['thigh_r']
    edit_bones['thigh_l'].parent = edit_bones['pelvis']
    edit_bones['thigh_r'].parent = edit_bones['pelvis']

    edit_bones['lowerarm_l'].parent = edit_bones['upperarm_l']
    edit_bones['lowerarm_r'].parent = edit_bones['upperarm_r']

    edit_bones['hand_l'].parent = edit_bones['lowerarm_l']
    edit_bones['hand_r'].parent = edit_bones['lowerarm_r']

    edit_bones['calf_l'].parent = edit_bones['thigh_l']
    edit_bones['calf_r'].parent = edit_bones['thigh_r']

    edit_bones['foot_l'].parent = edit_bones['calf_l']
    edit_bones['foot_r'].parent = edit_bones['calf_r']

    # Back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Delete ue4_rig
    bpy.data.armatures.remove(source_arm, True)

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

#class ExportRigifyAnim(bpy.types.Operator, ):
class ExportRigifyAnim(bpy.types.Operator, ExportHelper): #, IOFBXOrientationHelper): 
    bl_idname = "export_anim.rigify_fbx"
    bl_label = "Export Rigify action"
    bl_description = "Export active action as FBX file"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    global_scale = FloatProperty(
            name="Scale",
            min=0.001, max=1000.0,
            default=1.0,
            )

    #remove_unused_bones = BoolProperty(
    #        name="Remove unused bones",
    #        description="Remove unused bones based from meshes usage", 
    #        default=True,
    #        )

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
        return obj and obj.select and obj.type == 'ARMATURE' and obj.animation_data and obj.animation_data.action

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "global_scale")
        #layout.prop(self, "remove_unused_bones")
        layout.prop(self, "use_humanoid_name")
        layout.label(text="Timeframe of the action:")
        layout.prop(self, "timeframe", "")
        layout.prop(self, "hip_to_root")

    def invoke(self, context, event):
        action = context.object.animation_data.action
        directory = os.path.dirname(context.blend_data.filepath)

        self.filepath = os.path.join(directory, action.name + self.filename_ext)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath:
            raise Exception("filepath not set")

        # Create save system to save current selection, mode, and active object
        state = SaveState(context)

        scene = context.scene

        # Active object is source rigify object
        rig_obj = context.object

        # Check action
        action = rig_obj.animation_data.action

        # Scale of the objects
        scale = ABS_SCALE * self.global_scale

        if not action:
            self.report({'ERROR'}, "FAILED! Please activate an action you want to export.")
            return{'CANCELLED'}

        # Extract export rig from rigify
        #if self.remove_unused_bones:
        #    # If using linked lib
        #    mesh_objects = []
        #    if rig_obj.proxy_group:
        #        for obj in rig_obj.proxy_group.dupli_group.objects:
        #            if obj.type == 'MESH':
        #                mesh_objects.append(obj)
        #    else:
        #        mesh_objects = get_objects_using_rig(rig_obj)
        #    export_rig_ob = extract_export_rig(context, rig_obj, scale, mesh_objects)
        #else: export_rig_ob = extract_export_rig(context, rig_obj, scale)
        export_rig_ob = extract_export_rig(context, rig_obj, scale)

        # Scale original rig
        rig_obj.scale *= scale

        # Set timeframe
        if self.timeframe != 'SCENE':
            scene.frame_start = action.frame_range[0]
            scene.frame_end = action.frame_range[1]
            if self.timeframe == 'ACTION_MINUS_ONE':
                scene.frame_end -= 1

        if not self.use_humanoid_name:
            # Make constraint
            make_constraint(context, rig_obj, export_rig_ob)

            # Manual bake action if want to edit root bone
            #if self.hip_to_root:
            #    move_root(scene, export_rig_ob)

        else:
            # Retarget bone name
            convert_to_unreal_humanoid(export_rig_ob, scale)

            # Make humanoid constraint
            make_humanoid_constraint(context, rig_obj, export_rig_ob)

        # Select only export rig
        bpy.ops.object.select_all(action='DESELECT')
        export_rig_ob.select = True
        scene.objects.active = export_rig_ob

        #return {'FINISHED'}

        # Set Global Matrix
        forward = '-Y'
        up = 'Z'
        global_matrix = (Matrix.Scale(1.0/ABS_SCALE, 4) * axis_conversion(to_forward=forward, to_up=up,).to_4x4()) 

        ## EXPORT!
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

        # Delete temporary rig
        for arm in bpy.data.armatures:
            if arm.name.startswith('__TEMP__'):
                bpy.data.armatures.remove(arm, True)

        # Descale original rig
        rig_obj.scale /= scale

        # Load original state
        state.load(context)

        return {'FINISHED'}

class ExportRigifyMesh(bpy.types.Operator, ExportHelper):
    bl_idname = "export_mesh.rigify_fbx"
    bl_label = "Export Rigify mesh"
    bl_description = "Export rigify mesh as skeletal mesh FBX file"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    global_scale = FloatProperty(
            name="Scale",
            min=0.001, max=1000.0,
            default=1.0,
            )

    #remove_unused_bones = BoolProperty(
    #        name="Remove unused bones",
    #        description="Remove unused bones based from meshes usage", 
    #        default=True,
    #        )

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
        #layout.prop(self, "remove_unused_bones")
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

        # Scale of the objects
        scale = ABS_SCALE * self.global_scale

        # Get export rig
        #if self.remove_unused_bones:
        #    export_rig_ob = extract_export_rig(context, source_data.rigify_object, scale, source_data.mesh_objects)
        #else: export_rig_ob = extract_export_rig(context, source_data.rigify_object, scale)
        export_rig_ob = extract_export_rig(context, source_data.rigify_object, scale)

        # If returns string it means error
        if type(export_rig_ob) is str:
            state.load(context)
            self.report({'ERROR'}, export_rig_ob)
            return{'CANCELLED'}

        # Get export mesh objects
        export_mesh_objs = extract_export_meshes(context, source_data, export_rig_ob, scale)

        # Set to object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Select export objects
        export_rig_ob.select = True
        for obj in export_mesh_objs:
            obj.select = True

        # Retarget bone name and vertex groups
        if self.use_humanoid_name:
            convert_to_unreal_humanoid(export_rig_ob, scale, export_mesh_objs)

        #return {'FINISHED'}

        # Set Global Matrix
        forward = '-Y'
        up = 'Z'
        #global_matrix = (Matrix.Scale(1.0, 4) * axis_conversion(to_forward=forward, to_up=up,).to_4x4()) 
        # Descale global matrix because Unreal always multiply object by 100 points when importing
        global_matrix = (Matrix.Scale(1.0/ABS_SCALE, 4) * axis_conversion(to_forward=forward, to_up=up,).to_4x4()) 

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
        if any(source_data.failed_mesh_objects):
            obj_names = ''
            for i, obj in enumerate(source_data.failed_mesh_objects):
                obj_names += obj.name
                if i != len(source_data.failed_mesh_objects) - 1:
                    obj_names += ', '
            
            self.report({'INFO'}, "INFO: Cannot export mesh [" + obj_names + "] because of reasons")

        self.report({'INFO'}, "INFO: What does the fox say?")

        return {'FINISHED'}

class RotateBones(bpy.types.Operator):
    bl_idname = "armature.rotate_bones_to_unreal_like"
    bl_label = "(Don't use!) Rotate Bones to Unreal-like"
    bl_description = "Rotate bones to make it more like unreal"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'ARMATURE'

    def execute(self, context):
        obj = context.object
        scene = context.scene

        # Remember
        ori_obj = obj.name
        ori_layers = []
        for l in scene.layers:
            ori_layers.append(l)
        ori_mode = obj.mode

        # Go to object mode first
        bpy.ops.object.mode_set(mode='OBJECT')

        # Make all layers active
        for i in range(len(scene.layers)):
            scene.layers[i] = True

        # Load ue4 rig
        source_arm = load_ue4_rig()
        source_obj = bpy.data.objects.new('source_rig', source_arm)
        scene.objects.link(source_obj)

        # Active object is the target object
        target_obj = bpy.context.object
        target_arm = target_obj.data

        # Get source object matrices
        source_matrix = {}
        scene.objects.active = source_obj
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in source_arm.edit_bones:
            source_matrix[eb.name] = eb.matrix
        bpy.ops.object.mode_set(mode='OBJECT')

        print()

        # Go to target_obj
        scene.objects.active = target_obj
        bpy.ops.object.mode_set(mode='EDIT')

        for eb in target_arm.edit_bones:
            target_rot = eb.matrix.to_quaternion()
            if eb.name not in source_matrix: continue
            source_rot = source_matrix[eb.name].to_quaternion()

            diff = target_rot.rotation_difference(source_rot)
            diff_euler = diff.to_euler()

            x = math.degrees(diff_euler[0])
            y = math.degrees(diff_euler[1])
            z = math.degrees(diff_euler[2])

            print(eb.name.ljust(24), 
                    str(round(x, 2)).ljust(10),
                    str(round(y, 2)).ljust(10),
                    str(round(z, 2)).ljust(10))

            source_m = source_matrix[eb.name]
            source_rot_m = source_matrix[eb.name].to_3x3()
            target_rot_m = eb.matrix.to_3x3()
            diff_m = diff.to_matrix()

            print(target_rot_m)
            target_rot_m.rotate(diff_m)

            #print(target_rot_m)
            print(eb.matrix)

            new_mat = Matrix([
                (source_m[0][0], source_m[0][1], source_m[0][2], eb.matrix[0][3]),
                (source_m[1][0], source_m[1][1], source_m[1][2], eb.matrix[1][3]),
                (source_m[2][0], source_m[2][1], source_m[2][2], eb.matrix[2][3]),
                (0.0, 0.0, 0.0, 1.0),
                ])

            print(new_mat)

            eb.matrix = new_mat

            print(eb.matrix)
            print()

            #eb.matrix.rotate

        bpy.ops.object.mode_set(mode='OBJECT')

        # Delete ue4_rig
        bpy.data.armatures.remove(source_arm, True)

        # Recover
        scene.objects.active = scene.objects.get(obj.name)
        bpy.ops.object.mode_set(mode=ori_mode)
        for i, l in enumerate(ori_layers):
            scene.layers[i] = l

        return {'FINISHED'}

class AddHeroTPP(bpy.types.Operator):
    bl_idname = "object.add_standard_ue4_tpp"
    bl_label = "Add Standard UE4 TPP"
    bl_description = "Add standard UE4 Third Person Character with Rigify"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        rig_obj, mesh_obj = load_ue4_hero_tpp()
        scene.objects.active = rig_obj
        rig_obj.location = scene.cursor_location.copy()
        mesh_obj.select = False
        return {'FINISHED'}

class UE4HelperPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "objectmode"
    bl_label = "UE4 Export Helper"
    bl_category = "UE4 Helper"

    def draw(self, context):
        scene = context.scene

        c = self.layout.column()
        c.label(text="Export mesh:")
        c.operator("export_mesh.rigify_fbx")
        c.label(text="Export animation:")
        c.operator("export_anim.rigify_fbx")
        c.label(text="Rigify stuff:")
        c.operator("object.add_standard_ue4_tpp")
        #c.operator("armature.rotate_bones_to_unreal_like")

def register():
    bpy.utils.register_module(__name__)

def unregister():
	bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
