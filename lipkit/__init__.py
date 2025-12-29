"""
LipKit - Universal Lip Sync Extension for Blender
Supports both 2D (Grease Pencil) and 3D (Shape Keys) workflows

Copyright (C) 2024-2025 Shayan Moradi

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

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
