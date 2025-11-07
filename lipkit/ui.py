"""
UI Panels for LipKit
"""

import bpy


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
        
        # Preset selection
        row = layout.row(align=True)
        row.prop(props, "phoneme_preset", text="Preset")
        row.operator("lipkit.load_preset", text="", icon='FILE_REFRESH')
        
        # Auto-map button
        layout.operator("lipkit.auto_map_targets", icon='AUTO')
        
        layout.separator()
        
        # Mapping list
        box = layout.box()
        box.label(text="Mappings:", icon='LINENUMBERS_ON')
        
        if len(props.phoneme_mappings) == 0:
            box.label(text="Load a preset to begin", icon='INFO')
        else:
            # Show first few mappings as example
            for i, mapping in enumerate(props.phoneme_mappings[:5]):
                row = box.row()
                row.prop(mapping, "enabled", text="")
                row.label(text=f"{mapping.phoneme} [{mapping.phoneme_index}]")
                row.prop(mapping, "target_name", text="")
            
            if len(props.phoneme_mappings) > 5:
                box.label(text=f"... and {len(props.phoneme_mappings) - 5} more")
        
        # Stats
        mapped_count = sum(1 for m in props.phoneme_mappings if m.target_name and m.enabled)
        total_count = len(props.phoneme_mappings)
        
        if total_count > 0:
            layout.label(text=f"Mapped: {mapped_count}/{total_count}", icon='CHECKMARK')


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
