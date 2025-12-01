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
            # Refresh button to force re-scan
            row = layout.row(align=True)
            row.prop(props, "vse_strip", text="")
            row.operator("lipkit.refresh_vse_strips", text="", icon='FILE_REFRESH')
            
            # Count sounds across all scenes
            sound_count = 0
            direct_sound_count = len(bpy.data.sounds)
            
            for scene in bpy.data.scenes:
                seq = getattr(scene, 'sequence_editor', None)
                if seq:
                    seqs = getattr(seq, 'sequences_all', None) or getattr(seq, 'sequences', [])
                    if seqs:
                        for s in seqs:
                            if getattr(s, 'type', '') == 'SOUND':
                                sound_count += 1
            
            if props.vse_strip == 'NONE':
                box = layout.box()
                if sound_count == 0 and direct_sound_count == 0:
                    box.label(text="No sounds found", icon='ERROR')
                    box.label(text="Add audio to VSE or load a sound file", icon='INFO')
                elif sound_count == 0 and direct_sound_count > 0:
                    box.label(text=f"No VSE strips, but {direct_sound_count} sounds loaded", icon='INFO')
                    box.label(text="Click refresh ↻ to update list", icon='FILE_REFRESH')
                else:
                    box.label(text=f"Found {sound_count} VSE strips", icon='INFO')
                    box.label(text="Click refresh ↻ if not showing", icon='FILE_REFRESH')


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
        
        from .preferences import get_preferences, PreferencesDefaults
        from .utils.rhubarb_manager import get_effective_rhubarb_path, get_rhubarb_executable
        prefs = get_preferences(context)
        
        layout.label(text="Rhubarb Setup", icon='TOOL_SETTINGS')
        
        # Mode selector
        box = layout.box()
        
        # Only show mode selector if using actual preferences (not fallback)
        if not isinstance(prefs, PreferencesDefaults):
            try:
                box.prop(prefs, "rhubarb_mode", text="Mode")
                mode = prefs.rhubarb_mode
            except:
                mode = 'auto'
        else:
            mode = 'auto'
        
        # Get the effective path (what will actually be used)
        effective_path = get_effective_rhubarb_path(props, prefs)
        
        if mode == 'auto':
            # Auto mode - download button
            exe = get_rhubarb_executable()
            
            if props.rhubarb_downloading:
                # Show loading state
                box.label(text="⏳ Downloading...", icon='PLAY')
                box.label(text="This may take a minute", icon='INFO')
            elif exe and os.path.exists(exe):
                # Already installed
                box.label(text="✅ Installed", icon='CHECKMARK')
                row = box.row()
                row.label(text=os.path.basename(exe))
            else:
                # Not installed
                box.label(text="❌ Not installed", icon='ERROR')
                row = box.row()
                row.scale_y = 1.5
                row.enabled = not props.rhubarb_downloading
                row.operator("lipkit.download_rhubarb", text="📥 Download Rhubarb", icon='IMPORT')
                
                if props.rhubarb_download_error:
                    error_box = box.box()
                    error_box.label(text="Error:", icon='ERROR')
                    for line in props.rhubarb_download_error.split('\n'):
                        error_box.label(text=line)
        
        else:
            # Manual mode - folder selector
            tool_path = props.rhubarb_path or prefs.local_tool_path
            
            if tool_path and os.path.exists(tool_path):
                box.label(text="✅ Ready", icon='CHECKMARK')
                box.label(text=os.path.basename(tool_path))
            else:
                box.label(text="❌ Not configured", icon='ERROR')
            
            row = box.row()
            row.scale_y = 1.3
            row.operator("lipkit.select_rhubarb_manual", text="📁 Select Rhubarb Folder", icon='FILE_FOLDER')
            
            # Info
            box.label(text="Download and extract from:", icon='URL')
            box.label(text="github.com/DanielSWolf/rhubarb-lip-sync/releases")
        
        layout.separator()
        
        # Analyze button - smart state management
        row = layout.row()
        row.scale_y = 1.5
        
        # Check if phoneme data is actually available in memory
        from .operators import get_cached_phoneme_data, LIPKIT_OT_analyze_audio
        cached_data = get_cached_phoneme_data()
        has_valid_data = cached_data is not None and props.phoneme_data_cached
        
        if props.audio_analyzing:
            # Currently analyzing - show progress
            row.enabled = False
            
            # Get elapsed time and progress
            elapsed = 0
            if LIPKIT_OT_analyze_audio._start_time:
                import time
                elapsed = time.time() - LIPKIT_OT_analyze_audio._start_time
            
            percent = LIPKIT_OT_analyze_audio._progress_percent
            
            row.operator("lipkit.analyze_audio", text=f"⏳ Analyzing [{percent}%] ({elapsed:.0f}s)", icon='TIME')
            
            # Progress box with actual percentage
            progress_box = layout.box()
            
            # Progress bar using split
            progress_row = progress_box.row()
            progress_row.scale_y = 0.5
            split = progress_row.split(factor=max(0.01, percent/100))
            split.box()  # Filled portion
            if percent < 100:
                split.label(text="")  # Empty portion
            
            # Show message
            msg = LIPKIT_OT_analyze_audio._progress_message
            if msg:
                progress_box.label(text=msg, icon='INFO')
            
            # Help text
            help_row = progress_box.row()
            help_row.scale_y = 0.7
            help_row.label(text="See Console for details", icon='CONSOLE')
        elif has_valid_data:
            # Data available - can re-analyze
            row.operator("lipkit.analyze_audio", text="Re-Analyze Audio", icon='FILE_REFRESH')
        else:
            # No data - need to analyze (will auto-load if saved data exists)
            row.operator("lipkit.analyze_audio", text="Analyze Audio", icon='PLAY')
        
        # Status and management
        layout.separator()
        
        if has_valid_data:
            # Data is loaded in memory
            box = layout.box()
            box.label(text="✅ Phoneme data ready", icon='CHECKMARK')
            
            # Clear and Delete buttons
            row = layout.row(align=True)
            row.scale_y = 1.1
            row.operator("lipkit.clear_phoneme_data", text="Clear", icon='X')
            row.operator("lipkit.delete_phoneme_data", text="Delete from File", icon='TRASH')


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
        
        # Just show visual system type
        layout.prop(props, "visual_system", text="Type")
        
        # Info about what this means
        box = layout.box()
        if props.visual_system == 'gp_layer':
            box.label(text="Uses Grease Pencil layer opacity", icon='GREASEPENCIL')
        elif props.visual_system == 'shape_key':
            box.label(text="Uses 3D mesh shape keys", icon='SHAPEKEY_DATA')
        else:
            box.label(text="Uses image/texture switching", icon='IMAGE_DATA')


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
        box.label(text="Mouth Object:", icon='OUTLINER_OB_GREASEPENCIL')
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
            
            elif obj_type in ('GPENCIL', 'GREASEPENCIL'):
                if hasattr(obj.data, 'layers'):
                    layer_count = len(obj.data.layers)
                    box.label(text=f"✓ {layer_count} GP layers", icon='GREASEPENCIL')
                else:
                    box.label(text="⚠ No layers", icon='INFO')
            
            else:
                box.label(text=f"⚠ Type '{obj_type}' not supported", icon='ERROR')
        
        layout.separator()
        
        # Manual mapping section
        if len(props.phoneme_mappings) == 0:
            box = layout.box()
            box.label(text="No mouth shapes loaded", icon='INFO')
            row = box.row()
            row.scale_y = 1.3
            row.operator("lipkit.load_preset", text="📥 Load Mouth Shapes", icon='IMPORT')
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
        
        # Controller selector - allows selecting existing or creating new
        box = layout.box()
        box.label(text="Select Controller:", icon='EMPTY_AXIS')
        box.prop(props, "controller_object", text="")
        
        # Create new controller button
        row = layout.row()
        row.scale_y = 1.2
        row.operator("lipkit.create_controller", text="Create New Controller", icon='ADD')
        
        # If controller selected, show management options
        if props.controller_object:
            layout.separator()
            box = layout.box()
            box.label(text=f"Managing: {props.controller_object.name}", icon='CHECKMARK')
            
            row = box.row(align=True)
            row.operator("lipkit.clear_animation", text="Clear Animation", icon='X')
            row.operator("lipkit.clear_all_keyframes", text="Clean All", icon='TRASH')
            
            # Info
            box.label(text="💡 You can have multiple controllers", icon='INFO')
            box.label(text="for multiple characters!")


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
        
        # Generate button - ALWAYS visible
        col = layout.column()
        col.scale_y = 2.0
        
        # Check if currently generating
        if props.generation_in_progress:
            col.enabled = False
            col.operator("lipkit.generate", text="⏳ Generating...", icon='TIME')
            return
        
        # Check prerequisites
        can_generate = True
        issues = []
        
        if not props.controller_object:
            can_generate = False
            issues.append("No controller")
        
        if not props.target_object:
            can_generate = False
            issues.append("No target object")
        
        # Check if phoneme data is actually available
        from .operators import get_cached_phoneme_data
        cached_data = get_cached_phoneme_data()
        if not cached_data or not props.phoneme_data_cached:
            can_generate = False
            issues.append("No phoneme data - analyze audio")
        
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
