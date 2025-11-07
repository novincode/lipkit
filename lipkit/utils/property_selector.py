"""
Utilities for selecting animation targets (shape keys or GP layers)
"""

import bpy
from typing import List, Tuple


def get_shape_keys(obj: bpy.types.Object) -> List[str]:
    """Get list of shape key names from mesh object"""
    if not obj or obj.type != 'MESH':
        return []
    
    shape_keys = obj.data.shape_keys
    if not shape_keys or not shape_keys.key_blocks:
        return []
    
    # Skip "Basis" shape key
    return [key.name for key in shape_keys.key_blocks if key.name != "Basis"]


def get_gp_layers(obj: bpy.types.Object) -> List[str]:
    """Get list of layer names from Grease Pencil object"""
    if not obj or obj.type != 'GPENCIL':
        return []
    
    if not hasattr(obj.data, 'layers'):
        return []
    
    return [layer.info for layer in obj.data.layers]


def get_shape_key_items(scene, context) -> List[Tuple[str, str, str]]:
    """Get shape key items for EnumProperty"""
    props = scene.lipkit
    
    if not props.target_object:
        return [('NONE', 'None', 'Select an object first')]
    
    shape_keys = get_shape_keys(props.target_object)
    
    if not shape_keys:
        return [('NONE', 'None', 'No shape keys available')]
    
    items = []
    for key_name in shape_keys:
        items.append((key_name, key_name, f"Shape Key: {key_name}"))
    
    return items


def get_gp_layer_items(scene, context) -> List[Tuple[str, str, str]]:
    """Get GP layer items for EnumProperty"""
    props = scene.lipkit
    
    if not props.target_object:
        return [('NONE', 'None', 'Select an object first')]
    
    layers = get_gp_layers(props.target_object)
    
    if not layers:
        return [('NONE', 'None', 'No layers available')]
    
    items = []
    for layer_name in layers:
        items.append((layer_name, layer_name, f"GP Layer: {layer_name}"))
    
    return items


def get_available_targets(context) -> List[Tuple[str, str, str]]:
    """
    Get available target objects based on visual system setting
    """
    props = context.scene.lipkit
    items = [('NONE', 'None', 'No target object')]
    
    if props.visual_system == 'shape_key':
        # List mesh objects with shape keys
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                has_sk = hasattr(obj.data, 'shape_keys') and obj.data.shape_keys and obj.data.shape_keys.key_blocks
                if has_sk and len(obj.data.shape_keys.key_blocks) > 1:  # More than just Basis
                    items.append((obj.name, obj.name, f"Mesh: {obj.name}"))
    
    elif props.visual_system == 'gp_layer':
        # List GP objects with layers
        for obj in bpy.data.objects:
            if obj.type == 'GPENCIL':
                has_layers = hasattr(obj.data, 'layers') and len(obj.data.layers) > 0
                if has_layers:
                    items.append((obj.name, obj.name, f"GP Object: {obj.name}"))
    
    return items
