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
        output_gp_object: Optional[bpy.types.Object] = None,
        output_gp_layer: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Generate lip sync animation
        
        Args:
            target_object: Object to animate (GP object, mesh with shape keys, etc.)
            start_frame: Starting frame number
            fps: Frames per second (defaults to scene fps)
            use_nla: Whether to create NLA strip instead of direct keyframes
            action_name: Name for the action/NLA strip
            output_gp_object: Optional GP object for 2D output layer animation
            output_gp_layer: Optional GP layer name for 2D output
            
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
            for frame, index in frame_data.items():
                LipSyncController.add_keyframe(
                    self.controller,
                    frame,
                    index,
                    interpolation='CONSTANT'
                )
        
        # Step 3: Create drivers on target object OR generate 2D keyframes
        drivers_created = 0
        gp_keyframes_created = 0
        
        if output_gp_object and output_gp_layer:
            # 2D Output Mode: Generate keyframes directly on output GP layer
            gp_keyframes_created = self._generate_gp_2d_keyframes(
                output_gp_object,
                output_gp_layer,
                phoneme_to_index,
                frame_data,
                target_object
            )
        else:
            # 3D Mode: Create drivers on target object
            drivers_created = len(self._create_drivers(target_object, phoneme_to_index))
        
        # Step 4: Return results
        return {
            "success": True,
            "keyframes_created": len(frame_data),
            "drivers_created": drivers_created,
            "gp_keyframes_created": gp_keyframes_created,
            "start_frame": start_frame,
            "end_frame": max(frame_data.keys()) if frame_data else start_frame,
            "phoneme_count": len(self.lipsync_data.phonemes),
            "unique_phonemes": len(set(phoneme_to_index.values())),
            "output_mode": "2d_gp" if gp_keyframes_created > 0 else "3d_drivers",
        }
    
    def _generate_gp_2d_keyframes(
        self,
        output_gp_object: bpy.types.Object,
        output_gp_layer: str,
        phoneme_to_index: Dict[str, int],
        frame_data: Dict[int, int],
        input_target_object: bpy.types.Object
    ) -> int:
        """
        Generate keyframes by COPYING stroke data from mouth shape library to target layer
        
        Workflow:
        1. input_target_object = "MOUTH" object with layers A, B, C, etc (mouth shape library)
        2. output_gp_object = "CHARACTER" object (main character)
        3. output_gp_layer = "Mouth" layer in CHARACTER object (where animation appears)
        4. For each frame, copy the correct mouth shape from library to character's mouth layer
        
        Args:
            output_gp_object: CHARACTER object (receives the animation)
            output_gp_layer: Target layer name in CHARACTER (e.g., "Mouth")
            phoneme_to_index: Mapping of phoneme to index values
            frame_data: Frame to index mapping (frame -> phoneme_index)
            input_target_object: MOUTH library object (source of mouth shapes)
            
        Returns:
            Number of keyframes created
        """
        # Validate output GP object
        if output_gp_object.type not in ('GPENCIL', 'GREASEPENCIL'):
            print(f"ERROR: {output_gp_object.name} is not a Grease Pencil object")
            return 0
        
        # Get or create the target layer in CHARACTER object
        target_layer = None
        if hasattr(output_gp_object.data, 'layers'):
            for layer in output_gp_object.data.layers:
                layer_name = getattr(layer, 'name', None) or getattr(layer, 'info', None)
                if layer_name == output_gp_layer:
                    target_layer = layer
                    break
            
            if not target_layer:
                print(f"Creating new layer '{output_gp_layer}' in {output_gp_object.name}")
                target_layer = output_gp_object.data.layers.new(output_gp_layer)
        else:
            print(f"ERROR: {output_gp_object.name} has no layers attribute")
            return 0
        
        if not target_layer:
            print(f"ERROR: Failed to get or create layer '{output_gp_layer}'")
            return 0
        
        # Build reverse mapping: index -> source layer name
        index_to_layer = {}
        for phoneme, mapping_data in self.mapping.mappings.items():
            index = mapping_data.get("index", 0)
            layer_name = mapping_data.get("target")
            if layer_name:
                index_to_layer[index] = layer_name
        
        if not index_to_layer:
            print("ERROR: No phoneme mappings found")
            return 0
        
        print(f"🎨 2D Animation Mode:")
        print(f"  Library: {input_target_object.name} ({len(index_to_layer)} mouth shapes)")
        print(f"  Target: {output_gp_object.name} → Layer '{output_gp_layer}'")
        
        keyframes_created = 0
        
        # Clear existing frames in target layer (optional - user might want to keep)
        # target_layer.frames.clear()
        
        # For each frame in the animation
        for frame, phoneme_index in sorted(frame_data.items()):
            # Find which mouth shape to use
            source_layer_name = index_to_layer.get(phoneme_index)
            
            if not source_layer_name:
                print(f"⚠️  Frame {frame}: No layer mapped for index {phoneme_index}")
                continue
            
            # Find the source layer in the MOUTH library object
            source_layer = None
            if hasattr(input_target_object.data, 'layers'):
                for layer in input_target_object.data.layers:
                    current_layer_name = getattr(layer, 'name', None) or getattr(layer, 'info', None)
                    if current_layer_name == source_layer_name:
                        source_layer = layer
                        break
            
            if not source_layer:
                print(f"⚠️  Frame {frame}: Source layer '{source_layer_name}' not found in {input_target_object.name}")
                continue
            
            # Copy stroke data from source layer to target layer at this frame
            success = self._copy_gp_frame(
                source_layer=source_layer,
                target_layer=target_layer,
                target_frame=frame
            )
            
            if success:
                keyframes_created += 1
            else:
                print(f"⚠️  Frame {frame}: Failed to copy from '{source_layer_name}'")
        
        print(f"✅ Created {keyframes_created} keyframes on {output_gp_object.name}.{output_gp_layer}")
        
        return keyframes_created
    
    def _copy_gp_frame(
        self,
        source_layer,
        target_layer,
        target_frame: int
    ) -> bool:
        """
        Copy stroke data from source layer to target layer at specific frame
        
        Args:
            source_layer: Source GP layer (from mouth library)
            target_layer: Target GP layer (in character)
            target_frame: Frame number to create/update
            
        Returns:
            True if successful
        """
        try:
            # Get the first frame from source layer (assuming it's a static drawing)
            # Or get the active frame - adjust based on your setup
            source_frame = None
            if hasattr(source_layer, 'frames') and len(source_layer.frames) > 0:
                # Use the first frame as the mouth shape template
                source_frame = source_layer.frames[0]
            elif hasattr(source_layer, 'active_frame'):
                source_frame = source_layer.active_frame
            
            if not source_frame:
                return False
            
            # Create or get target frame
            target_frame_obj = None
            
            # Check if frame already exists
            if hasattr(target_layer, 'frames'):
                for frame in target_layer.frames:
                    if frame.frame_number == target_frame:
                        target_frame_obj = frame
                        # Clear existing strokes
                        target_frame_obj.strokes.clear()
                        break
                
                # Create new frame if doesn't exist
                if not target_frame_obj:
                    target_frame_obj = target_layer.frames.new(target_frame)
            else:
                return False
            
            # Copy all strokes from source to target
            for source_stroke in source_frame.strokes:
                # Create new stroke in target
                target_stroke = target_frame_obj.strokes.new()
                
                # Copy stroke properties
                target_stroke.line_width = source_stroke.line_width
                if hasattr(source_stroke, 'material_index'):
                    target_stroke.material_index = source_stroke.material_index
                
                # Copy points
                target_stroke.points.add(len(source_stroke.points))
                for i, source_point in enumerate(source_stroke.points):
                    target_point = target_stroke.points[i]
                    target_point.co = source_point.co.copy()
                    if hasattr(source_point, 'pressure'):
                        target_point.pressure = source_point.pressure
                    if hasattr(source_point, 'strength'):
                        target_point.strength = source_point.strength
            
            return True
            
        except Exception as e:
            print(f"ERROR copying GP frame: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
