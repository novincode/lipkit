"""
UI Panels for LipKit
"""

import bpy
import os


class LIPKIT_PT_setup(bpy.types.Panel):
    """Setup panel - shows at the top"""
    bl_label = "Setup"
    bl_idname = "LIPKIT_PT_setup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LipKit"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        from .preferences import get_preferences
        prefs = get_preferences(context)
        
        # Tool status
        box = layout.box()
        box.label(text="Rhubarb Lip Sync Tool:", icon='TOOL_SETTINGS')
        
        # Check if tool is configured and exists
        tool_configured = bool(prefs.local_tool_path)
        tool_exists = tool_configured and os.path.exists(prefs.local_tool_path)
        
        if not tool_configured:
            box.label(text="❌ Not configured", icon='ERROR')
            box.label(text="Select folder or executable below", icon='QUESTION')
        elif not tool_exists:
            box.label(text="❌ File not found", icon='ERROR')
            box.label(text=f"Path: {prefs.local_tool_path}", icon='QUESTION')
        else:
            box.label(text="✅ Ready", icon='CHECKMARK')
            row = box.row()
            row.label(text=os.path.basename(prefs.local_tool_path))
        
        # File selector button
        row = layout.row()
        row.scale_y = 1.5
        if tool_configured and tool_exists:
            # Show "Change" button if already configured
            row.operator("lipkit.select_rhubarb", text="📁 Change Path", icon='FILE_FOLDER')
        else:
            # Show "Select" button if not configured
            row.operator("lipkit.select_rhubarb", text="📁 Select Rhubarb", icon='FILE_FOLDER')
        
        # Info
        layout.separator()
        info_box = layout.box()
        info_box.label(text="Steps:", icon='INFO')
        info_box.label(text="1. Download Rhubarb from GitHub")
        info_box.label(text="2. Extract the ZIP file")
        info_box.label(text="3. Click above to select folder")
        info_box.label(text="4. Should show ✅ Ready")
        
        # Download link
        layout.separator()
        col = layout.column()
        col.scale_y = 0.8
        col.label(text="Download Rhubarb:", icon='URL')
        col.label(text="github.com/DanielSWolf/")
        col.label(text="rhubarb-lip-sync/releases")


class LIPKIT_PT_main(bpy.types.Panel):
    """Main LipKit panel"""
    bl_label = "LipKit"
    bl_idname = "LIPKIT_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LipKit"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.lipkit
        
        layout.label(text="Universal Lip Sync", icon='SPEAKER')
        
        # Quick status
        if props.controller_object:
            layout.label(text=f"✓ Controller: {props.controller_object.name}", icon='CHECKMARK')
        else:
            layout.operator("lipkit.create_controller", icon='PLUS', text="Create Controller")


class LIPKIT_PT_audio(bpy.types.Panel):
    """Audio source panel"""
    bl_label = "Audio Source"
    bl_idname = "LIPKIT_PT_audio"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LipKit"
    bl_parent_id = "LIPKIT_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.lipkit
        
        layout.prop(props, "audio_source", expand=True)
        
        if props.audio_source == 'FILE':
            layout.prop(props, "audio_filepath", text="")
        elif props.audio_source == 'VSE':
            layout.prop(props, "vse_strip", text="Strip")
            
            if props.vse_strip == 'NONE':
                box = layout.box()
                box.label(text="No sound strips found", icon='INFO')
                box.label(text="Add a sound strip to VSE")


class LIPKIT_PT_phoneme_engine(bpy.types.Panel):
    """Phoneme engine panel"""
    bl_label = "Phoneme Engine"
    bl_idname = "LIPKIT_PT_phoneme_engine"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LipKit"
    bl_parent_id = "LIPKIT_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.lipkit
        
        layout.prop(props, "phoneme_provider", text="Engine")
        
        # Show Rhubarb path selector if LOCAL is selected
        if props.phoneme_provider == 'LOCAL':
            box = layout.box()
            box.label(text="Rhubarb Setup:", icon='TOOL_SETTINGS')
            
            tool_path = props.rhubarb_path
            
            # Check status
            if tool_path and os.path.exists(tool_path):
                box.label(text="✅ Ready", icon='CHECKMARK')
                box.label(text=os.path.basename(tool_path))
            else:
                box.label(text="❌ Not configured", icon='ERROR')
            
            # Simple folder selector
            row = box.row()
            row.scale_y = 1.3
            row.operator("lipkit.select_rhubarb", text="Select Rhubarb Folder", icon='FILEBROWSER')
            
            # Info
            box.label(text="Download, extract, select folder")
            box.label(text="github.com/DanielSWolf/rhubarb-lip-sync")
        
        layout.prop(props, "language")
        
        # Analyze button
        row = layout.row()
        row.scale_y = 1.5
        
        if props.phoneme_data_cached:
            row.operator("lipkit.analyze_audio", text="Re-Analyze Audio", icon='FILE_REFRESH')
        else:
            row.operator("lipkit.analyze_audio", text="Analyze Audio", icon='PLAY')
        
        # Status
        if props.phoneme_data_cached:
            box = layout.box()
            box.label(text="✓ Phoneme data ready", icon='CHECKMARK')


class LIPKIT_PT_visual_system(bpy.types.Panel):
    """Visual system panel"""
    bl_label = "Visual System"
    bl_idname = "LIPKIT_PT_visual_system"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LipKit"
    bl_parent_id = "LIPKIT_PT_main"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.lipkit
        
        layout.prop(props, "visual_system", text="Type")
        layout.prop(props, "target_object")
        
        # Info based on selection
        if props.target_object:
            obj = props.target_object
            box = layout.box()
            
            if props.visual_system == 'gp_layer' and obj.type == 'GPENCIL':
                layer_count = len(obj.data.layers)
                box.label(text=f"✓ {layer_count} GP layers found", icon='GREASEPENCIL')
            
            elif props.visual_system == 'shape_key':
                if hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
                    sk_count = len(obj.data.shape_keys.key_blocks) - 1  # Exclude basis
                    box.label(text=f"✓ {sk_count} shape keys found", icon='SHAPEKEY_DATA')
                else:
                    box.label(text="⚠ No shape keys found", icon='ERROR')
            
            else:
                box.label(text=f"Object type: {obj.type}", icon='OBJECT_DATA')


class LIPKIT_PT_mapping(bpy.types.Panel):
    """Phoneme mapping panel"""
    bl_label = "Phoneme Mapping"
    bl_idname = "LIPKIT_PT_mapping"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LipKit"
    bl_parent_id = "LIPKIT_PT_main"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.lipkit
        
        # Target object selector FIRST
        box = layout.box()
        box.label(text="Animation Target:", icon='OBJECT_DATA')
        box.prop(props, "target_object", text="")
        
        if props.target_object:
            obj = props.target_object
            obj_type = obj.type
            
            # Show what's available - DYNAMIC based on object type
            if obj_type == 'MESH':
                if hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
                    sk_count = len(obj.data.shape_keys.key_blocks) - 1
                    box.label(text=f"✓ {sk_count} shape keys", icon='SHAPEKEY_DATA')
                else:
                    box.label(text="⚠ No shape keys", icon='INFO')
            
            elif obj_type == 'GPENCIL':
                if hasattr(obj.data, 'layers'):
                    layer_count = len(obj.data.layers)
                    box.label(text=f"✓ {layer_count} GP layers", icon='GREASEPENCIL')
                else:
                    box.label(text="⚠ No layers", icon='INFO')
            
            else:
                box.label(text=f"⚠ Type '{obj_type}' not supported", icon='ERROR')
        
        layout.separator()
        
        # Preset selection (with settings icon for advanced)
        row = layout.row(align=True)
        row.prop(props, "phoneme_preset", text="Preset")
        
        layout.separator()
        
        # Manual mapping section
        if len(props.phoneme_mappings) == 0:
            box = layout.box()
            box.label(text="Load a preset first", icon='INFO')
            layout.operator("lipkit.load_preset", text="Load Preset", icon='PRESET')
        else:
            # Stats at top
            mapped_count = sum(1 for m in props.phoneme_mappings 
                              if m.target_object and m.target_property and m.enabled)
            total_count = len(props.phoneme_mappings)
            
            row = layout.row()
            if mapped_count == total_count:
                row.label(text=f"✓ All {total_count} mapped", icon='CHECKMARK')
            else:
                row.label(text=f"Mapped: {mapped_count}/{total_count}", icon='INFO')
            
            # Show ALL mappings in a scrollable list
            box = layout.box()
            box.label(text="Select Target for Each Sound:", icon='SPEAKER')
            
            for i, mapping in enumerate(props.phoneme_mappings):
                # Each phoneme gets one clean row
                row = box.row(align=True)
                row.prop(mapping, "enabled", text="")
                row.label(text=f"{mapping.phoneme}:")
                
                # Select button
                row.operator("lipkit.select_mapping_target", text="Select", icon='EYEDROPPER').mapping_index = i
                
                # Show current mapping
                if mapping.target_property:
                    row.label(text=mapping.target_property, icon='CHECKMARK')
                else:
                    row.label(text="(not set)", icon='BLANK1')



class LIPKIT_PT_controller(bpy.types.Panel):
    """Controller panel"""
    bl_label = "Controller"
    bl_idname = "LIPKIT_PT_controller"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LipKit"
    bl_parent_id = "LIPKIT_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.lipkit
        
        if props.controller_object:
            box = layout.box()
            box.label(text=f"✓ {props.controller_object.name}", icon='EMPTY_AXIS')
            
            row = box.row(align=True)
            row.operator("lipkit.clear_animation", text="Clear", icon='X')
        else:
            layout.operator("lipkit.create_controller", icon='ADD')


class LIPKIT_PT_generate(bpy.types.Panel):
    """Generation panel"""
    bl_label = "Generate"
    bl_idname = "LIPKIT_PT_generate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "LipKit"
    bl_parent_id = "LIPKIT_PT_main"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.lipkit
        
        # Animation settings
        col = layout.column(align=True)
        col.prop(props, "start_frame")
        col.prop(props, "use_nla")
        
        if props.use_nla:
            col.prop(props, "action_name")
        
        col.prop(props, "interpolation")
        
        layout.separator()
        
        # Generate button
        col = layout.column()
        col.scale_y = 2.0
        
        # Check prerequisites
        can_generate = True
        issues = []
        
        if not props.controller_object:
            can_generate = False
            issues.append("No controller")
        
        if not props.target_object:
            can_generate = False
            issues.append("No target object")
        
        if not props.phoneme_data_cached:
            can_generate = False
            issues.append("No phoneme data")
        
        mapped_count = sum(1 for m in props.phoneme_mappings if m.target_name and m.enabled)
        if mapped_count == 0:
            can_generate = False
            issues.append("No mappings")
        
        if can_generate:
            col.operator("lipkit.generate", text="🚀 Generate Lip Sync", icon='PLAY')
        else:
            col.enabled = False
            col.operator("lipkit.generate", text="Generate Lip Sync", icon='ERROR')
            
            # Show issues
            box = layout.box()
            box.label(text="Issues:", icon='ERROR')
            for issue in issues:
                box.label(text=f"• {issue}")


# Registration
classes = [
    LIPKIT_PT_main,
    LIPKIT_PT_audio,
    LIPKIT_PT_phoneme_engine,
    LIPKIT_PT_visual_system,
    LIPKIT_PT_mapping,
    LIPKIT_PT_controller,
    LIPKIT_PT_generate,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
