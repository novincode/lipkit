"""
Operators for LipKit
"""

import bpy
from bpy.props import StringProperty
import traceback

from .core.controller import LipSyncController
from .core.animation_engine import AnimationEngine
from .core.mapping import PhonemeMapping, PresetManager
from .phoneme_providers import LocalPhonemeProvider, APIPhonemeProvider, CustomAPIProvider
from .utils import audio_utils
from .preferences import get_preferences

# Module-level cache for phoneme data (survives scene changes)
_phoneme_data_cache = None


def get_cached_phoneme_data():
    """Retrieve cached phoneme data from analyze_audio"""
    global _phoneme_data_cache
    return _phoneme_data_cache


class LIPKIT_OT_create_controller(bpy.types.Operator):
    """Create a new LipKit controller object"""
    bl_idname = "lipkit.create_controller"
    bl_label = "Create Controller"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            controller = LipSyncController.create_controller()
            context.scene.lipkit.controller_object = controller
            
            self.report({'INFO'}, f"Created controller: {controller.name}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create controller: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_analyze_audio(bpy.types.Operator):
    """Analyze audio and extract phonemes"""
    bl_idname = "lipkit.analyze_audio"
    bl_label = "Analyze Audio"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.lipkit
        prefs = get_preferences(context)
        
        # Get audio path
        audio_path = None
        if props.audio_source == 'FILE':
            audio_path = bpy.path.abspath(props.audio_filepath)
        elif props.audio_source == 'VSE':
            if props.vse_strip != 'NONE':
                audio_path = audio_utils.get_audio_from_vse(props.vse_strip)
        
        if not audio_path:
            self.report({'ERROR'}, "No audio file selected")
            return {'CANCELLED'}
        
        # Validate audio
        is_valid, error_msg = audio_utils.validate_audio_file(audio_path)
        if not is_valid:
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}
        
        # Check cache first
        if prefs.use_cache:
            cached_data = audio_utils.load_from_cache(
                audio_path,
                props.language,
                props.phoneme_provider
            )
            
            if cached_data:
                self.report({'INFO'}, "Loaded phoneme data from cache")
                # Store in scene (would need a proper storage mechanism)
                props.phoneme_data_cached = True
                return {'FINISHED'}
        
        # Extract phonemes
        try:
            provider = self._get_provider(props, prefs)
            
            if not provider.is_available():
                self.report({'ERROR'}, f"Provider '{provider.name}' is not available")
                return {'CANCELLED'}
            
            self.report({'INFO'}, f"Extracting phonemes using {provider.name}...")
            
            lipsync_data = provider.extract_phonemes(
                audio_path,
                language=props.language
            )
            
            # Cache result
            if prefs.use_cache:
                audio_utils.save_to_cache(
                    audio_path,
                    props.language,
                    props.phoneme_provider,
                    lipsync_data
                )
            
            # Store in scene AND module cache
            global _phoneme_data_cache
            _phoneme_data_cache = lipsync_data
            props.phoneme_data_cached = True
            
            self.report(
                {'INFO'},
                f"Extracted {len(lipsync_data.phonemes)} phonemes ({lipsync_data.duration:.1f}s)"
            )
            
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to analyze audio: {str(e)}")
            if prefs.debug_mode:
                traceback.print_exc()
            return {'CANCELLED'}
    
    def _get_provider(self, props, prefs):
        """Get the appropriate phoneme provider"""
        if props.phoneme_provider == 'LOCAL':
            return LocalPhonemeProvider(tool_path=prefs.local_tool_path)
        
        elif props.phoneme_provider == 'API':
            return APIPhonemeProvider(
                api_key=prefs.api_key,
                endpoint=prefs.api_endpoint
            )
        
        elif props.phoneme_provider == 'CUSTOM':
            return CustomAPIProvider(
                endpoint=prefs.custom_api_endpoint,
                api_key=prefs.custom_api_key
            )
        
        else:
            return LocalPhonemeProvider()


class LIPKIT_OT_load_preset(bpy.types.Operator):
    """Load phoneme mapping preset"""
    bl_idname = "lipkit.load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        
        try:
            preset_data = PresetManager.load_preset(props.phoneme_preset)
            
            if not preset_data:
                self.report({'ERROR'}, f"Preset not found: {props.phoneme_preset}")
                return {'CANCELLED'}
            
            # Clear existing mappings
            props.phoneme_mappings.clear()
            
            # Add mappings from preset
            for item in preset_data.get("mappings", []):
                mapping = props.phoneme_mappings.add()
                mapping.phoneme = item.get("phoneme", "")
                mapping.phoneme_index = item.get("index", 0)
                mapping.target_name = ""  # User needs to set this
                mapping.enabled = True
            
            self.report({'INFO'}, f"Loaded preset: {preset_data.get('name', props.phoneme_preset)}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load preset: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_auto_map_targets(bpy.types.Operator):
    """Automatically map targets based on naming"""
    bl_idname = "lipkit.auto_map_targets"
    bl_label = "Auto-Map Targets"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        target_obj = props.target_object
        
        if not target_obj:
            self.report({'ERROR'}, "No target object selected")
            return {'CANCELLED'}
        
        mapped_count = 0
        
        try:
            if props.visual_system == 'gp_layer' and target_obj.type == 'GPENCIL':
                # Auto-map GP layers
                for mapping in props.phoneme_mappings:
                    phoneme = mapping.phoneme.lower()
                    
                    for layer in target_obj.data.layers:
                        if phoneme in layer.info.lower():
                            mapping.target_name = layer.info
                            mapped_count += 1
                            break
            
            elif props.visual_system == 'shape_key':
                # Auto-map shape keys
                if hasattr(target_obj.data, 'shape_keys') and target_obj.data.shape_keys:
                    for mapping in props.phoneme_mappings:
                        phoneme = mapping.phoneme.lower()
                        
                        for key in target_obj.data.shape_keys.key_blocks:
                            if phoneme in key.name.lower():
                                mapping.target_name = key.name
                                mapped_count += 1
                                break
            
            self.report({'INFO'}, f"Auto-mapped {mapped_count} targets")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to auto-map: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_generate(bpy.types.Operator):
    """Generate lip sync animation"""
    bl_idname = "lipkit.generate"
    bl_label = "Generate Lip Sync"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        prefs = get_preferences(context)
        
        # Validate inputs
        if not props.controller_object:
            self.report({'ERROR'}, "No controller object - create one first")
            return {'CANCELLED'}
        
        if not props.target_object:
            self.report({'ERROR'}, "No target object selected")
            return {'CANCELLED'}
        
        if not props.phoneme_data_cached:
            self.report({'ERROR'}, "No phoneme data - analyze audio first")
            return {'CANCELLED'}
        
        # Get audio path (for re-extraction)
        audio_path = None
        if props.audio_source == 'FILE':
            audio_path = bpy.path.abspath(props.audio_filepath)
        elif props.audio_source == 'VSE':
            if props.vse_strip != 'NONE':
                audio_path = audio_utils.get_audio_from_vse(props.vse_strip)
        
        if not audio_path:
            self.report({'ERROR'}, "No audio file available")
            return {'CANCELLED'}
        
        try:
            props.generation_in_progress = True
            
            # Use cached phoneme data
            lipsync_data = get_cached_phoneme_data()
            
            if not lipsync_data:
                self.report({'ERROR'}, "Phoneme data lost - analyze audio again")
                return {'CANCELLED'}
            
            # Build mapping
            mapping = PhonemeMapping()
            mapping.name = props.action_name
            mapping.visual_system = props.visual_system
            mapping.target_object = props.target_object.name
            mapping.phoneme_set = props.phoneme_preset
            
            for item in props.phoneme_mappings:
                if item.enabled and item.target_name:
                    mapping.add_mapping(
                        item.phoneme,
                        item.phoneme_index,
                        item.target_name
                    )
            
            # Generate animation
            engine = AnimationEngine(lipsync_data, mapping, props.controller_object)
            
            results = engine.generate(
                props.target_object,
                start_frame=props.start_frame,
                use_nla=props.use_nla,
                action_name=props.action_name
            )
            
            self.report(
                {'INFO'},
                f"Generated {results['keyframes_created']} keyframes, "
                f"{results['drivers_created']} drivers"
            )
            
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Generation failed: {str(e)}")
            if prefs.debug_mode:
                traceback.print_exc()
            return {'CANCELLED'}
        
        finally:
            props.generation_in_progress = False


class LIPKIT_OT_clear_animation(bpy.types.Operator):
    """Clear generated lip sync animation"""
    bl_idname = "lipkit.clear_animation"
    bl_label = "Clear Animation"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        
        if not props.controller_object:
            self.report({'WARNING'}, "No controller object")
            return {'CANCELLED'}
        
        try:
            LipSyncController.clear_animation(props.controller_object)
            self.report({'INFO'}, "Cleared animation from controller")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to clear: {str(e)}")
            return {'CANCELLED'}


# Registration
classes = [
    LIPKIT_OT_create_controller,
    LIPKIT_OT_analyze_audio,
    LIPKIT_OT_load_preset,
    LIPKIT_OT_auto_map_targets,
    LIPKIT_OT_generate,
    LIPKIT_OT_clear_animation,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
