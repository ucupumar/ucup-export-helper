import bpy, os

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
    bpy.ops.constraint.childof_set_inverse(context_copy, constraint="Child Of", owner='OBJECT')

    # Revert rigify pose
    rigify_object.data.pose_position = 'POSE'

def make_constraint(context, rig_object, export_rig_object):

    # Deselect all and select the rig
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
    link_object(scene, export_rig_ob)

    # Show x-ray for debugging
    if is_greater_than_280():
        export_rig_ob.show_in_front = True
    else: export_rig_ob.show_x_ray = True

    # Deselect all and select the export rig
    bpy.ops.object.select_all(action='DESELECT')
    set_active(export_rig_ob)
    select_set(export_rig_ob, True)

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

def extract_export_meshes(context, mesh_objects, export_rig_ob, scale):
    
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
        #print(obj.name)
        #select_set(obj, True)
        #scene.objects.active = obj

        #bpy.ops.object.duplicate()

        #new_obj = scene.objects.active

        new_obj = obj.copy()
        new_obj.data = new_obj.data.copy()
        link_object(scene, new_obj)

        # New objects scaling
        #if new_obj.parent != rig_object:
        #    print('aaaaaaaa')
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

        # Populate exported meshes list
        export_objs.append(new_obj)

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

def evaluate_and_get_source_data(scene, objects):

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
                    print(ob)
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

