"""
Blender property groups for LipKit

Copyright (C) 2024-2025 Shayan Moradi
SPDX-License-Identifier: GPL-3.0-or-later
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


def detect_visual_system(obj: bpy.types.Object) -> str:
    """
    Auto-detect visual system type from object
    
    Args:
        obj: Blender object
        
    Returns:
        'gp_layer', 'shape_key', or 'image_sequence'
    """
    if not obj:
        return 'gp_layer'  # Default
    
    # Check if it's a Grease Pencil object (Blender 4.x and 5.x)
    if obj.type in ('GPENCIL', 'GREASEPENCIL'):
        return 'gp_layer'
    
    # Check if it has shape keys
    if obj.type == 'MESH':
        if hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
            return 'shape_key'
    
    # Default fallback
    return 'gp_layer'


def get_all_scenes_with_sequencer():
    """Get all scenes that might have a sequencer, Blender 4.x and 5.x compatible"""
    scenes = set()
    
    # Add all scenes from bpy.data.scenes
    for scene in bpy.data.scenes:
        scenes.add(scene)
    
    # Blender 5.x: Check workspace.sequencer_scene
    try:
        for workspace in bpy.data.workspaces:
            seq_scene = getattr(workspace, 'sequencer_scene', None)
            if seq_scene:
                scenes.add(seq_scene)
    except:
        pass
    
    # Blender 5.x: Check context.sequencer_scene if available
    try:
        ctx = bpy.context
        if hasattr(ctx, 'sequencer_scene') and ctx.sequencer_scene:
            scenes.add(ctx.sequencer_scene)
    except:
        pass
    
    return list(scenes)


def get_sound_strips(self, context):
    """Get list of sound strips from VSE across ALL scenes - Blender 4.2+ and 5.x compatible"""
    items = [('NONE', 'None', 'No sound strip selected')]
    
    found_sounds = []
    
    # Get all possible scenes
    all_scenes = get_all_scenes_with_sequencer()
    
    for scene in all_scenes:
        # Get sequence editor - try multiple methods for Blender 5 compatibility
        seq_editor = None
        
        # Method 1: Direct attribute
        if hasattr(scene, 'sequence_editor') and scene.sequence_editor:
            seq_editor = scene.sequence_editor
        
        if not seq_editor:
            continue
        
        # Get sequences - try multiple attributes
        sequences = None
        
        # Try sequences_all first (includes muted/hidden)
        if hasattr(seq_editor, 'sequences_all') and seq_editor.sequences_all:
            sequences = seq_editor.sequences_all
        # Fallback to sequences
        elif hasattr(seq_editor, 'sequences') and seq_editor.sequences:
            sequences = seq_editor.sequences
        
        if not sequences:
            continue
        
        for strip in sequences:
            try:
                strip_type = getattr(strip, 'type', '')
                
                if strip_type == 'SOUND':
                    # Use unique identifier: scene_name::strip_name
                    unique_id = f"{scene.name}::{strip.name}"
                    channel = getattr(strip, 'channel', 0)
                    
                    # Get sound filepath for tooltip
                    sound = getattr(strip, 'sound', None)
                    filepath = ""
                    if sound:
                        filepath = getattr(sound, 'filepath', '')
                    
                    # Show scene, channel, and strip name
                    label = f"[{scene.name}] Ch{channel}: {strip.name}"
                    tooltip = f"Scene: {scene.name}, Channel: {channel}, File: {filepath}"
                    
                    found_sounds.append((unique_id, label, tooltip))
            except Exception as e:
                print(f"[LipKit] Error reading strip: {e}")
    
    # Also offer direct access to loaded sounds (as fallback)
    for sound in bpy.data.sounds:
        try:
            filepath = bpy.path.abspath(sound.filepath)
            if filepath:
                sound_id = f"SOUND::{sound.name}"
                label = f"[Sound] {sound.name}"
                tooltip = f"Direct sound file: {filepath}"
                # Only add if not already in VSE strips
                if not any(s[0].endswith(f"::{sound.name}") for s in found_sounds):
                    found_sounds.append((sound_id, label, tooltip))
        except:
            pass
    
    # Add all found sounds
    items.extend(found_sounds)
    
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


def clear_phoneme_data(props):
    """Clear all phoneme data when audio source changes"""
    props.phoneme_data_cached = False
    props.has_phoneme_data = False
    props.phoneme_data_json = ""
    
    # Clear module cache too
    try:
        from .operators import clear_cached_phoneme_data
        clear_cached_phoneme_data()
    except:
        pass


def on_audio_filepath_changed(self, context):
    """Called when audio file path changes - clear phoneme data"""
    clear_phoneme_data(self)


def on_vse_strip_changed(self, context):
    """Called when VSE strip selection changes - clear phoneme data"""
    clear_phoneme_data(self)


def on_audio_source_changed(self, context):
    """Called when audio source type changes - clear phoneme data"""
    clear_phoneme_data(self)


def on_preset_changed(self, context):
    """Auto-load preset when selection changes"""
    # Import here to avoid circular imports
    from .core.mapping import PresetManager
    
    # Don't auto-load custom preset
    if self.phoneme_preset == 'custom':
        return
    
    try:
        preset_data = PresetManager.load_preset(self.phoneme_preset)
        
        if not preset_data:
            return
        
        # Clear existing mappings
        self.phoneme_mappings.clear()
        
        # Add mappings from preset
        for item in preset_data.get("mappings", []):
            mapping = self.phoneme_mappings.add()
            mapping.phoneme = item.get("phoneme", "")
            mapping.phoneme_index = item.get("index", 0)
            mapping.target_name = ""  # User needs to set this
            mapping.enabled = True
        
        print(f"✓ Auto-loaded preset: {preset_data.get('name', self.phoneme_preset)}")
    
    except Exception as e:
        print(f"Failed to auto-load preset: {e}")


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
        default='FILE',
        update=on_audio_source_changed
    )
    
    audio_filepath: StringProperty(
        name="Audio File",
        description="Path to audio file",
        subtype='FILE_PATH',
        default="",
        update=on_audio_filepath_changed
    )
    
    vse_strip: EnumProperty(
        name="VSE Strip",
        description="Sound strip from Video Sequence Editor",
        items=get_sound_strips,
        update=on_vse_strip_changed
    )
    
    # Phoneme Engine Section
    rhubarb_path: StringProperty(
        name="Rhubarb Path",
        description="Path to Rhubarb executable",
        subtype='FILE_PATH',
        default=""
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
        default='rhubarb',
        update=on_preset_changed
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
    
    # Timing adjustments
    min_hold_frames: IntProperty(
        name="Min Hold Frames",
        description="Minimum frames each mouth shape must hold. Increase to reduce jittery rapid changes (0 = no minimum)",
        default=2,
        min=0,
        max=24
    )
    
    merge_threshold: FloatProperty(
        name="Merge Threshold",
        description="Merge phonemes closer than this many seconds (0 = no merging)",
        default=0.04,
        min=0.0,
        max=0.2,
        step=1,
        precision=3
    )
    
    # State
    phoneme_data_cached: BoolProperty(
        name="Phoneme Data Cached",
        description="Whether phoneme data has been extracted",
        default=False
    )
    
    # Store analyzed phoneme data as JSON
    phoneme_data_json: StringProperty(
        name="Phoneme Data JSON",
        description="JSON string of analyzed phoneme data",
        default=""
    )
    
    has_phoneme_data: BoolProperty(
        name="Has Phoneme Data",
        description="Whether phoneme data exists and can be saved",
        default=False
    )
    
    audio_analyzing: BoolProperty(
        name="Audio Analyzing",
        description="Whether audio is currently being analyzed",
        default=False
    )
    
    generation_in_progress: BoolProperty(
        name="Generation in Progress",
        description="Whether lip sync generation is in progress",
        default=False
    )
    
    # Rhubarb download state
    rhubarb_downloading: BoolProperty(
        name="Rhubarb Downloading",
        description="Whether Rhubarb is currently downloading",
        default=False
    )
    
    rhubarb_download_error: StringProperty(
        name="Rhubarb Download Error",
        description="Error message from download if failed",
        default=""
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
