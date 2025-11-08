"""
Animation engine - generates keyframes and drivers for lip sync
"""

import bpy
from typing import Dict, List, Optional
from ..core import LipSyncData, PhonemeData
from ..core.controller import LipSyncController
from ..core.mapping import PhonemeMapping, VisemeMapper
from ..visual_systems import get_visual_system
from ..utils import audio_utils


class AnimationEngine:
    """
    Main animation engine that converts phoneme data into Blender keyframes
    """
    
    def __init__(
        self,
        lipsync_data: LipSyncData,
        mapping: PhonemeMapping,
        controller: bpy.types.Object
    ):
        """
        Initialize animation engine
        
        Args:
            lipsync_data: Phoneme timing data
            mapping: Phoneme-to-visual mapping
            controller: LipKit controller object
        """
        self.lipsync_data = lipsync_data
        self.mapping = mapping
        self.controller = controller
        self.visual_system = get_visual_system(mapping.visual_system)
        
        if not self.visual_system:
            raise ValueError(f"Unknown visual system: {mapping.visual_system}")
    
    def generate(
        self,
        target_object: bpy.types.Object,
        start_frame: int = 1,
        fps: Optional[float] = None,
        use_nla: bool = False,
        action_name: str = "LipSync",
        use_easing: bool = False,
        easing_type: str = 'ease_in_out',
        easing_duration: float = 3.0
    ) -> Dict[str, any]:
        """
        Generate lip sync animation using controller + drivers
        
        Args:
            target_object: Object to animate (GP object, mesh with shape keys, etc.)
            start_frame: Starting frame number
            fps: Frames per second (defaults to scene fps)
            use_nla: Whether to create NLA strip instead of direct keyframes
            action_name: Name for the action/NLA strip
            use_easing: Apply easing to mouth transitions
            easing_type: Type of easing ('ease_in_out', 'ease_in', 'ease_out', 'smooth')
            easing_duration: Number of frames for easing transition
            
        Returns:
            Dictionary with generation results and statistics
        """
        if fps is None:
            fps = bpy.context.scene.render.fps
        
        # Step 1: Build phoneme-to-index mapping
        phoneme_to_index = self._build_phoneme_index_map()
        
        # Step 2: Generate keyframes on controller
        frame_data = {}
        for phoneme_data in self.lipsync_data.phonemes:
            frame = start_frame + audio_utils.time_to_frame(phoneme_data.start_time, fps)
            phoneme = phoneme_data.phoneme
            
            # Get index for this phoneme
            index = phoneme_to_index.get(phoneme, 0)
            frame_data[frame] = index
        
        # Apply easing if requested
        if use_easing:
            from ..utils.easing_utils import apply_easing_to_keyframes
            frame_data = apply_easing_to_keyframes(
                frame_data,
                easing_type=easing_type,
                easing_duration=easing_duration
            )
            print(f"✨ Applied {easing_type} easing over {easing_duration} frames")
        
        # Create action with keyframes
        if use_nla:
            action = LipSyncController.create_action(
                self.controller,
                action_name,
                frame_data
            )
            nla_strip = LipSyncController.create_nla_strip(
                self.controller,
                action,
                track_name="LipSync",
                start_frame=start_frame
            )
        else:
            # Direct keyframing
            for frame, index in sorted(frame_data.items()):
                LipSyncController.add_keyframe(
                    self.controller,
                    frame,
                    index,
                    interpolation='CONSTANT'
                )
        
        # Step 3: Create drivers on target object
        drivers_created = self._create_drivers(target_object, phoneme_to_index)
        
        # Step 4: Return results
        return {
            "success": True,
            "keyframes_created": len(frame_data),
            "drivers_created": len(drivers_created),
            "start_frame": start_frame,
            "end_frame": max(frame_data.keys()) if frame_data else start_frame,
            "phoneme_count": len(self.lipsync_data.phonemes),
            "unique_phonemes": len(set(phoneme_to_index.values())),
        }
    
    def _build_phoneme_index_map(self) -> Dict[str, int]:
        """
        Build mapping from phoneme strings to controller indices
        Uses the mapping configuration
        """
        phoneme_to_index = {}
        
        # If using viseme reduction, map phonemes to visemes first
        if self.mapping.phoneme_set == "arpabet":
            # Map ARPAbet phonemes to Preston Blair visemes
            for phoneme in self.lipsync_data.phonemes:
                viseme = VisemeMapper.phoneme_to_viseme(phoneme.phoneme)
                index = VisemeMapper.get_viseme_index(viseme)
                phoneme_to_index[phoneme.phoneme] = index
        else:
            # Use direct mapping from configuration
            for phoneme, mapping_data in self.mapping.mappings.items():
                index = mapping_data.get("index", 0)
                phoneme_to_index[phoneme] = index
        
        return phoneme_to_index
    
    def _create_drivers(
        self,
        target_object: bpy.types.Object,
        phoneme_to_index: Dict[str, int]
    ) -> List[bpy.types.FCurve]:
        """
        Create drivers on target object for all unique phoneme indices
        
        Returns:
            List of created FCurves
        """
        drivers = []
        
        # Get unique indices
        unique_indices = set(phoneme_to_index.values())
        
        # For each unique index, create a driver
        for index in unique_indices:
            # Find which phoneme(s) map to this index
            phonemes_for_index = [
                p for p, i in phoneme_to_index.items() if i == index
            ]
            
            if not phonemes_for_index:
                continue
            
            # Use first phoneme to get target name
            phoneme = phonemes_for_index[0]
            mapping_data = self.mapping.mappings.get(phoneme)
            
            if not mapping_data:
                continue
            
            target_name = mapping_data.get("target")
            
            if not target_name:
                continue
            
            # Create driver based on visual system type
            try:
                if self.mapping.visual_system == "gp_layer":
                    fcurve = self.visual_system.create_driver(
                        self.controller,
                        target_object,
                        index,
                        layer_name=target_name
                    )
                elif self.mapping.visual_system == "shape_key":
                    fcurve = self.visual_system.create_driver(
                        self.controller,
                        target_object,
                        index,
                        shape_key_name=target_name
                    )
                else:
                    print(f"Warning: Visual system {self.mapping.visual_system} not fully implemented")
                    continue
                
                drivers.append(fcurve)
            
            except Exception as e:
                print(f"Warning: Failed to create driver for {target_name}: {e}")
        
        return drivers
    
    def preview_at_time(self, time_seconds: float, fps: Optional[float] = None) -> str:
        """
        Get which phoneme is active at a given time
        
        Args:
            time_seconds: Time in seconds
            fps: Frames per second
            
        Returns:
            Phoneme string active at that time
        """
        phoneme_data = self.lipsync_data.get_phoneme_at_time(time_seconds)
        return phoneme_data.phoneme if phoneme_data else "REST"


def quick_generate(
    audio_path: str,
    target_object: bpy.types.Object,
    visual_system_type: str = "gp_layer",
    preset_name: str = "preston_blair",
    start_frame: int = 1,
    use_mock_data: bool = True
) -> Dict[str, any]:
    """
    Quick generation function for simple workflows
    
    Args:
        audio_path: Path to audio file
        target_object: Object to animate
        visual_system_type: Type of visual system ('gp_layer', 'shape_key')
        preset_name: Name of phoneme preset
        start_frame: Starting frame
        use_mock_data: If True, uses mock phoneme data (for testing without extraction tool)
        
    Returns:
        Generation results
    """
    # Import here to avoid circular imports
    from ..phoneme_providers import LocalPhonemeProvider
    from ..core.mapping import PresetManager
    
    # Extract phonemes
    provider = LocalPhonemeProvider()
    lipsync_data = provider.extract_phonemes(audio_path)
    
    # Create controller
    controller = LipSyncController.create_controller()
    
    # Load preset and create mapping
    preset_data = PresetManager.load_preset(preset_name)
    mapping = PhonemeMapping()
    mapping.name = preset_data.get("name", preset_name)
    mapping.phoneme_set = preset_data.get("phoneme_set", "preston_blair")
    mapping.visual_system = visual_system_type
    mapping.target_object = target_object.name
    
    # Auto-map based on visual system type
    if visual_system_type == "gp_layer" and target_object.type in ('GPENCIL', 'GREASEPENCIL'):
        # Try to auto-map layers
        for item in preset_data.get("mappings", []):
            phoneme = item["phoneme"]
            index = item["index"]
            
            # Look for layer with matching name
            layer_name = None
            for layer in target_object.data.layers:
                # Support both old (.info) and new (.name) attribute names
                current_layer_name = getattr(layer, 'name', None) or getattr(layer, 'info', None)
                if current_layer_name and phoneme.lower() in current_layer_name.lower():
                    layer_name = current_layer_name
                    break
            
            if layer_name:
                mapping.add_mapping(phoneme, index, layer_name)
    
    elif visual_system_type == "shape_key" and hasattr(target_object.data, 'shape_keys'):
        # Try to auto-map shape keys
        if target_object.data.shape_keys:
            for item in preset_data.get("mappings", []):
                phoneme = item["phoneme"]
                index = item["index"]
                
                # Look for shape key with matching name
                shape_key_name = None
                for key in target_object.data.shape_keys.key_blocks:
                    if phoneme.lower() in key.name.lower():
                        shape_key_name = key.name
                        break
                
                if shape_key_name:
                    mapping.add_mapping(phoneme, index, shape_key_name)
    
    # Generate animation
    engine = AnimationEngine(lipsync_data, mapping, controller)
    results = engine.generate(target_object, start_frame=start_frame)
    
    results["controller"] = controller
    results["mapping"] = mapping
    
    return results
