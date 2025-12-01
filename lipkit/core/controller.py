"""
Controller system - the heart of LipKit's clean timeline approach
Uses a single custom property to control all lip sync targets via drivers
"""

import bpy
from typing import Optional, Dict, Any


class LipSyncController:
    """
    Manages the single controller object that drives all lip sync animations
    This keeps the timeline clean - only one animated property!
    """
    
    CONTROLLER_NAME_PREFIX = "LipKit_Controller"
    PROPERTY_NAME = "phoneme_index"
    
    @staticmethod
    def create_controller(
        name: Optional[str] = None,
        collection: Optional[bpy.types.Collection] = None
    ) -> bpy.types.Object:
        """
        Create a new lip sync controller object
        
        Args:
            name: Optional custom name for controller
            collection: Collection to link controller to (default: scene collection)
            
        Returns:
            The created controller object (Empty)
        """
        if name is None:
            name = LipSyncController._generate_unique_name()
        
        # Create an Empty object as the controller
        controller = bpy.data.objects.new(name, None)
        controller.empty_display_type = 'SPHERE'
        controller.empty_display_size = 0.1
        
        # Add custom property for phoneme index
        controller[LipSyncController.PROPERTY_NAME] = 0
        
        # Set property settings for better UX
        prop_manager = controller.id_properties_ui(LipSyncController.PROPERTY_NAME)
        prop_manager.update(
            min=0,
            max=100,
            soft_min=0,
            soft_max=50,
            description="Current phoneme index - controls all lip sync targets via drivers"
        )
        
        # Link to collection
        if collection is None:
            collection = bpy.context.scene.collection
        collection.objects.link(controller)
        
        # Add custom properties for metadata
        controller["lipkit_version"] = "0.1.0"
        controller["is_lipkit_controller"] = True
        
        return controller
    
    @staticmethod
    def _generate_unique_name() -> str:
        """Generate unique controller name"""
        base_name = LipSyncController.CONTROLLER_NAME_PREFIX
        counter = 1
        
        while base_name in bpy.data.objects:
            base_name = f"{LipSyncController.CONTROLLER_NAME_PREFIX}_{counter:03d}"
            counter += 1
        
        return base_name
    
    @staticmethod
    def get_controller(name: str) -> Optional[bpy.types.Object]:
        """Get controller object by name"""
        return bpy.data.objects.get(name)
    
    @staticmethod
    def find_controllers() -> list:
        """Find all LipKit controllers in the scene"""
        controllers = []
        for obj in bpy.data.objects:
            if obj.get("is_lipkit_controller", False):
                controllers.append(obj)
        return controllers
    
    @staticmethod
    def is_controller(obj: bpy.types.Object) -> bool:
        """Check if object is a LipKit controller"""
        return obj.get("is_lipkit_controller", False)
    
    @staticmethod
    def add_keyframe(
        controller: bpy.types.Object,
        frame: int,
        phoneme_index: int,
        interpolation: str = 'CONSTANT'
    ) -> None:
        """
        Add a keyframe to the controller
        
        Args:
            controller: Controller object
            frame: Frame number
            phoneme_index: Phoneme index value
            interpolation: Keyframe interpolation type (CONSTANT recommended)
        """
        # Set the value
        controller[LipSyncController.PROPERTY_NAME] = phoneme_index
        
        # Insert keyframe
        data_path = f'["{LipSyncController.PROPERTY_NAME}"]'
        controller.keyframe_insert(data_path=data_path, frame=frame)
        
        # Set interpolation (Blender 4.x and 5.x compatible)
        if controller.animation_data and controller.animation_data.action:
            action = controller.animation_data.action
            fcurve = None
            
            # Try to find the fcurve - handle both Blender 4 and 5 API
            try:
                # Blender 4.x and most 5.x versions
                if hasattr(action, 'fcurves'):
                    fcurve = action.fcurves.find(data_path)
            except (AttributeError, TypeError):
                pass
            
            # Fallback: iterate through fcurves if find() doesn't work
            if fcurve is None:
                try:
                    for fc in action.fcurves:
                        if fc.data_path == data_path:
                            fcurve = fc
                            break
                except (AttributeError, TypeError):
                    # action.fcurves not available - skip interpolation setting
                    pass
            
            if fcurve:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.co[0] == frame:
                        keyframe.interpolation = interpolation
                        break
    
    @staticmethod
    def clear_animation(controller: bpy.types.Object) -> None:
        """Clear all animation from controller (Blender 4.x and 5.x compatible)"""
        if controller.animation_data:
            try:
                if controller.animation_data.action:
                    bpy.data.actions.remove(controller.animation_data.action)
            except (AttributeError, ReferenceError):
                pass
            try:
                controller.animation_data_clear()
            except (AttributeError, ReferenceError):
                pass
    
    @staticmethod
    def get_phoneme_at_frame(controller: bpy.types.Object, frame: int) -> int:
        """Get the phoneme index at a specific frame"""
        # Set frame and evaluate
        bpy.context.scene.frame_set(frame)
        return controller.get(LipSyncController.PROPERTY_NAME, 0)
    
    @staticmethod
    def create_action(
        controller: bpy.types.Object,
        action_name: str,
        frame_data: Dict[int, int],
        interpolation: str = 'CONSTANT'
    ) -> bpy.types.Action:
        """
        Create an action with keyframes for the controller
        
        Args:
            controller: Controller object
            action_name: Name for the action
            frame_data: Dictionary mapping frame numbers to phoneme indices
            interpolation: Keyframe interpolation type
            
        Returns:
            Created action
        """
        # Create or get action
        action = bpy.data.actions.new(name=action_name)
        
        if not controller.animation_data:
            controller.animation_data_create()
        
        controller.animation_data.action = action
        
        # Add keyframes
        for frame, phoneme_idx in sorted(frame_data.items()):
            LipSyncController.add_keyframe(controller, frame, phoneme_idx, interpolation=interpolation)
        
        return action
    
    @staticmethod
    def create_nla_strip(
        controller: bpy.types.Object,
        action: bpy.types.Action,
        track_name: str = "LipSync",
        start_frame: int = 1
    ) -> bpy.types.NlaStrip:
        """
        Create an NLA strip from an action (non-destructive workflow)
        
        Args:
            controller: Controller object
            action: Action to convert to NLA strip
            track_name: Name for the NLA track
            start_frame: Start frame for the strip
            
        Returns:
            Created NLA strip
        """
        if not controller.animation_data:
            controller.animation_data_create()
        
        # Push action to NLA stack
        nla_tracks = controller.animation_data.nla_tracks
        
        # Find or create track
        track = None
        for t in nla_tracks:
            if t.name == track_name:
                track = t
                break
        
        if not track:
            track = nla_tracks.new()
            track.name = track_name
        
        # Create strip
        strip = track.strips.new(action.name, start_frame, action)
        
        return strip


def get_data_path_for_target(target_type: str, **kwargs) -> str:
    """
    Get the data path for different target types
    
    Args:
        target_type: Type of target ('gp_layer', 'shape_key', etc.)
        **kwargs: Additional parameters (layer_name, shape_key_name, etc.)
    
    Returns:
        Data path string for driver
    """
    if target_type == "gp_layer":
        # Grease Pencil layer opacity
        layer_name = kwargs.get("layer_name", "")
        return f'layers["{layer_name}"].opacity'
    
    elif target_type == "gp_layer_hide":
        # Grease Pencil layer hide
        layer_name = kwargs.get("layer_name", "")
        return f'layers["{layer_name}"].hide'
    
    elif target_type == "shape_key":
        # Shape key value
        shape_key_name = kwargs.get("shape_key_name", "")
        return f'key_blocks["{shape_key_name}"].value'
    
    elif target_type == "material":
        # Material node input value (simplified)
        return "diffuse_color"
    
    elif target_type == "bone":
        # Bone property
        bone_name = kwargs.get("bone_name", "")
        prop_name = kwargs.get("prop_name", "location")
        return f'pose.bones["{bone_name}"].{prop_name}'
    
    else:
        raise ValueError(f"Unknown target type: {target_type}")
