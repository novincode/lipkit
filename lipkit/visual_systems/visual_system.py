"""
Visual system handlers - abstract base and implementations for different target types
"""

import bpy
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..core.controller import LipSyncController


class VisualSystem(ABC):
    """
    Abstract base class for visual systems
    Each system knows how to create drivers for its specific target type
    """
    
    @abstractmethod
    def create_driver(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_index: int,
        **kwargs
    ) -> bpy.types.FCurve:
        """
        Create a driver that activates this target when controller == phoneme_index
        
        Args:
            controller: LipKit controller object
            target_object: The object to animate
            phoneme_index: Index value that activates this target
            **kwargs: System-specific parameters
            
        Returns:
            Created FCurve with driver
        """
        pass
    
    @abstractmethod
    def validate_target(self, target_object: bpy.types.Object, **kwargs) -> bool:
        """Validate that target object is compatible with this system"""
        pass
    
    @property
    @abstractmethod
    def system_name(self) -> str:
        """Human-readable name of this visual system"""
        pass
    
    @property
    @abstractmethod
    def system_type(self) -> str:
        """Unique identifier for this system"""
        pass


class GreasePencilLayerSystem(VisualSystem):
    """
    Visual system for Grease Pencil layers
    Uses layer opacity to show/hide different mouth drawings
    """
    
    @property
    def system_name(self) -> str:
        return "Grease Pencil Layers"
    
    @property
    def system_type(self) -> str:
        return "gp_layer"
    
    def validate_target(self, target_object: bpy.types.Object, **kwargs) -> bool:
        """Check if object is a Grease Pencil object with the specified layer"""
        if target_object.type != 'GPENCIL':
            return False
        
        layer_name = kwargs.get("layer_name")
        if layer_name:
            return layer_name in target_object.data.layers
        
        return True
    
    def create_driver(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_index: int,
        **kwargs
    ) -> bpy.types.FCurve:
        """
        Create driver for GP layer opacity
        
        Args:
            layer_name: Name of the Grease Pencil layer
            blend_range: Optional range for smooth blending (default: 0 = instant)
        """
        layer_name = kwargs.get("layer_name")
        if not layer_name:
            raise ValueError("layer_name is required for GP layer system")
        
        blend_range = kwargs.get("blend_range", 0)
        
        # Get the layer
        gp_layer = target_object.data.layers.get(layer_name)
        if not gp_layer:
            raise ValueError(f"Layer '{layer_name}' not found in {target_object.name}")
        
        # Create driver on opacity
        data_path = f'layers["{layer_name}"].opacity'
        fcurve = target_object.data.driver_add(data_path)
        
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        
        # Add variable pointing to controller
        var = driver.variables.new()
        var.name = "phoneme"
        var.type = 'SINGLE_PROP'
        
        target = var.targets[0]
        target.id = controller
        target.data_path = f'["{LipSyncController.PROPERTY_NAME}"]'
        
        # Expression: return 1.0 when phoneme == index, else 0.0
        if blend_range > 0:
            # Smooth transition
            driver.expression = f"max(0.0, 1.0 - abs(phoneme - {phoneme_index}) / {blend_range})"
        else:
            # Instant switch
            driver.expression = f"1.0 if phoneme == {phoneme_index} else 0.0"
        
        return fcurve
    
    def setup_all_layers(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_mapping: Dict[str, str]
    ) -> List[bpy.types.FCurve]:
        """
        Set up drivers for all layers in the mapping
        
        Args:
            controller: Controller object
            target_object: GP object
            phoneme_mapping: Dict of phoneme_index -> layer_name
            
        Returns:
            List of created FCurves
        """
        fcurves = []
        
        for phoneme_idx_str, layer_name in phoneme_mapping.items():
            try:
                phoneme_idx = int(phoneme_idx_str)
                fcurve = self.create_driver(
                    controller,
                    target_object,
                    phoneme_idx,
                    layer_name=layer_name
                )
                fcurves.append(fcurve)
            except (ValueError, KeyError) as e:
                print(f"Warning: Failed to create driver for {layer_name}: {e}")
        
        return fcurves


class ShapeKeySystem(VisualSystem):
    """
    Visual system for 3D shape keys (blend shapes)
    """
    
    @property
    def system_name(self) -> str:
        return "Shape Keys (3D)"
    
    @property
    def system_type(self) -> str:
        return "shape_key"
    
    def validate_target(self, target_object: bpy.types.Object, **kwargs) -> bool:
        """Check if object has shape keys"""
        if not hasattr(target_object.data, 'shape_keys'):
            return False
        
        if not target_object.data.shape_keys:
            return False
        
        shape_key_name = kwargs.get("shape_key_name")
        if shape_key_name:
            return shape_key_name in target_object.data.shape_keys.key_blocks
        
        return True
    
    def create_driver(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_index: int,
        **kwargs
    ) -> bpy.types.FCurve:
        """
        Create driver for shape key value
        
        Args:
            shape_key_name: Name of the shape key
            blend_range: Optional range for smooth blending
        """
        shape_key_name = kwargs.get("shape_key_name")
        if not shape_key_name:
            raise ValueError("shape_key_name is required for shape key system")
        
        blend_range = kwargs.get("blend_range", 0)
        
        # Get shape key
        shape_keys = target_object.data.shape_keys
        if not shape_keys or shape_key_name not in shape_keys.key_blocks:
            raise ValueError(f"Shape key '{shape_key_name}' not found")
        
        # Create driver on shape key value
        data_path = f'key_blocks["{shape_key_name}"].value'
        fcurve = shape_keys.driver_add(data_path)
        
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        
        # Add variable
        var = driver.variables.new()
        var.name = "phoneme"
        var.type = 'SINGLE_PROP'
        
        target = var.targets[0]
        target.id = controller
        target.data_path = f'["{LipSyncController.PROPERTY_NAME}"]'
        
        # Expression
        if blend_range > 0:
            driver.expression = f"max(0.0, 1.0 - abs(phoneme - {phoneme_index}) / {blend_range})"
        else:
            driver.expression = f"1.0 if phoneme == {phoneme_index} else 0.0"
        
        return fcurve
    
    def setup_all_shape_keys(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_mapping: Dict[str, str]
    ) -> List[bpy.types.FCurve]:
        """Set up drivers for all shape keys in the mapping"""
        fcurves = []
        
        for phoneme_idx_str, shape_key_name in phoneme_mapping.items():
            try:
                phoneme_idx = int(phoneme_idx_str)
                fcurve = self.create_driver(
                    controller,
                    target_object,
                    phoneme_idx,
                    shape_key_name=shape_key_name
                )
                fcurves.append(fcurve)
            except (ValueError, KeyError) as e:
                print(f"Warning: Failed to create driver for {shape_key_name}: {e}")
        
        return fcurves


class ImageSequenceSystem(VisualSystem):
    """
    Visual system for image-based mouth shapes (sprite sheets)
    Changes material texture based on phoneme
    """
    
    @property
    def system_name(self) -> str:
        return "Image Sequence"
    
    @property
    def system_type(self) -> str:
        return "image_sequence"
    
    def validate_target(self, target_object: bpy.types.Object, **kwargs) -> bool:
        """Check if object has materials"""
        return len(target_object.material_slots) > 0
    
    def create_driver(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_index: int,
        **kwargs
    ) -> Optional[bpy.types.FCurve]:
        """
        Create driver for image texture switching
        
        This is more complex - typically would use a node setup with multiple images
        and drivers controlling mix factors
        """
        # TODO: Implement image sequence system
        # This requires a specific node setup in the material
        print("Image sequence system not yet fully implemented")
        return None


class GeometryNodesSystem(VisualSystem):
    """
    Visual system using Geometry Nodes attributes
    For advanced procedural mouth shapes
    """
    
    @property
    def system_name(self) -> str:
        return "Geometry Nodes"
    
    @property
    def system_type(self) -> str:
        return "geometry_nodes"
    
    def validate_target(self, target_object: bpy.types.Object, **kwargs) -> bool:
        """Check if object has geometry nodes modifier"""
        for modifier in target_object.modifiers:
            if modifier.type == 'NODES':
                return True
        return False
    
    def create_driver(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_index: int,
        **kwargs
    ) -> Optional[bpy.types.FCurve]:
        """
        Create driver for geometry nodes input
        
        Args:
            input_name: Name of the geometry nodes input
        """
        # TODO: Implement geometry nodes system
        print("Geometry Nodes system not yet fully implemented")
        return None


# Registry of available visual systems
VISUAL_SYSTEMS = {
    "gp_layer": GreasePencilLayerSystem(),
    "shape_key": ShapeKeySystem(),
    "image_sequence": ImageSequenceSystem(),
    "geometry_nodes": GeometryNodesSystem(),
}


def get_visual_system(system_type: str) -> Optional[VisualSystem]:
    """Get a visual system by type"""
    return VISUAL_SYSTEMS.get(system_type)


def register_visual_system(system_type: str, system: VisualSystem) -> None:
    """Register a custom visual system (extensibility!)"""
    VISUAL_SYSTEMS[system_type] = system


def get_available_systems() -> List[tuple]:
    """Get list of available systems for UI enum"""
    return [
        (key, system.system_name, system.system_name)
        for key, system in VISUAL_SYSTEMS.items()
    ]
