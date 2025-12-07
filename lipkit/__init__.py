"""
LipKit - Universal Lip Sync Extension for Blender
Supports both 2D (Grease Pencil) and 3D (Shape Keys) workflows
"""

bl_info = {
    "name": "LipKit",
    "author": "LipKit Team",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > LipKit",
    "description": "Universal lip sync system for 2D and 3D animations",
    "category": "Animation",
}

import bpy
from . import (
    preferences,
    properties,
    operators,
    ui,
)

# Module registration list
modules = [
    preferences,
    properties,
    operators,
    ui,
]


@bpy.app.handlers.persistent
def reset_analyzing_state(dummy):
    """Reset analyzing state when file loads - prevents stuck state bug"""
    for scene in bpy.data.scenes:
        if hasattr(scene, 'lipkit'):
            # If file was saved while analyzing, reset it
            if scene.lipkit.audio_analyzing:
                print("LipKit: Resetting stale 'analyzing' state from saved file")
                scene.lipkit.audio_analyzing = False
            
            # Also clear the generation flag
            if scene.lipkit.generation_in_progress:
                scene.lipkit.generation_in_progress = False


def register():
    """Register all addon classes and properties"""
    for module in modules:
        module.register()
    
    # Add load handler to reset analyzing state
    if reset_analyzing_state not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(reset_analyzing_state)
    
    print("LipKit: Registered successfully")


def unregister():
    """Unregister all addon classes and properties"""
    # Remove load handler
    if reset_analyzing_state in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(reset_analyzing_state)
    
    for module in reversed(modules):
        module.unregister()
    
    print("LipKit: Unregistered")


if __name__ == "__main__":
    register()
