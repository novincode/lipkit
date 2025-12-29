"""
Addon preferences for LipKit

Copyright (C) 2024-2025 Shayan Moradi
SPDX-License-Identifier: GPL-3.0-or-later
"""

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty


# Store the package name at module level for reliable access
_package_name = __package__


class PreferencesDefaults:
    """Fallback preferences object when addon prefs can't be loaded"""
    def __init__(self):
        self.use_cache = True
        self.local_tool_path = ""
        self.rhubarb_mode = "auto"
        self.debug_mode = False
    
    def __getattr__(self, name):
        """Return sensible defaults for any missing attributes"""
        defaults = {
            'rhubarb_mode': 'auto',
            'use_cache': True,
            'local_tool_path': '',
            'debug_mode': False,
        }
        return defaults.get(name, None)


class LipKitPreferences(bpy.types.AddonPreferences):
    # Use __package__ for proper extension namespace support
    bl_idname = _package_name
    
    # Rhubarb Setup Mode
    rhubarb_mode: EnumProperty(
        name="Rhubarb Setup",
        description="How to manage Rhubarb installation",
        items=[
            ('auto', 'Auto (Recommended)', 'Automatically download and manage Rhubarb'),
            ('manual', 'Manual', 'Manually select Rhubarb folder'),
        ],
        default='auto'
    )
    
    # Local Tool Settings
    local_tool_path: StringProperty(
        name="Local Tool Path",
        description="Path to phoneme extraction tool (e.g., Rhubarb)",
        subtype='FILE_PATH',
        default=""
    )
    
    use_cache: BoolProperty(
        name="Use Cache",
        description="Cache phoneme extraction results to speed up re-generation",
        default=True
    )
    
    # Debug Settings
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Enable debug logging",
        default=False
    )
    
    def draw(self, context):
        layout = self.layout
        
        # Rhubarb Setup Section
        box = layout.box()
        box.label(text="Rhubarb Lip Sync Setup", icon='FILE_SOUND')
        box.prop(self, "rhubarb_mode", expand=True)
        
        if self.rhubarb_mode == 'auto':
            # Auto mode
            box2 = box.box()
            row = box2.row(align=True)
            row.scale_y = 1.5
            row.operator("lipkit.download_rhubarb", text="📥 Download Rhubarb", icon='IMPORT')
            
            box2.label(text="Rhubarb will be automatically downloaded and", icon='INFO')
            box2.label(text="installed to your Blender config folder", icon='BLANK1')
            
            # Check if already installed
            from .utils.rhubarb_manager import get_rhubarb_executable
            exe = get_rhubarb_executable()
            if exe:
                box2.label(text=f"✅ Installed: {exe}", icon='CHECKMARK')
            else:
                box2.label(text="Not installed yet. Click Download button.", icon='ERROR')
        
        else:
            # Manual mode
            box2 = box.box()
            box2.prop(self, "local_tool_path")
            box2.operator("lipkit.select_rhubarb_manual", text="📁 Select Folder", icon='FILE_FOLDER')
            
            if self.local_tool_path:
                box2.label(text=f"Path set to: {self.local_tool_path}", icon='CHECKMARK')
        
        box.prop(self, "use_cache")
        
        layout.separator()
        
        # Debug
        box = layout.box()
        box.prop(self, "debug_mode")


def get_preferences(context=None):
    """Get addon preferences - works with both addon and extension formats"""
    if context is None:
        context = bpy.context
    
    try:
        addons = context.preferences.addons
        
        # Try with the actual package name first (extension format)
        if _package_name in addons:
            prefs = addons[_package_name].preferences
            if prefs is not None:
                return prefs
        
        # Fallback: Try direct name
        if "lipkit" in addons:
            prefs = addons["lipkit"].preferences
            if prefs is not None:
                return prefs
        
        # Try with package name pattern if it's an extension (bl_ext.repo.lipkit)
        for addon_name in addons.keys():
            if "lipkit" in addon_name.lower():
                prefs = addons[addon_name].preferences
                if prefs is not None:
                    return prefs
        
        # If not found, return defaults
        print("⚠️ LipKit preferences not found in Blender - using defaults")
        return PreferencesDefaults()
    
    except Exception as e:
        print(f"⚠️ Error getting preferences ({e}) - using defaults")
        # Return fallback with defaults
        return PreferencesDefaults()


def register():
    bpy.utils.register_class(LipKitPreferences)


def unregister():
    bpy.utils.unregister_class(LipKitPreferences)
