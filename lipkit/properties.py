"""
Blender property groups for LipKit
"""

import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    IntProperty,
    FloatProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
)


def get_sound_strips(self, context):
    """Get list of sound strips from VSE"""
    items = [('NONE', 'None', 'No sound strip selected')]
    
    if context.scene.sequence_editor:
        for strip in context.scene.sequence_editor.sequences_all:
            if strip.type == 'SOUND':
                items.append((strip.name, strip.name, f"Sound strip: {strip.name}"))
    
    return items


def get_gp_objects(self, context):
    """Get list of Grease Pencil objects"""
    items = [('NONE', 'None', 'No Grease Pencil object')]
    
    for obj in bpy.data.objects:
        if obj.type in ('GPENCIL', 'GREASEPENCIL'):
            items.append((obj.name, obj.name, f"GP Object: {obj.name}"))
    
    return items


def get_mesh_objects(self, context):
    """Get list of mesh objects with shape keys"""
    items = [('NONE', 'None', 'No mesh object')]
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            has_sk = hasattr(obj.data, 'shape_keys') and obj.data.shape_keys
            label = f"{obj.name} {'(has shape keys)' if has_sk else ''}"
            items.append((obj.name, obj.name, label))
    
    return items


class LipKitPhonemeMappingItem(bpy.types.PropertyGroup):
    """Single phoneme mapping entry"""
    
    phoneme: StringProperty(
        name="Phoneme",
        description="Phoneme code (e.g., AH, EE, M)",
        default=""
    )
    
    phoneme_index: IntProperty(
        name="Index",
        description="Controller index for this phoneme",
        default=0,
        min=0
    )
    
    # New object-based properties
    target_object: PointerProperty(
        name="Target Object",
        description="Object with the animation target (mesh with shape keys or GP object)",
        type=bpy.types.Object
    )
    
    target_property: StringProperty(
        name="Target Property",
        description="Shape key name or GP layer name",
        default=""
    )
    
    # Legacy property (kept for backwards compatibility)
    target_name: StringProperty(
        name="Target",
        description="Name of target layer/shape key",
        default=""
    )
    
    enabled: BoolProperty(
        name="Enabled",
        description="Enable this mapping",
        default=True
    )


class LipKitSceneProperties(bpy.types.PropertyGroup):
    """Main properties stored on scene"""
    
    # Audio Source Section
    audio_source: EnumProperty(
        name="Audio Source",
        description="Where to get audio from",
        items=[
            ('FILE', 'File', 'Load audio from external file'),
            ('VSE', 'VSE Strip', 'Use audio from Video Sequence Editor'),
        ],
        default='FILE'
    )
    
    audio_filepath: StringProperty(
        name="Audio File",
        description="Path to audio file",
        subtype='FILE_PATH',
        default=""
    )
    
    vse_strip: EnumProperty(
        name="VSE Strip",
        description="Sound strip from Video Sequence Editor",
        items=get_sound_strips
    )
    
    # Phoneme Engine Section
    rhubarb_path: StringProperty(
        name="Rhubarb Path",
        description="Path to Rhubarb executable",
        subtype='FILE_PATH',
        default=""
    )
    
    phoneme_provider: EnumProperty(
        name="Phoneme Provider",
        description="Method for extracting phonemes from audio",
        items=[
            ('LOCAL', 'Local (Free)', 'Local phoneme extraction'),
            ('API', 'Cloud API (Premium)', 'Cloud-based extraction (requires API key)'),
            ('CUSTOM', 'Custom API', 'Custom API endpoint'),
        ],
        default='LOCAL'
    )
    
    language: EnumProperty(
        name="Language",
        description="Audio language",
        items=[
            ('en', 'English', 'English'),
            ('es', 'Spanish', 'Spanish'),
            ('fr', 'French', 'French'),
            ('de', 'German', 'German'),
        ],
        default='en'
    )
    
    # Visual System Section
    visual_system: EnumProperty(
        name="Visual System",
        description="Type of visual system to use",
        items=[
            ('gp_layer', 'Grease Pencil Layers', 'Use GP layer visibility'),
            ('shape_key', 'Shape Keys (3D)', 'Use mesh shape keys'),
            ('image_sequence', 'Image Sequence', 'Use texture switching'),
        ],
        default='gp_layer'
    )
    
    target_object: PointerProperty(
        name="Target Object",
        description="Object to animate",
        type=bpy.types.Object
    )
    
    # Controller
    controller_object: PointerProperty(
        name="Controller",
        description="LipKit controller object",
        type=bpy.types.Object
    )
    
    # Mapping
    phoneme_preset: EnumProperty(
        name="Preset",
        description="Phoneme mapping preset",
        items=[
            ('rhubarb', 'Rhubarb (A-H, X)', 'For use with Rhubarb Lip Sync tool'),
            ('preston_blair', 'Preston Blair (9)', 'Classic 2D animation'),
            ('arpabet', 'ARPAbet', 'Full English phoneme set'),
            ('custom', 'Custom', 'Custom mapping'),
        ],
        default='rhubarb'
    )
    
    phoneme_mappings: CollectionProperty(
        type=LipKitPhonemeMappingItem
    )
    
    active_mapping_index: IntProperty(
        name="Active Mapping",
        default=0
    )
    
    # Animation Settings
    start_frame: IntProperty(
        name="Start Frame",
        description="Starting frame for animation",
        default=1,
        min=1
    )
    
    use_nla: BoolProperty(
        name="Use NLA Strip",
        description="Create NLA strip instead of direct keyframes",
        default=True
    )
    
    action_name: StringProperty(
        name="Action Name",
        description="Name for the action/NLA strip",
        default="LipSync"
    )
    
    interpolation: EnumProperty(
        name="Interpolation",
        description="Keyframe interpolation type",
        items=[
            ('CONSTANT', 'Constant', 'Instant switching (recommended)'),
            ('LINEAR', 'Linear', 'Linear interpolation'),
        ],
        default='CONSTANT'
    )
    
    # State
    phoneme_data_cached: BoolProperty(
        name="Phoneme Data Cached",
        description="Whether phoneme data has been extracted",
        default=False
    )
    
    generation_in_progress: BoolProperty(
        name="Generation in Progress",
        description="Whether lip sync generation is in progress",
        default=False
    )


def register():
    bpy.utils.register_class(LipKitPhonemeMappingItem)
    bpy.utils.register_class(LipKitSceneProperties)
    
    # Register property group on scene
    bpy.types.Scene.lipkit = PointerProperty(type=LipKitSceneProperties)


def unregister():
    # Remove property from scene
    del bpy.types.Scene.lipkit
    
    bpy.utils.unregister_class(LipKitSceneProperties)
    bpy.utils.unregister_class(LipKitPhonemeMappingItem)
