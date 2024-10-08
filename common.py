import bpy, os, time
from mathutils import *

TEMP_SUFFIX = '__TEMP__'
COPY_SUFFIX = '.COPY'

def is_greater_than_280():
    if bpy.app.version >= (2, 80, 0):
        return True
    return False

def link_object(scene, obj):
    if is_greater_than_280():
        scene.collection.objects.link(obj)
    else: scene.objects.link(obj)

def select_get(obj):
    if is_greater_than_280():
        return obj.select_get()
    return obj.select

def select_set(obj, val):
    if is_greater_than_280():
        obj.select_set(val)
    else: obj.select = val

def set_active(obj):
    if is_greater_than_280():
        bpy.context.view_layer.objects.active = obj
    else: bpy.context.scene.objects.active = obj

def cursor_location_get():
    if is_greater_than_280():
        return bpy.context.scene.cursor.location
    return bpy.context.scene.cursor_location

def get_instance_collection(obj):
    if is_greater_than_280():
        return obj.instance_collection
    return obj.dupli_group

def get_set_collection(collection_name, parent_collection=None):
    if collection_name in bpy.data.collections: # Does the collection already exist?
        return bpy.data.collections[collection_name]
    else:
        new_collection = bpy.data.collections.new(collection_name)
        if parent_collection: parent_collection.children.link(new_collection) # Add the new collection under a parent
        return new_collection

class SaveState():
    def __init__(self, context):
        self.active = context.object
        self.select = context.selected_objects
        self.mode = context.mode
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end

        if context.object.animation_data:
            self.action = context.object.animation_data.action
        else: self.action = None

    def load(self, context):
        scene = context.scene
        for obj in bpy.data.objects:
            if obj in self.select:
                select_set(obj, True)
            else: 
                select_set(obj, False)
        set_active(self.active)
        bpy.ops.object.mode_set(mode=self.mode)
        scene.frame_start = self.frame_start
        scene.frame_end = self.frame_end

        if context.object.animation_data:
            context.object.animation_data.action = self.action

def get_addon_filepath():
    return os.path.dirname(bpy.path.abspath(__file__)) + os.sep

def get_current_armature_object():
    obj = bpy.context.object
    if not obj: return None

    if obj.type == 'ARMATURE':
        return obj

    arm_obj = None

    # Search in modifiers
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE' and mod.object:
            arm_obj = mod.object
            break

    return arm_obj

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
                # print(v.index)
                # print(vg.weight)
                obj.vertex_groups[vg1_index].add([v.index],vg.weight,'ADD')
                
    vg2 = obj.vertex_groups.get(vg2_name)
    obj.vertex_groups.remove(vg2)

def make_root_constraint(context, rigify_object, export_rig_object):

    ori_mode = context.object.mode
    scene = context.scene

    # Goto object mode, deselect all and select the rig
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    set_active(export_rig_object)
    select_set(export_rig_object, True)

    # Make rigify at rest pose
    rigify_object.data.pose_position = 'REST'

    # Object constraint
    bpy.ops.object.constraint_add(type='CHILD_OF')
    export_rig_object.constraints['Child Of'].target = rigify_object
    export_rig_object.constraints['Child Of'].subtarget = 'root'

    # Context copy for inverse child of constraint
    context_copy = bpy.context.copy()
    context_copy['constraint'] = export_rig_object.constraints['Child Of']
    bpy.ops.constraint.childof_set_inverse(constraint="Child Of", owner='OBJECT')

    # Revert rigify pose
    rigify_object.data.pose_position = 'POSE'

    # Back to original mode
    if context.object.mode != ori_mode:
        bpy.ops.object.mode_set(mode=ori_mode)

def make_constraint(context, rig_object, export_rig_object):

    ori_mode = context.object.mode

    # Deselect all and select the rig
    if context.object.mode == 'OBJECT':
        bpy.ops.object.select_all(action='DESELECT')

    set_active(export_rig_object)
    select_set(export_rig_object, True)

    # Go to armature pose mode
    bpy.ops.object.mode_set(mode='POSE')

    pose_bones = export_rig_object.pose.bones
    bones = export_rig_object.data.bones

    # Set constraint
    for bone in bones:
        #pose_bones.active = bone
        bones.active = bone
        bone_name = bone.name
        target_bone_name = bone.name

        # Dealing with bone with copy suffix
        if bone_name.endswith(COPY_SUFFIX):
            target_bone_name = target_bone_name.replace(COPY_SUFFIX, '')
        
        # bpy.ops.pose.constraint_add(type="COPY_LOCATION")
        # bpy.ops.pose.constraint_add(type="COPY_ROTATION")
        # bpy.ops.pose.constraint_add(type="COPY_SCALE")
        pose_bones[bone_name].constraints.new(type="COPY_LOCATION")
        pose_bones[bone_name].constraints.new(type="COPY_ROTATION")
        pose_bones[bone_name].constraints.new(type="COPY_SCALE")



        # Add constraint target based by rig source object
        pose_bones[bone_name].constraints["Copy Location"].target = rig_object
        pose_bones[bone_name].constraints["Copy Location"].subtarget = target_bone_name
        pose_bones[bone_name].constraints["Copy Rotation"].target = rig_object
        pose_bones[bone_name].constraints["Copy Rotation"].subtarget = target_bone_name
        pose_bones[bone_name].constraints["Copy Scale"].target = rig_object
        pose_bones[bone_name].constraints["Copy Scale"].subtarget = target_bone_name
        pose_bones[bone_name].constraints["Copy Scale"].target_space = 'LOCAL_WITH_PARENT'
        pose_bones[bone_name].constraints["Copy Scale"].owner_space = 'WORLD'
    
    # Back to original mode
    if context.object.mode != ori_mode:
        bpy.ops.object.mode_set(mode=ori_mode)

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
def extract_export_rig(context, source_object, scale, use_rigify=False, unparent_all=False):

    scene = context.scene

    # Check if this object is a proxy or not
    #if source_object.proxy:
    #    source_object = source_object.proxy

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
    link_object(scene, export_rig_ob)

    # Show x-ray for debugging
    if is_greater_than_280():
        export_rig_ob.show_in_front = True
    else: export_rig_ob.show_x_ray = True

    # Deselect all and select the export rig
    bpy.ops.object.select_all(action='DESELECT')
    set_active(export_rig_ob)
    select_set(export_rig_ob, True)
    select_set(source_object, True)

    # Go to armature edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Edit bones
    edit_bones = export_rig.edit_bones
    source_edit_bones = source_object.data.edit_bones
    
    # Rearrange parent (RIGIFY ONLY)
    if use_rigify:
        for bone in edit_bones:
            if bone.parent and bone.parent.name.startswith('ORG-'):
                parent_name = bone.parent.name.replace('ORG-', 'DEF-')
                parent = edit_bones.get(parent_name)
                bone.parent = parent
                print(bone.name, bone.parent.name)

    # Delete other than deform bones
    for bone in edit_bones:
        b = export_rig.bones.get(bone.name)
        #if 'DEF-' not in bone.name and bone.name != 'root':
        #if not bone.use_deform and bone.name != 'root':
        if not bone.use_deform and not b.ue4h_props.force_export:
            edit_bones.remove(bone)
    
    if unparent_all:
        for bone in edit_bones:
            bname = bone.name
            if (bname in source_edit_bones):
                if (source_edit_bones[bname].gr_props.keep_parent == False):
                    bone.parent = None

    export_rig_ob.data.collections_all['DEF'].is_solo = True

    # Change active bone layers to layer 0
    # for bone in edit_bones:
    #     for i, layer in enumerate(bone.layers):
    #         if i == 0: bone.layers[i] = True
    #         else: bone.layers[i] = False

    # Cleaning up unused bones based usage of meshes
    # Usually for deleting hand palm bones and some others
    #if any(meshes_to_evaluate):
    #    vg_names = get_vertex_group_names(meshes_to_evaluate)
    #    for bone in edit_bones:
    #        if bone.name not in vg_names and bone.name != 'root':
    #            edit_bones.remove(bone)

    # Change active armature layers to layer 0
    # for i, layer in enumerate(export_rig.layers):
    #     if i == 0: export_rig.layers[i] = True
    #     else: export_rig.layers[i] = False

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
    #if use_rigify:
    #    bpy.ops.wm.properties_remove(data_path = 'active_object.data', property = 'rig_id')

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

def extract_export_meshes(context, mesh_objects, export_rig_ob, scale, only_export_baked_vcols=False):
    
    scene = context.scene

    # Set to object mode
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect for safety purpose
    bpy.ops.object.select_all(action='DESELECT')

    # Deals with dupli_group
    #if dupli_group:
    #    pass

    # Duplicate Meshes
    export_objs = []
    for obj in mesh_objects:

        #new_obj = scene.objects.active
        obj_name = obj.name
        obj.name += TEMP_SUFFIX

        new_obj = obj.copy()
        new_obj.data = new_obj.data.copy()
        new_obj.name = obj_name
        link_object(scene, new_obj)

        # New objects scaling
        #if new_obj.parent != rig_object:
        #    new_obj.scale *= scale

        # Select this mesh
        select_set(new_obj, True)
        set_active(new_obj)

        # Clear parent
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # Scale mesh
        new_obj.scale *= scale
        new_obj.location *= scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # Parent to export rig
        new_obj.parent = export_rig_ob

        # Remove vcols
        if only_export_baked_vcols and new_obj.type == 'MESH':
            for vcol in reversed(new_obj.data.color_attributes):
                if not vcol.name.startswith('Baked '):
                    new_obj.data.color_attributes.remove(vcol)

        # Populate exported meshes list
        export_objs.append(new_obj)

        # Check if there's shape keys
        if new_obj.data.shape_keys:
            shapes_count = len(new_obj.data.shape_keys.key_blocks)

            # Apply modifiers other than armatures so shape keys will be exported
            if shapes_count > 0:
                apply_modifiers_with_shape_keys(new_obj, 
                        [m.name for m in new_obj.modifiers if m.type != 'ARMATURE'], True)

        # Change armature object to exported rig
        mod_armature = [mod for mod in new_obj.modifiers if mod.type == 'ARMATURE'][0]
        mod_armature.object = export_rig_ob

        select_set(obj, False)
        select_set(new_obj, False)

    # Apply transform to exported rig and mesh
    #bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    return export_objs 

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

    set_active(export_rig_obj)

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

def evaluate_and_get_source_data(scene, objects, use_export_meshes=True):

    rig_object = None
    mesh_objects = []
    failed_mesh_objects = []
    error_messages = ''
    #dupli_group = None

    # If only select armature object
    if len(objects) == 1 and objects[0].type == 'ARMATURE':
        rig_object = objects[0]

    # If rig object still not found
    if not rig_object:

        # Selected armatures
        armature_objs = [o for o in objects if o.type == 'ARMATURE']

        # If select more than one armatures
        if len(armature_objs) > 1:
            error_messages = "FAILED! You cannot export more than one armatures"
        
        # If select at least one armature
        elif len(armature_objs) == 1:
            rig_object = armature_objs[0]

        # If not select any armatures, search for possible armature
        elif len(armature_objs) == 0:

            # List to check of possibility armature modifier using different object
            armature_object_list = []

            for obj in objects:
                armature_mod = [mod for mod in obj.modifiers if (
                    mod.type == 'ARMATURE' and mod.object)]

                # If object has armature modifier
                if any(armature_mod):
                    # Add armature object used to list
                    armature_mod = armature_mod[0]
                    if armature_mod.object not in armature_object_list:
                        armature_object_list.append(armature_mod.object)
                
            # If no armature found
            if not any(armature_object_list):
                error_messages = "FAILED! No armature found! Make sure have properly set your armature modifier."

            # If more than one armature object found
            elif len(armature_object_list) > 1:
                error_messages = "FAILED! There are more than one armature object variation on selected objects"

            else:
                rig_object = armature_object_list[0]

    ## If rig object still not found, check is rig is linked
    #if not rig_object:

    #    # Check if selected object has dupli group (linked object to other file)
    #    dupli_group = [o for o in objects if o.type == 'EMPTY' and o.dupli_group]
    #    if dupli_group: dupli_group = dupli_group[0]

    #    if dupli_group:

    #        # If dupli group found, search inside dupli_group
    #        for o in dupli_group.objects:
    #            if o.type == 'ARMATURE':
    #                # Search for actual object with linked armature
    #                rig_object = [ob for ob in scene.objects if ob.data == o.data]
    #                if rig_object: rig_object = rig_object[0]

    if use_export_meshes:

        # Get mesh objects that using rig object
        if rig_object:
            for o in scene.objects:
                if o.ue4h_props.disable_export: continue

                # Search for modifier using rig object
                if o.type == 'MESH':
                    for mod in o.modifiers:
                        if mod.type == 'ARMATURE' and mod.object == rig_object:
                            mesh_objects.append(o)
                            break

                # If object is linked pass dupli_group
                icol = get_instance_collection(o)
                if icol:
                    for ob in icol.objects:
                        #print(ob)
                        for mod in ob.modifiers:
                            if mod.type == 'ARMATURE' and mod.object and mod.object.data == rig_object.data:
                                mesh_objects.append(ob)
                        #if ob.data == rig_object.data:
                        #    dupli_group = o.dupli_group
                        #    break

        #if dupli_group:
        #    for o in dupli_group.objects:
        #        pass

        # Check failed meshes
        for o in objects:
            if o.type == 'MESH' and o not in mesh_objects:
                failed_mesh_objects.append(o)
        
        # If not found any mesh to be export
        if not(mesh_objects): # and not dupli_group:
            error_messages = "FAILED! No objects valid to export! Make sure your armature modifiers are properly set."

    return rig_object, mesh_objects, failed_mesh_objects, error_messages

# Check if using rigify by checking existance of MCH-WGT-hips
def check_use_rigify(rig):
    root_bone = rig.bones.get('MCH-WGT-hips')
    if not root_bone: return False
    return True

def move_root(scene, obj):

    # Deselect all and select the rig
    bpy.ops.object.select_all(action='DESELECT')
    set_active(obj)
    select_set(obj, True)

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
    link_object(scene, temp_ob)
    select_set(temp_ob, False)

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
    set_active(temp_ob)
    select_set(obj, False)
    select_set(temp_ob, True)

    # Delete temp object
    bpy.ops.object.delete()

    # Select back original object
    set_active(obj)
    select_set(obj, True)

def reset_pose_bone_props(obj, scene, action):
    scene_props = scene.rigify_export_props

    arm_l_follow_found = False
    arm_r_follow_found = False
    leg_l_follow_found = False
    leg_r_follow_found = False

    hand_l_ik_found = False
    hand_r_ik_found = False
    foot_l_ik_found = False
    foot_r_ik_found = False

    for fcurve in action.fcurves:

        if fcurve.data_path == 'pose.bones["upper_arm_parent.L"]["FK_limb_follow"]':
            arm_l_follow_found = True
        elif fcurve.data_path == 'pose.bones["upper_arm_parent.R"]["FK_limb_follow"]':
            arm_r_follow_found = True

        elif fcurve.data_path == 'pose.bones["thigh_parent.L"]["FK_limb_follow"]':
            leg_l_follow_found = True
        elif fcurve.data_path == 'pose.bones["thigh_parent.R"]["FK_limb_follow"]':
            leg_r_follow_found = True

        elif fcurve.data_path == 'pose.bones["upper_arm_parent.L"]["IK_FK"]':
            hand_l_ik_found = True
        elif fcurve.data_path == 'pose.bones["upper_arm_parent.R"]["IK_FK"]':
            hand_r_ik_found = True

        elif fcurve.data_path == 'pose.bones["thigh_parent.L"]["IK_FK"]':
            foot_l_ik_found = True
        elif fcurve.data_path == 'pose.bones["thigh_parent.R"]["IK_FK"]':
            foot_r_ik_found = True

    if not arm_l_follow_found:
        try: obj.pose.bones["upper_arm_parent.L"]["FK_limb_follow"] = 1.0 if scene_props.default_arm_follow else 0.0
        except Exception as e: print(e)

    if not arm_r_follow_found:
        try: obj.pose.bones["upper_arm_parent.R"]["FK_limb_follow"] = 1.0 if scene_props.default_arm_follow else 0.0
        except Exception as e: print(e)

    if not leg_l_follow_found:
        try: obj.pose.bones["thigh_parent.L"]["FK_limb_follow"] = 1.0 if scene_props.default_arm_follow else 0.0
        except Exception as e: print(e)

    if not leg_r_follow_found:
        try: obj.pose.bones["thigh_parent.R"]["FK_limb_follow"] = 1.0 if scene_props.default_arm_follow else 0.0
        except Exception as e: print(e)

    if not hand_l_ik_found:
        try: obj.pose.bones["upper_arm_parent.L"]["IK_FK"] = 0.0 if scene_props.default_hand_ik else 1.0
        except Exception as e: print(e)

    if not hand_r_ik_found:
        try: obj.pose.bones["upper_arm_parent.R"]["IK_FK"] = 0.0 if scene_props.default_hand_ik else 1.0
        except Exception as e: print(e)

    if not foot_l_ik_found:
        try: obj.pose.bones["thigh_parent.L"]["IK_FK"] = 0.0 if scene_props.default_foot_ik else 1.0
        except Exception as e: print(e)

    if not foot_r_ik_found:
        try: obj.pose.bones["thigh_parent.R"]["IK_FK"] = 0.0 if scene_props.default_foot_ik else 1.0
        except Exception as e: print(e)

def reset_pose_bones(obj):
    for pb in obj.pose.bones:

        # Set the rotation to 0
        if not pb.lock_rotation_w:
            pb.rotation_quaternion[0] = 1.0
        for i in range(3):
            if not pb.lock_rotation[i]:
                pb.rotation_quaternion[i+1] = 0.0
                pb.rotation_euler[i] = 0.0

        # Set the scale to 1
        for i in range(3):
            if not pb.lock_scale[i]:
                pb.scale[i] = 1.0

        # Set the location at rest (edit) pose bone position
        for i in range(3):
            if not pb.lock_location[i]:
                pb.location[i] = 0.0

def equal_float(value0, value1, tolerance):
    return value0 >= value1 - tolerance and value0 <= value1 + tolerance 

def remove_non_transformed_keyframes(action, ignore_object_transform=True, ignore_root=True, tolerance=0.0):

    msgs = []

    for fcurve in action.fcurves:
        #print(fcurve.data_path + " channel " + str(fcurve.array_index))
        transformed_key_found = False

        if ignore_object_transform:
            if fcurve.data_path in {'location', 'rotation_quaternion', 'rotation_euler', 'scale'}:
                continue

        if ignore_root:
            if fcurve.data_path.startswith('pose.bones["root"]'):
                continue

        for keyframe in fcurve.keyframe_points:
            #print(keyframe.co)

            if fcurve.data_path.endswith('location'):
                #if keyframe.co[1] != 0.0:
                if not equal_float(keyframe.co[1], 0.0, tolerance):
                    transformed_key_found = True
                    break
            elif fcurve.data_path.endswith('rotation_quaternion'):
                if fcurve.array_index == 0:
                    #if keyframe.co[1] != 1.0:
                    if not equal_float(keyframe.co[1], 1.0, tolerance):
                        transformed_key_found = True
                        break
                else:
                    #if keyframe.co[1] != 0.0:
                    if not equal_float(keyframe.co[1], 0.0, tolerance):
                        transformed_key_found = True
                        break
            elif fcurve.data_path.endswith('rotation_euler'):
                #if keyframe.co[1] != 0.0:
                if not equal_float(keyframe.co[1], 0.0, tolerance):
                    transformed_key_found = True
                    break
            elif fcurve.data_path.endswith('scale'):
                #if keyframe.co[1] != 1.0:
                if not equal_float(keyframe.co[1], 1.0, tolerance):
                    transformed_key_found = True
                    break

        if not transformed_key_found:
            msgs.append(action.name + ' ' + fcurve.data_path + ' is removed!')
            action.fcurves.remove(fcurve)

    return msgs

def apply_modifiers_with_shape_keys(obj, selectedModifiers, disable_armatures=True):

    list_properties = []
    properties = ["interpolation", "mute", "name", "relative_key", "slider_max", "slider_min", "value", "vertex_group"]
    shapesCount = 0
    vertCount = -1
    startTime = time.time()

    view_layer = bpy.context.view_layer
    scene = bpy.context.scene

    disabled_armature_modifiers = []
    if disable_armatures:
        for modifier in obj.modifiers:
            if modifier.name not in selectedModifiers and modifier.type == 'ARMATURE' and modifier.show_viewport == True:
                disabled_armature_modifiers.append(modifier)
                modifier.show_viewport = False
    
    if obj.data.shape_keys:
        shapesCount = len(obj.data.shape_keys.key_blocks)

    ori_active = view_layer.objects.active
    view_layer.objects.active = obj
    
    if(shapesCount == 0):
        for modifierName in selectedModifiers:
            try: bpy.ops.object.modifier_apply(modifier=modifierName)
            except Exception as e: print(e)
        if disable_armatures:
            for modifier in disabled_armature_modifiers:
                modifier.show_viewport = True
        view_layer.objects.active = ori_active
        return (True, None)

    # Remember original selected objects
    ori_selected_objs = [o for o in view_layer.objects if o.select_get()]
    
    # We want to preserve original object, so all shapes will be joined to it.
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    originalIndex = obj.active_shape_key_index
    
    # Copy object which will holds all shape keys.
    copyObject = obj.copy()
    scene.collection.objects.link(copyObject)
    copyObject.data = copyObject.data.copy()
    copyObject.select_set(False)
    
    # Return selection to original object.
    view_layer.objects.active = obj
    obj.select_set(True)
    
    # Save key shape properties
    for i in range(0, shapesCount):
        key_b = obj.data.shape_keys.key_blocks[i]
        print (obj.data.shape_keys.key_blocks[i].name, key_b.name)
        properties_object = {p:None for p in properties}
        properties_object["name"] = key_b.name
        properties_object["mute"] = key_b.mute
        properties_object["interpolation"] = key_b.interpolation
        properties_object["relative_key"] = key_b.relative_key.name
        properties_object["slider_max"] = key_b.slider_max
        properties_object["slider_min"] = key_b.slider_min
        properties_object["value"] = key_b.value
        properties_object["vertex_group"] = key_b.vertex_group
        list_properties.append(properties_object)

    # Save animation data
    ori_fcurves = []
    ori_action_name = ''
    if obj.data.shape_keys.animation_data and obj.data.shape_keys.animation_data.action:
        ori_action_name = obj.data.shape_keys.animation_data.action.name
        for fc in obj.data.shape_keys.animation_data.action.fcurves:
            fc_dic = {}

            for prop in dir(fc):
                copy_props_to_dict(fc, fc_dic) #, True)

            ori_fcurves.append(fc_dic)

    # Handle base shape in original object
    print("apply_modifiers_with_shape_keys: Applying base shape key")
    bpy.ops.object.shape_key_remove(all=True)
    for modifierName in selectedModifiers:
        try: bpy.ops.object.modifier_apply(modifier=modifierName)
        except Exception as e: print(e)
    vertCount = len(obj.data.vertices)
    bpy.ops.object.shape_key_add(from_mix=False)
    obj.select_set(False)

    # Handle other shape-keys: copy object, get right shape-key, apply modifiers and merge with original object.
    # We handle one object at time here.
    for i in range(1, shapesCount):
        currTime = time.time()
        elapsedTime = currTime - startTime

        print("apply_modifiers_with_shape_keys: Applying shape key %d/%d ('%s', %0.2f seconds since start)" % (i+1, shapesCount, list_properties[i]["name"], elapsedTime))

        # Select copy object.
        copyObject.select_set(True)
        
        # Copy temp object.
        tmpObject = copyObject.copy()
        scene.collection.objects.link(tmpObject)
        tmpObject.data = tmpObject.data.copy()
        view_layer.objects.active = tmpObject

        bpy.ops.object.shape_key_remove(all=True)
        copyObject.active_shape_key_index = i
        
        # Get right shape-key.
        bpy.ops.object.shape_key_transfer()
        tmpObject.active_shape_key_index = 0
        bpy.ops.object.shape_key_remove()
        bpy.ops.object.shape_key_remove(all=True)
        
        # Time to apply modifiers.
        for modifierName in selectedModifiers:
            try: bpy.ops.object.modifier_apply(modifier=modifierName)
            except Exception as e: print(e)
        
        # Verify number of vertices.
        if vertCount != len(tmpObject.data.vertices):
            errorInfo = ("Shape keys ended up with different number of vertices!\n"
                         "All shape keys needs to have the same number of vertices after modifier is applied.\n"
                         "Otherwise joining such shape keys will fail!")
            return (False, errorInfo)
    
        # Join with original object
        copyObject.select_set(False)
        view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.join_shapes()
        obj.select_set(False)
        
        # Remove tmpObject
        bpy.data.objects.remove(tmpObject, do_unlink=True)
    
    # Restore shape key properties like name, mute etc.
    view_layer.objects.active = obj
    for i in range(0, shapesCount):
        key_b = view_layer.objects.active.data.shape_keys.key_blocks[i]
        key_b.name = list_properties[i]["name"]
        key_b.interpolation = list_properties[i]["interpolation"]
        key_b.mute = list_properties[i]["mute"]
        key_b.slider_max = list_properties[i]["slider_max"]
        key_b.slider_min = list_properties[i]["slider_min"]
        key_b.value = list_properties[i]["value"]
        key_b.vertex_group = list_properties[i]["vertex_group"]
        rel_key = list_properties[i]["relative_key"]
    
        for j in range(0, shapesCount):
            key_brel = view_layer.objects.active.data.shape_keys.key_blocks[j]
            if rel_key == key_brel.name:
                key_b.relative_key = key_brel
                break
    
    # Remove copyObject.
    bpy.data.objects.remove(copyObject, do_unlink=True)
    
    # Select original object.
    view_layer.objects.active = obj
    view_layer.objects.active.select_set(True)
    
    if disable_armatures:
        for modifier in disabled_armature_modifiers:
            modifier.show_viewport = True

    obj.active_shape_key_index = originalIndex

    # Recover animation data
    if any(ori_fcurves):

        obj.data.shape_keys.animation_data_create()
        obj.data.shape_keys.animation_data.action = bpy.data.actions.new(name=ori_action_name)

        for ofc in ori_fcurves:
            fcurve = obj.data.shape_keys.animation_data.action.fcurves.new(
                data_path=ofc['data_path'], #index=2
            )

            for key, val in ofc.items():
                if key in {'data_path', 'keyframe_points'}: continue
                try: setattr(fcurve, key, val)
                except Exception as e: pass

            for kp in ofc['keyframe_points']:
                k = fcurve.keyframe_points.insert(
                frame=kp['co'][0],
                value=kp['co'][1]
                )

                for key, val in kp.items():
                    try: setattr(k, key, val)
                    except Exception as e: pass

            for mod in ofc['modifiers']:
                m = fcurve.modifiers.new(type=mod['type'])
                for key, val in mod.items():
                    try: setattr(m, key, val)
                    except Exception as e: pass

    # Recover selected objects
    bpy.ops.object.select_all(action='DESELECT')
    for o in ori_selected_objs:
        o.select_set(True)
    view_layer.objects.active = ori_active
    
    return (True, None)

