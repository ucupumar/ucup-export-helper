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
from bpy.props import *
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

def get_current_armature_object():
    obj = bpy.context.object
    if not obj: return None

    if obj.type == 'ARMATURE':
        return obj

    arm_obj = None
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE' and mod.object:
            arm_obj = mod.object
            break
    return arm_obj

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

#retarget_dict = {
std_retarget_dict = {
        'root'                : 'Root'                  , 
        #'DEF-spine'           : 'pelvis'                , 
        #'DEF-spine.001'       : 'spine_01'              , 
        #'DEF-spine.002'       : 'spine_02'              , 
        #'DEF-spine.003'       : 'spine_03'              , 
        #'DEF-spine.004'       : 'neck_01'               , 
        #'DEF-spine.005'       : 'head'                  , 

        # LEFT                                           
        'DEF-shoulder.L'      : 'clavicle_l'            , 
        #'DEF-upper_arm.L'     : 'upperarm_twist_01_l'   ,
        #'DEF-upper_arm.L.001' : 'upperarm_l'            , 
        #'DEF-forearm.L'       : 'lowerarm_l'            , 
        #'DEF-forearm.L.001'   : 'lowerarm_twist_01_l'   , 
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
        #'DEF-thigh.L'         : 'thigh_twist_01_l'      , 
        #'DEF-thigh.L.001'     : 'thigh_l'               ,
        #'DEF-shin.L'          : 'calf_l'                , 
        #'DEF-shin.L.001'      : 'calf_twist_01_l'       , 
        'DEF-foot.L'          : 'foot_l'                , 
        'DEF-toe.L'           : 'ball_l'                , 
        
        # RIGHT                                          
        'DEF-shoulder.R'      : 'clavicle_r'            , 
        #'DEF-upper_arm.R'     : 'upperarm_twist_01_r'   ,
        #'DEF-upper_arm.R.001' : 'upperarm_r'            , 
        #'DEF-forearm.R'       : 'lowerarm_r'            , 
        #'DEF-forearm.R.001'   : 'lowerarm_twist_01_r'   , 
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
        #'DEF-thigh.R'         : 'thigh_twist_01_r'      , 
        #'DEF-thigh.R.001'     : 'thigh_r'               ,
        #'DEF-shin.R'          : 'calf_r'                , 
        #'DEF-shin.R.001'      : 'calf_twist_01_r'       , 
        'DEF-foot.R'          : 'foot_r'                , 
        'DEF-toe.R'           : 'ball_r'                , 
        }

suffix_dict = {
        '.L' : '_l',
        '.R' : '_r',
        }

def get_retarget_dict(rig_object):
    retarget_dict = std_retarget_dict.copy()
    # Check number of spines first
    bones = rig_object.data.bones

    # Get limb bones
    limb_names = ['DEF-upper_arm.L', 'DEF-upper_arm.R',
                  'DEF-forearm.L', 'DEF-forearm.R',
                  'DEF-thigh.L', 'DEF-thigh.R',
                  'DEF-shin.L', 'DEF-shin.R',
                  ]
    limbs = {}
    for bone in bones:
        if bone.name in limb_names:
            # Search for its childs
            limbs[bone.name] = [bone]
            cur_bone = bone
            while True:
                child_bone = [b for b in bones if b.parent == cur_bone and bone.name in b.name]
                if child_bone:
                    limbs[bone.name].append(child_bone[0])
                    cur_bone = child_bone[0]
                else:
                    break

    limb_prefixes = {
            'DEF-upper_arm' : 'upperarm',
            'DEF-forearm'   : 'lowerarm',
            'DEF-thigh'     : 'thigh',
            'DEF-shin'      : 'calf',
            }

    # Add limb bones to dictionary
    for parent_name, limb_bones in limbs.items():

        prefix = [[b, a] for b, a in limb_prefixes.items() if b in parent_name]
        if not prefix: continue

        prefix_before = prefix[0][0]
        prefix_after = prefix[0][1]
        suffix_before = parent_name[-2:]
        suffix_after = suffix_dict[suffix_before]

        # Upperarm and thigh has inversed bones
        if prefix_before in {'DEF-upper_arm', 'DEF-thigh'}:
            iterator = reversed(limb_bones)
        else: iterator = limb_bones

        for i, bone in enumerate(iterator):
            if i == 0:
                retarget_dict[bone.name] = prefix_after + suffix_after
            else:
                retarget_dict[bone.name] = prefix_after + '_twist_' + str(i).zfill(2) + suffix_after

    # Get all the spines sorted
    spines = []
    super_spine = bones.get('DEF-spine')
    if super_spine:
        spines.append(super_spine)
        cur_spine = super_spine
        while True:
            bone = [bone for bone in bones if bone.name.startswith('DEF-spine.') and bone.parent == cur_spine]
            if bone:
                bone = bone[0]
                spines.append(bone)
                cur_spine = bone
            else:
                break

    # Get the last spine
    last_spine = None
    mch_neck = bones.get('MCH-ROT-neck')
    if mch_neck:
        last_spine_name = mch_neck.parent.name.replace('MCH-', 'DEF-')
        last_spine = bones.get(last_spine_name)

    # Add spine dictionary
    last_idx = len(spines)-1
    last_spine_found = False
    last_spine_idx = 0
    for i, spine in enumerate(spines):
        # First bone is pelvis
        if i == 0:
            retarget_dict[spine.name] = 'pelvis'
            continue

        # Last index is head
        if i == last_idx:
            retarget_dict[spine.name] = 'head'
            continue

        # Spine bones before the last one found
        if i >= 1 and not last_spine_found:
            retarget_dict[spine.name] = 'spine_' + str(i).zfill(2)
            if spine == last_spine:
                last_spine_found = True
                last_spine_idx = i
                continue

        # Neck bones are after last spine
        if last_spine_found:
            retarget_dict[spine.name] = 'neck_' + str(i-last_spine_idx).zfill(2)

    #print(retarget_dict)

    return retarget_dict

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

    # Get retarget dictionary
    retarget_dict = get_retarget_dict(rigify_object)

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

def make_constraint(context, rig_object, export_rig_object):

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
        pose_bones[bone.name].constraints["Copy Location"].target = rig_object
        pose_bones[bone.name].constraints["Copy Location"].subtarget = bone.name
        pose_bones[bone.name].constraints["Copy Rotation"].target = rig_object
        pose_bones[bone.name].constraints["Copy Rotation"].subtarget = bone.name
        pose_bones[bone.name].constraints["Copy Scale"].target = rig_object
        pose_bones[bone.name].constraints["Copy Scale"].subtarget = bone.name
        pose_bones[bone.name].constraints["Copy Scale"].target_space = 'LOCAL_WITH_PARENT'
        pose_bones[bone.name].constraints["Copy Scale"].owner_space = 'WORLD'
    
    # Back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Root constraint is really special case
    make_root_constraint(context, rig_object, export_rig_object)

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

#def extract_export_rig(context, source_object, scale, meshes_to_evaluate = []):
def extract_export_rig(context, source_object, scale, use_rigify=False):

    scene = context.scene

    # Check if this object is a proxy or not
    if source_object.proxy:
        source_object = source_object.proxy

    # Set to object mode
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Duplicate Rigify Object
    export_rig_ob = source_object.copy()
    export_rig_ob.name =(source_object.name + '_export')
    export_rig_ob.data = export_rig_ob.data.copy()
    export_rig_ob.scale *= scale
    export_rig_ob.name = 'root'
    export_rig = export_rig_ob.data
    scene.objects.link(export_rig_ob)

    # Show x-ray for debugging
    export_rig_ob.show_x_ray = True

    # Deselect all and select the export rig
    bpy.ops.object.select_all(action='DESELECT')
    scene.objects.active = export_rig_ob
    export_rig_ob.select = True

    # Go to armature edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Edit bones
    edit_bones = export_rig.edit_bones
    
    # Rearrange parent (RIGIFY ONLY)
    if use_rigify:
        for bone in edit_bones:
            if bone.parent and bone.parent.name.startswith('ORG-'):
                parent_name = bone.parent.name.replace('ORG-', 'DEF-')
                parent = edit_bones.get(parent_name)
                bone.parent = parent

    # Delete other than deform bones
    for bone in edit_bones:
        b = export_rig.bones.get(bone.name)
        #if 'DEF-' not in bone.name and bone.name != 'root':
        #if not bone.use_deform and bone.name != 'root':
        if not bone.use_deform and not b.ue4h_props.force_export:
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

    # Remove rig_id used by rigify rig_ui.py (RIGIFY ONLY)
    if use_rigify:
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
    #roots = []
    #for bone in export_rig.bones:
    #    if not bone.parent:
    #        roots.append(bone)

    ## If not found a bone or have many roots, it's counted as not valid
    #if len(export_rig.bones) == 0 or len(roots) > 1:
    #    #bpy.ops.object.mode_set(mode='OBJECT')
    #    #bpy.ops.object.delete()
    #    return "FAILED! The rig is not a valid rigify!"

    # END: EVALUATE VALID RIGIFY

    return export_rig_ob

def extract_export_meshes(context, mesh_objects, export_rig_ob, scale):
    
    scene = context.scene

    # Set to object mode
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect for safety purpose
    bpy.ops.object.select_all(action='DESELECT')

    # Duplicate Meshes
    export_objs = []
    for obj in mesh_objects:
        #print(obj.name)
        obj.select = True
        scene.objects.active = obj

        bpy.ops.object.duplicate()

        new_obj = scene.objects.active

        #new_obj = obj.copy()
        #new_obj.data = new_obj.data.copy()
        #scene.objects.link(new_obj)

        # New objects scaling
        #if new_obj.parent != rig_object:
        #    print('aaaaaaaa')
        #    new_obj.scale *= scale

        # Select this mesh
        #new_obj.select = True
        #scene.objects.active = new_obj

        # Clear parent
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # Scale mesh
        new_obj.scale *= scale
        new_obj.location *= scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # Parent to export rig
        new_obj.parent = export_rig_ob

        # Populate exported meshes list
        export_objs.append(new_obj)

        # Change armature object to exported rig
        mod_armature = [mod for mod in new_obj.modifiers if mod.type == 'ARMATURE'][0]
        mod_armature.object = export_rig_ob

        #obj.select = False
        new_obj.select = False

    # Apply transform to exported rig and mesh
    #bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    return export_objs

def convert_to_unreal_humanoid(rigify_obj, export_rig_obj, scale, mesh_objects = []):

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

    # Get retarget dictionary
    retarget_dict = get_retarget_dict(rigify_obj)

    # Rename bones
    for bone in export_rig_obj.data.bones:
        new_name = retarget_dict.get(bone.name)
        if new_name:
            bone.name = new_name

    # Rename vertex groups
    for o in mesh_objects:
        for vg in o.vertex_groups:
            if vg.name in retarget_dict:
                vg.name = retarget_dict[vg.name]

    scene.objects.active = export_rig_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = export_rig_obj.data.edit_bones

    # Unconnect all the bones
    for bone in edit_bones:
        bone.use_connect = False

    # Reverse limb bones
    master_lib_names = ['upperarm_l', 'upperarm_r', 'thigh_l', 'thigh_r']
    limb_chains = {}
    for name in master_lib_names:
        master_bone = edit_bones.get(name)
        if not master_bone: continue

        suffix = name[-2:]
        prefix = name[:-2]

        limb_chains[name] = [master_bone]
        cur_bone = master_bone
        while True:
            bone = cur_bone.parent
            if bone.name.startswith(prefix):
                limb_chains[name].append(bone)
                cur_bone = bone
            else:
                break

    # Reverse things
    for master_name, limb_bones in limb_chains.items():
        if not limb_bones: continue

        last_idx = len(limb_bones)-1
        last_parent = limb_bones[last_idx].parent

        matrices = []

        # Reverse parent
        for i, bone in enumerate(limb_bones):
            matrices.append(bone.matrix.copy())
            if i == 0:
                bone.parent = last_parent
            else: bone.parent = limb_bones[i-1]

        # Reverse matrix
        for i, matrix in enumerate(reversed(matrices)):
            ori_matrix = limb_bones[i].matrix
            new_loc = matrix.to_translation()
            limb_bones[i].matrix = Matrix([
                (ori_matrix[0][0], ori_matrix[0][1], ori_matrix[0][2], new_loc.x),
                (ori_matrix[1][0], ori_matrix[1][1], ori_matrix[1][2], new_loc.y),
                (ori_matrix[2][0], ori_matrix[2][1], ori_matrix[2][2], new_loc.z),
                (0.0, 0.0, 0.0, 1.0),
                ])

    reparent_dict = {
            'hand_l' : 'lowerarm_l',
            'hand_r' : 'lowerarm_r',
            'foot_l' : 'calf_l',
            'foot_r' : 'calf_r',
            'thumb_01_l' : 'hand_l',
            'thumb_01_r' : 'hand_r',
            }

    # Reparent Forward limb bones
    for child_name, parent_name in reparent_dict.items():
        child = edit_bones.get(child_name)
        parent = edit_bones.get(parent_name)
        if child and parent:
            child.parent = parent

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

    # Back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Delete ue4_rig
    bpy.data.armatures.remove(source_arm, True)

# Fuction for Unparent ik related bones (currrently for rigify only)
def unparent_ik_related_bones(use_humanoid_name, rigify_obj, export_rig_obj):
    scene = bpy.context.scene

    # Search for ik related bones
    unparent_bone_names = []
    for bone in rigify_obj.data.bones:
        # Logically if bone marked with fk suffix should have its ik counterpart bone
        if ((bone.name.endswith('_fk.L') or bone.name.endswith('_fk.R')) 
            # MCH bone is not count
            and not bone.name.startswith('MCH-') 
            # Root ik bone also doesn't count, indicated by 'parent' suffix in its parent bone
            and not (bone.parent.name.endswith('_parent.L') or (bone.parent.name.endswith('_parent.R'))) 
            ):
            bone_name = 'DEF-' + bone.name.replace('_fk', '')
            unparent_bone_names.append(bone_name)

    # Set to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    scene.objects.active = export_rig_obj

    # Set to edit mode
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = export_rig_obj.data.edit_bones

    # Get retarget dictionary
    retarget_dict = get_retarget_dict(rigify_obj)

    for bone in edit_bones:
        if use_humanoid_name:
            for key, value in retarget_dict.items():
                if value == bone.name and key in unparent_bone_names:
                    bone.parent = None
                    break
        elif bone.name in unparent_bone_names:
            bone.parent = None

    # Back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

def evaluate_and_get_source_data(scene, objects):

    rig_object = None
    mesh_objects = []
    failed_mesh_objects = []

    # If only select armature object
    if len(objects) == 1 and objects[0].type == 'ARMATURE':
        rig_object = objects[0]
        mesh_objects = [o for o in scene.objects if (
            o.type == 'MESH' and
            not o.ue4h_props.disable_export and
            any(mod for mod in o.modifiers if (
                    mod.type == 'ARMATURE' and 
                    mod.object == rig_object
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
            rig_object = armature_objs[0]

            # Evaluating mesh to be exported or not
            for obj in objects:
                if obj.ue4h_props.disable_export: continue
                if any([mod for mod in obj.modifiers if (
                    mod.type == 'ARMATURE' and mod.object == rig_object)]):
                    mesh_objects.append(obj)
                elif obj.type == 'MESH':
                    failed_mesh_objects.append(obj)

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
                    #mesh_objects.append(obj)

                    # Add armature object used to list
                    armature_mod = armature_mod[0]
                    if armature_mod.object not in armature_object_list:
                        armature_object_list.append(armature_mod.object)

                # If object didn't have armature modifier or didn't set armature object,
                # do not export
                else:
                    failed_mesh_objects.append(obj)
                
            # If no armature found
            if not any(armature_object_list):
                return "FAILED! No armature found! Make sure have properly set your armature modifier."

            # If more than one armature object found
            elif len(armature_object_list) > 1:
                return "FAILED! There are more than one armature object variation on selected objects"

            rig_object = armature_object_list[0]

            # Add other objects using same rig object
            for obj in scene.objects:
                if obj.ue4h_props.disable_export: continue
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE' and mod.object == rig_object:
                        mesh_objects.append(obj)
    
    # If not found any mesh to be export
    #if not(mesh_objects):
    #    return "FAILED! No objects valid to export! Make sure your armature modifiers are properly set."

    return rig_object, mesh_objects, failed_mesh_objects

# Check if using rigify by checking existance of MCH-WGT-hips
def check_use_rigify(rig):
    root_bone = rig.bones.get('MCH-WGT-hips')
    if not root_bone: return False
    return True

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

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select and obj.type == 'ARMATURE' and obj.animation_data and obj.animation_data.action

    def draw(self, context):
        layout = self.layout
        rig_obj = get_current_armature_object()
        action = rig_obj.animation_data.action
        props = action.ue4h_props
        #layout.prop(self, "global_scale")
        #layout.prop(self, "remove_unused_bones")
        #layout.prop(self, "use_humanoid_name")
        #layout.prop(self, "unparent_ik_bones")
        layout.label(action.name, icon='ACTION')
        #layout.label(text="Timeframe of the action:")
        layout.prop(props, "timeframe", text="Timeframe")
        #layout.prop(props, "hip_to_root")

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
        rig_props = rig_obj.data.ue4h_props

        # Check if using rigify by checking the widget of root bone
        use_rigify = check_use_rigify(rig_obj.data)
        #if not use_rigify:
        #    state.load(context)
        #    self.report({'ERROR'}, 'This addon only works with Blender 2.78 Rigify! (More support coming soon!)')
        #    return{'CANCELLED'}

        # Check action
        action = rig_obj.animation_data.action
        action_props = action.ue4h_props

        # Scale of the objects
        scale = ABS_SCALE * rig_props.global_scale

        if not action:
            self.report({'ERROR'}, "FAILED! Please activate an action you want to export.")
            return{'CANCELLED'}

        # Extract export rig from rigify
        export_rig_ob = extract_export_rig(context, rig_obj, scale, use_rigify)

        # Scale original rig
        rig_obj.scale *= scale

        # Set timeframe
        if action_props.timeframe != 'SCENE':
            scene.frame_start = action.frame_range[0]
            scene.frame_end = action.frame_range[1]
            if action_props.timeframe == 'ACTION_MINUS_ONE':
                scene.frame_end -= 1

        if use_rigify and rig_props.use_humanoid_name:
            # Retarget bone name
            convert_to_unreal_humanoid(rig_obj, export_rig_ob, scale)

            # Make humanoid constraint
            make_humanoid_constraint(context, rig_obj, export_rig_ob)

        else:
            # Make constraint
            make_constraint(context, rig_obj, export_rig_ob)

            # Manual bake action if want to edit root bone
            #if action_props.hip_to_root:
            #    move_root(scene, export_rig_ob)

        if use_rigify and rig_props.unparent_ik_bones:
            unparent_ik_related_bones(rig_props.use_humanoid_name, rig_obj, export_rig_ob)

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
                bake_anim_force_startend_keying=True,
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
    bl_label = "Export UE4 Skeletal mesh"
    bl_description = "Export rigify mesh as skeletal mesh FBX file"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        #objs = [obj for obj in context.selected_objects if (
        #    obj.proxy == None and # You can't export if object is linked
        #    (obj.type == 'MESH' or obj.type == 'ARMATURE') # Only mesh or armature can be exported
        #    )]
        #return any(objs)
        return get_current_armature_object()

    def draw(self, context):
        layout = self.layout
        rig_obj = get_current_armature_object()
        use_rigify = check_use_rigify(rig_obj.data)
        props = rig_obj.data.ue4h_props
        #layout.label('No specific options yet!')
        #layout.prop(self, "global_scale")
        #layout.prop(self, "remove_unused_bones")
        #layout.prop(self, "use_humanoid_name")
        layout.label(rig_obj.name + ' (Rigify : '+ str(use_rigify) + ')', icon='ARMATURE_DATA')
        c = layout.column()
        c.active = use_rigify
        c.prop(props, "use_humanoid_name")
        c.prop(props, "unparent_ik_bones")
        layout.prop(props, "global_scale")

    def execute(self, context):
        if not self.filepath:
            raise Exception("filepath not set")

        # Create save system to save current selection, mode, and active object
        state = SaveState(context)

        # Evaluate selected objects to export
        rig_object, mesh_objects, failed_mesh_objects = evaluate_and_get_source_data(context.scene, context.selected_objects)

        # If evaluate returns string it means error
        if not mesh_objects:
            state.load(context)
            self.report({'ERROR'}, "FAILED! No objects valid to export! Make sure your armature modifiers are properly set.")
            return{'CANCELLED'}

        # Scale of the objects
        rig_props = rig_object.data.ue4h_props
        scale = ABS_SCALE * rig_props.global_scale

        # Check if using rigify by checking the widget of root bone
        use_rigify = check_use_rigify(rig_object.data)
        #if not use_rigify:
        #    state.load(context)
        #    self.report({'ERROR'}, 'This addon only works with Blender 2.78 Rigify! (More support coming soon!)')
        #    return{'CANCELLED'}

        # Get export rig
        #if self.remove_unused_bones:
        #    export_rig_ob = extract_export_rig(context, rig_object, scale, mesh_objects)
        #else: export_rig_ob = extract_export_rig(context, rig_object, scale)
        export_rig_ob = extract_export_rig(context, rig_object, scale, use_rigify)

        # If returns string it means error
        #if type(export_rig_ob) is str:
        #    state.load(context)
        #    self.report({'ERROR'}, export_rig_ob)
        #    return{'CANCELLED'}

        # Get export mesh objects
        export_mesh_objs = extract_export_meshes(context, mesh_objects, export_rig_ob, scale)

        # Set to object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Select export objects
        export_rig_ob.select = True
        for obj in export_mesh_objs:
            obj.select = True

        # Retarget bone name and vertex groups (RIGIFY ONLY)
        if use_rigify:
            if rig_props.use_humanoid_name:
                convert_to_unreal_humanoid(rig_object, export_rig_ob, scale, export_mesh_objs)

            if rig_props.unparent_ik_bones:
                unparent_ik_related_bones(rig_props.use_humanoid_name, rig_object, export_rig_ob)

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
                bake_anim_force_startend_keying=True,
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
        if any(failed_mesh_objects):
            obj_names = ''
            for i, obj in enumerate(failed_mesh_objects):
                obj_names += obj.name
                if i != len(failed_mesh_objects) - 1:
                    obj_names += ', '
            
            self.report({'INFO'}, "INFO: Cannot export mesh [" + obj_names + "] because of reasons")

        #self.report({'INFO'}, "INFO: Export successful!")

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

        #print()

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

class ToggleUE4HelperOptions(bpy.types.Operator):
    bl_idname = "scene.toggle_ue4_helper_options"
    bl_label = "Toggle UE4 Helper Options"
    bl_description = "Toggle UE4 Helper Options"
    #bl_options = {'REGISTER', 'UNDO'}

    prop = StringProperty(default='show_rig_export_options')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        props = context.scene.ue4h_props

        if self.prop not in dir(props) or not self.prop.startswith('show_'):
            return {'CANCELLED'}

        cur_value = getattr(props, self.prop)
        setattr(props, self.prop, not cur_value)

        return {'FINISHED'}

class UE4HelperSkeletalPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "objectmode"
    bl_label = "UE4 Skeletal"
    bl_category = "UE4 Helper"

    def draw(self, context):
        scene = context.scene
        obj = context.object
        scene_props = context.scene.ue4h_props

        # Search for armature
        rig_obj = get_current_armature_object()

        c = self.layout.column(align=True)
        r = c.row(align=True)
        r.operator('export_mesh.rigify_fbx', text='Export Skeletal Mesh', icon='MOD_ARMATURE')
        if scene_props.show_rig_export_options: r.alert = True
        r.operator('scene.toggle_ue4_helper_options', text='', icon='SCRIPTWIN').prop = 'show_rig_export_options'

        if scene_props.show_rig_export_options:
            box = c.box()
            if not rig_obj:
                box.label("No rig selected!", icon="ARMATURE_DATA")
            else:
                props = rig_obj.data.ue4h_props
                col = box.column(align=True)
                #boxx = col.box()
                #coll = boxx.column(align=True)
                use_rigify = check_use_rigify(rig_obj.data)
                col.label(rig_obj.name + ' (Rigify : '+ str(use_rigify) + ')', icon='ARMATURE_DATA')
                #col.label('Active: ' + rig_obj.name)
                #col.label('Rigify: True')
                cc = col.column(align=True)
                cc.active = use_rigify
                cc.prop(props, 'use_humanoid_name', text='Use Humanoid bone names')
                cc.prop(props, 'unparent_ik_bones')
                col.prop(props, 'global_scale')
                col.separator()

        c.separator()

        r = c.row(align=True)
        #r.operator("export_anim.rigify_fbx", text="Export current action", icon='ACTION_TWEAK')
        r.operator("export_anim.rigify_fbx", text="Export current action", icon='ACTION')
        if scene_props.show_action_export_options: r.alert = True
        r.operator('scene.toggle_ue4_helper_options', text='', icon='SCRIPTWIN').prop = 'show_action_export_options'
        if scene_props.show_action_export_options:
            box = c.box()
            if not rig_obj:
                box.label("No rig selected!", icon="ACTION")
            else:
                if not rig_obj.animation_data or not rig_obj.animation_data.action:
                    box.label("No active action!", icon="ACTION")
                else:
                    action = rig_obj.animation_data.action
                    col = box.column(align=True)
                    col.label(action.name, icon='ACTION')
                    #col.label("Timeframe:")
                    #col.prop(action.ue4h_props, 'timeframe', text='')
                    col.prop(action.ue4h_props, 'timeframe', text='Timeframe')
                    #col.prop(action.ue4h_props, 'hip_to_root', text="Hip XY location to Root location")
        c.separator()

        #c.operator("export_anim.rigify_fbx", text="Export all actions", icon='ACTION')
        #c.separator()

class BONE_PT_ue4_helper(bpy.types.Panel):
    bl_label = "UE4 Helper Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    #bl_options = {'DEFAULT_OPEN'}

    def draw(self, context):
        bone = bpy.context.active_bone
        if not bone:
            self.layout.label('No active bone!')
            return
        arm = bpy.context.object.data
        bone = arm.bones.get(bone.name)
        props = bone.ue4h_props
        c = self.layout.column()
        c.active = not bone.use_deform
        c.prop(props, 'force_export')
        #self.layout.label('Nothing to see here!')

class OBJECT_PT_ue4_helper(bpy.types.Panel):
    bl_label = "UE4 Helper Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    #bl_options = {'DEFAULT_OPEN'}

    def draw(self, context):
        obj = bpy.context.object
        rig_obj = get_current_armature_object()
        #if not rig_obj:
        #    self.layout.label('No active rig object found!')
        #    return
        props = obj.ue4h_props
        c = self.layout.column()
        c.active = True if rig_obj else False
        #c.active = not bone.use_deform
        c.prop(props, 'disable_export')
        #self.layout.label('Nothing to see here!')

class UE4HelperNewObjectsPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "objectmode"
    bl_label = "Add New Objects"
    bl_category = "UE4 Helper"

    def draw(self, context):
        c = self.layout.column(align=True)
        c.operator("object.add_standard_ue4_tpp", text="Add UE4 TPP Mesh", icon='ARMATURE_DATA')

class ObjectUE4HelperProps(bpy.types.PropertyGroup):
    disable_export = BoolProperty(
            name="Disable Export Object",
            description = "Disable export object even if using exported armature in its modifier",
            default=False,
            )

class BoneUE4HelperProps(bpy.types.PropertyGroup):
    force_export = BoolProperty(
            name="Force Export Bone",
            description = "Force export bone even if not using deform option",
            default=False,
            )

class ArmatureUE4HelperProps(bpy.types.PropertyGroup):
    global_scale = FloatProperty(
            name="Scale",
            description = "Scale of objects multplied by 100 (Unreal default)",
            min=0.001, max=1000.0,
            default=1.0,
            )

    use_humanoid_name = BoolProperty(
            name="Use Unreal humanoid bone names",
            description="Use standard unreal humanoid bone name for easy retargeting.\n(Works best using Rigify)", 
            default=True,
            )

    unparent_ik_bones = BoolProperty(
            name="Unparent IK related bones",
            description="EXPERIMENTAL! Unparent hand and leg bones so it can be transformed freely.\n(Useful to do squash and stretch without error. Only works with Rigify rig)", 
            default=False,
            )

class ActionUE4HelperProps(bpy.types.PropertyGroup):
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

    #hip_to_root = BoolProperty(
    #        name="Convert Hip XY location to Root location",
    #        description="Useful if you want to use root motion on UE4", 
    #        default=False,
    #        )

class SceneUE4HelperProps(bpy.types.PropertyGroup):
    show_rig_export_options = BoolProperty(default=False)
    show_action_export_options = BoolProperty(default=False)

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Armature.ue4h_props = PointerProperty(type=ArmatureUE4HelperProps)
    bpy.types.Action.ue4h_props = PointerProperty(type=ActionUE4HelperProps)
    bpy.types.Scene.ue4h_props = PointerProperty(type=SceneUE4HelperProps)
    bpy.types.Bone.ue4h_props = PointerProperty(type=BoneUE4HelperProps)
    bpy.types.Object.ue4h_props = PointerProperty(type=ObjectUE4HelperProps)

def unregister():
    bpy.utils.unregister_module(__name__)

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
