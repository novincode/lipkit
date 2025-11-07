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


def register():
    """Register all addon classes and properties"""
    for module in modules:
        module.register()
    
    print("LipKit: Registered successfully")


def unregister():
    """Unregister all addon classes and properties"""
    for module in reversed(modules):
        module.unregister()
    
    print("LipKit: Unregistered")


if __name__ == "__main__":
    register()
