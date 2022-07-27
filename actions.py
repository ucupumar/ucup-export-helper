import bpy
from bpy.props import *
from mathutils import *
from .common import *

class YNewAction(bpy.types.Operator):
    bl_idname = "armature.y_new_action"
    bl_label = "New Action"
    bl_description = "New action"
    bl_options = {'REGISTER', 'UNDO'}

    action_name : StringProperty(
            name = 'Action Name',
            description = 'New action name',
            default = 'Action'
            )

    enable_fake_user : BoolProperty(
            name = 'Enable Fake User',
            description = "Enable fake user so animation don't dissapear after saving",
            default = True
            )

    reset_pose : BoolProperty(
            name = 'Reset Pose',
            description = 'Reset pose',
            default = True
            )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'action_name')
        self.layout.prop(self, 'enable_fake_user')
        self.layout.prop(self, 'reset_pose')

    @classmethod
    def poll(cls, context):
        obj = get_current_armature_object()
        return obj

    def execute(self, context):
        obj = get_current_armature_object()

        # Make sure animation data is exists
        if not obj.animation_data:
            obj.animation_data_create()

        action = bpy.data.actions.new(self.action_name)

        if self.reset_pose:
            obj.animation_data.action = None
            reset_pose_bones(obj)

        obj.animation_data.action = action

        if self.enable_fake_user:
            action.use_fake_user = True

        return {'FINISHED'}

class YRemoveAction(bpy.types.Operator):
    bl_idname = "armature.y_remove_action"
    bl_label = "Remove Action"
    bl_description = "Remove action"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = get_current_armature_object()
        return obj and obj.animation_data

    def execute(self, context):

        obj = get_current_armature_object()
        wm_props = context.window_manager.rigify_export_props

        try: action = bpy.data.actions[wm_props.active_action]
        except:
            self.report({'ERROR'}, "No action selected!")
            return {'CANCELLED'}

        bpy.data.actions.remove(action)

        wm_props.active_action = min(wm_props.active_action, len(bpy.data.actions)-1)

        return {'FINISHED'}

class YToggleDeselectAction(bpy.types.Operator):
    bl_idname = "armature.y_toggle_deselect_action"
    bl_label = "Toggle Deselect Action"
    bl_description = "Toggle Deselect action"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = get_current_armature_object()
        return obj and obj.animation_data

    def execute(self, context):
        obj = get_current_armature_object()
        wm_props = context.window_manager.rigify_export_props

        active_action = None
        list_action = None

        if obj.animation_data:
            active_action = obj.animation_data.action

        try: list_action = bpy.data.actions[wm_props.active_action]
        except: pass

        if active_action == list_action:

            obj.animation_data.action = None

            reset_pose_bones(obj)

        else:
            obj.animation_data.action = list_action

        return {'FINISHED'}

class YRemoveNonTransformativeFrames(bpy.types.Operator):
    bl_idname = "armature.y_remove_non_transformative_frames"
    bl_label = "Remove Non Transformative Frames"
    bl_description = "Remove non transformative frames"
    bl_options = {'REGISTER', 'UNDO'}

    all_actions : BoolProperty(
            name = 'All Actions',
            description = 'Remove untransformative frames on all actions rather than only on active action',
            default = False
            )

    remove_nlas : BoolProperty(
            name = 'Remove NLA Tracks',
            description = 'Remove all NLA tracks to avoid mixed animations',
            default = False
            )

    ignore_root : BoolProperty(
            name = 'Do Not Remove Root Transformations',
            description = 'Do not remove root transformations',
            default = True
            )

    ignore_object_transform : BoolProperty(
            name = 'Do Not Remove Object Transformations',
            description = 'Do not remove object transformations',
            default = True
            )

    @classmethod
    def poll(cls, context):
        return get_current_armature_object()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'all_actions')
        self.layout.prop(self, 'remove_nlas')
        self.layout.prop(self, 'ignore_root')
        self.layout.prop(self, 'ignore_object_transform')

    def execute(self, context):

        obj = get_current_armature_object()
        wm_props = context.window_manager.rigify_export_props

        if self.all_actions:
            actions = bpy.data.actions
        else:
            # Get action
            try: actions = [bpy.data.actions[wm_props.active_action]]
            except:
                self.report({'ERROR'}, "No action selected!")
                return {'CANCELLED'}

        for action in actions:

            msgs = remove_non_transformed_keyframes(action, self.ignore_object_transform, self.ignore_root)

            for msg in msgs:
                self.report({'INFO'}, msg)

        # Remove NLA tracks
        if self.remove_nlas:
            for track in reversed(obj.animation_data.nla_tracks):
                obj.animation_data.nla_tracks.remove(track)

        #print(transformed_key_found)

        return {'FINISHED'}

class YToggleActionSettings(bpy.types.Operator):
    bl_idname = "scene.y_toggle_action_settings"
    bl_label = "Toggle Action Settings"
    bl_description = "Toggle action settings"
    #bl_options = {'REGISTER', 'UNDO'}

    prop : StringProperty(default='show_action_settings')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        props = context.scene.rigify_export_props

        if self.prop not in dir(props) or not self.prop.startswith('show_'):
            return {'CANCELLED'}

        cur_value = getattr(props, self.prop)
        setattr(props, self.prop, not cur_value)

        return {'FINISHED'}

class YToggleActionGlobalSettings(bpy.types.Operator):
    bl_idname = "scene.y_toggle_action_global_settings"
    bl_label = "Toggle Action List Global Settings"
    bl_description = "Toggle action list global settings"
    #bl_options = {'REGISTER', 'UNDO'}

    prop : StringProperty(default='show_global_settings')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        props = context.scene.rigify_export_props

        if self.prop not in dir(props) or not self.prop.startswith('show_'):
            return {'CANCELLED'}

        cur_value = getattr(props, self.prop)
        setattr(props, self.prop, not cur_value)

        return {'FINISHED'}

def draw_action_manager(self, context):
    obj = get_current_armature_object()

    scene_props = context.scene.rigify_export_props
    props = context.window_manager.rigify_export_props

    listrow = self.layout.row()

    col = listrow.column()
    
    action = None

    # Check active action
    if obj.animation_data:
        action = obj.animation_data.action
        if action and (
                props.active_action >= len(bpy.data.actions) or
                action != bpy.data.actions[props.active_action]
                ):
            index = [i for i,a in enumerate(bpy.data.actions) if a == action][0]
            props.active_action = index

    col.template_list("ACTION_UL_y_action_lists", "", bpy.data,
            "actions", props, "active_action", rows=3, maxrows=5)  

    col = listrow.column(align=True)
    col.operator('armature.y_new_action', text='', icon='ADD')
    col.operator('armature.y_remove_action', text='', icon='REMOVE')
    col.menu("ACTION_MT_y_action_list_special_menu", text='', icon='DOWNARROW_HLT')
    col.operator('armature.y_toggle_deselect_action', text='', icon='OUTLINER_OB_ARMATURE')

    col = self.layout.column()

    #if action:
    #col.operator('armature.y_toggle_deselect_action', icon='ACTION')

    r = col.row()
    rr = r.row()

    if scene_props.show_action_settings: rr.alert = True
    icon = 'PREFERENCES'
    rr.operator('scene.y_toggle_action_settings', text='', icon=icon).prop = 'show_action_settings'

    #col.label(text='Active: ' + action.name, icon='ACTION')
    if action:
        r.label(text='Active Action: ' + action.name)
    else:
        r.label(text='Active Action: -')

    if scene_props.show_action_settings:

        box = col.box()
        bcol = box.column()

        if not action:
            bcol.label(text='No active action!')
        else:
            bcol.prop(action, 'use_frame_range')

            if action.use_frame_range:
                brow = bcol.row(align=True)
                brow.prop(action, 'frame_start')
                brow.prop(action, 'frame_end')

            action_props = action.rigify_export_props

            bcol.prop(action_props, 'enable_loop')

            if action_props.enable_loop:
                brow = bcol.row()
                brow.active = (not action.use_frame_range) # and action_props.enable_loop
                brow.prop(action_props, 'enable_skip_last_frame')

    r = col.row()
    rr = r.row()

    if scene_props.show_global_settings: rr.alert = True
    icon = 'PREFERENCES' # if is_greater_than_280() else 'SCRIPTWIN'
    rr.operator('scene.y_toggle_action_global_settings', text='', icon=icon).prop = 'show_global_settings'

    #r.label(text='Action Manager Settings:', icon='PREFERENCES')
    r.label(text='Action Manager Settings:')

    if scene_props.show_global_settings:

        box = col.box()
        bcol = box.column()

        bcol.prop(scene_props, 'sync_unkeyframed_bones')
        bcol.prop(scene_props, 'sync_frames')
        bcol.prop(scene_props, 'sync_bone_layers')

class UE4HELPER_PT_item_RigifyExportActionPanel(bpy.types.Panel):
    bl_label = "Action Manager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"

    @classmethod
    def poll(cls, context):
        return get_current_armature_object()

    def draw(self, context):
        draw_action_manager(self, context)

class UE4HELPER_PT_RigifyExportActionPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_context = "objectmode"
    bl_label = "Action Manager"
    bl_category = "Ucup Exporter"

    @classmethod
    def poll(cls, context):
        return get_current_armature_object()

    def draw(self, context):
        draw_action_manager(self, context)

class ACTION_UL_y_action_lists(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        action_props = item.rigify_export_props
        row = layout.row(align=True)
        row.prop(item, 'name', text='', emboss=False, icon='ACTION')

        rrow = row.row(align=True)
        rrow.active = item.use_frame_range
        rrow.prop(item, 'use_frame_range', text='', icon='ACTION_TWEAK')

        #if item.use_frame_range:
        #    rrow = row.row(align=True)
        #    rrow.label(text='', icon='ACTION_TWEAK')

        #if action_props.enable_loop and not item.use_frame_range:
        #    rrow = row.row(align=True)
        #    rrow.active = action_props.enable_skip_last_frame
        #    rrow.prop(action_props, 'enable_skip_last_frame', text='', icon='FRAME_PREV')

        rrow = row.row(align=True)
        rrow.active = action_props.enable_loop
        rrow.prop(action_props, 'enable_loop', text='', icon='FILE_REFRESH')

        rrow = row.row(align=True)
        rrow.prop(item, 'use_fake_user', text='', emboss=False)
        #rrow.prop(item, 'use_fake_user', text='')

        rrow = row.row(align=True)
        rrow.prop(action_props, 'enable_export', text='')

class YActionListSpecialMenu(bpy.types.Menu):
    bl_idname = "ACTION_MT_y_action_list_special_menu"
    bl_label = "Action Special Menu"
    bl_description = "Action Special Menu"

    @classmethod
    def poll(cls, context):
        return get_current_armature_object()

    def draw(self, context):
        self.layout.operator('armature.y_remove_non_transformative_frames', icon='ACTION')

def update_frame_range(self, context):
    obj =  get_current_armature_object()
    scene = context.scene
    scene_props = scene.rigify_export_props
    wm_props = context.window_manager.rigify_export_props

    if not scene_props.sync_frames: return

    # Get action
    action = bpy.data.actions[wm_props.active_action]
    action_props = action.rigify_export_props

    if obj.animation_data.action == action:
        # Set start and end frame
        if action.use_frame_range:
            scene.frame_start = int(action.frame_start)
            scene.frame_end = int(action.frame_end)
        else:
            scene.frame_start = int(action.frame_range[0])
            scene.frame_end = int(action.frame_range[1])

        # Skip last frame option
        if action_props.enable_loop and action_props.enable_skip_last_frame:
            scene.frame_end = scene.frame_end-1

def update_action(self, context):
    obj =  get_current_armature_object()
    scene_props = context.scene.rigify_export_props

    if self.active_action >= len(bpy.data.actions) or self.active_action < 0:
        return

    # Get action
    action = bpy.data.actions[self.active_action]
    action_props = action.rigify_export_props

    # Reset all bone transformations first
    if scene_props.sync_unkeyframed_bones:

        reset_pose_bones(obj)

    # Set action
    if not obj.animation_data:
        obj.animation_data_create()
    obj.animation_data.action = action

    # Update scene frame range
    update_frame_range(action, context)

    if scene_props.sync_bone_layers:

        # Get all bone names related to action
        bone_names = []
        for fcurve in action.fcurves:
            if fcurve.group and fcurve.group.name not in bone_names:
                bone_names.append(fcurve.group.name)

        # Get relevant layers
        layers = []
        for name in bone_names:
            bone = obj.data.bones.get(name)
            if bone:
                for i in range(32):
                    if bone.layers[i] and i not in layers:
                        layers.append(i)

        # Enable only relevant layers
        if layers:
            for i in range(32):
                obj.data.layers[i] = i in layers

        #print(bone_names)

class YSceneRigifyExportActionProps(bpy.types.PropertyGroup):

    show_action_settings : BoolProperty(default=True)
    show_global_settings : BoolProperty(default=False)

    sync_bone_layers : BoolProperty(
            name = 'Sync Bone Layers',
            description = 'Sync bone layers when active action changes',
            default = False
            )

    sync_frames : BoolProperty(
            name = 'Sync Frames',
            description = 'Sync frame start and end when active action changes',
            default = True
            )

    sync_unkeyframed_bones : BoolProperty(
            name = 'Sync Unkeyframed Bones',
            description = 'Clear unkeyframed bones when changing action',
            default = True
            )

class YWMRigifyExportActionProps(bpy.types.PropertyGroup):
    active_action : IntProperty(default=0, update=update_action)

class YActionRigifyExportActionProps(bpy.types.PropertyGroup):

    enable_export : BoolProperty(
            name = 'Enable Export',
            description = 'Export this action (only works on Godot for now)',
            default = True
            )

    enable_loop : BoolProperty(
            name = 'Enable Loop',
            description = 'Enable animation loop (only works on Godot for now)',
            default = False,
            update=update_frame_range)

    enable_skip_last_frame : BoolProperty(
            name = 'Enable Skip Last Frame',
            description = 'Enable skip the last frame (only works on Godot for now)',
            default = True,
            update=update_frame_range)

def register():
    bpy.utils.register_class(YNewAction)
    bpy.utils.register_class(YRemoveAction)
    bpy.utils.register_class(YToggleDeselectAction)
    bpy.utils.register_class(YRemoveNonTransformativeFrames)
    bpy.utils.register_class(YToggleActionSettings)
    bpy.utils.register_class(YToggleActionGlobalSettings)
    bpy.utils.register_class(UE4HELPER_PT_RigifyExportActionPanel)
    bpy.utils.register_class(UE4HELPER_PT_item_RigifyExportActionPanel)
    bpy.utils.register_class(YSceneRigifyExportActionProps)
    bpy.utils.register_class(YWMRigifyExportActionProps)
    bpy.utils.register_class(YActionRigifyExportActionProps)
    bpy.utils.register_class(ACTION_UL_y_action_lists)
    bpy.utils.register_class(YActionListSpecialMenu)

    bpy.types.Scene.rigify_export_props = PointerProperty(type=YSceneRigifyExportActionProps)
    bpy.types.Action.rigify_export_props = PointerProperty(type=YActionRigifyExportActionProps)
    bpy.types.WindowManager.rigify_export_props = PointerProperty(type=YWMRigifyExportActionProps)

def unregister():
    bpy.utils.unregister_class(YNewAction)
    bpy.utils.unregister_class(YRemoveAction)
    bpy.utils.unregister_class(YToggleDeselectAction)
    bpy.utils.unregister_class(YRemoveNonTransformativeFrames)
    bpy.utils.unregister_class(YToggleActionSettings)
    bpy.utils.unregister_class(YToggleActionGlobalSettings)
    bpy.utils.unregister_class(UE4HELPER_PT_RigifyExportActionPanel)
    bpy.utils.unregister_class(UE4HELPER_PT_item_RigifyExportActionPanel)
    bpy.utils.unregister_class(YSceneRigifyExportActionProps)
    bpy.utils.unregister_class(YWMRigifyExportActionProps)
    bpy.utils.unregister_class(YActionRigifyExportActionProps)
    bpy.utils.unregister_class(ACTION_UL_y_action_lists)
    bpy.utils.unregister_class(YActionListSpecialMenu)
