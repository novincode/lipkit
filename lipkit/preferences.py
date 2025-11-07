"""
Addon preferences for LipKit
"""

import bpy
from bpy.props import StringProperty, BoolProperty


class LipKitPreferences(bpy.types.AddonPreferences):
    bl_idname = "lipkit"
    
    # Local Tool Settings
    local_tool_path: StringProperty(
        name="Local Tool Path",
        description="Path to phoneme extraction tool (e.g., Rhubarb, Allosaurus)",
        subtype='FILE_PATH',
        default=""
    )
    
    use_cache: BoolProperty(
        name="Use Cache",
        description="Cache phoneme extraction results to speed up re-generation",
        default=True
    )
    
    # API Settings
    api_key: StringProperty(
        name="API Key",
        description="API key for LipKit Cloud service",
        default="",
        subtype='PASSWORD'
    )
    
    api_endpoint: StringProperty(
        name="API Endpoint",
        description="Cloud API endpoint URL",
        default="https://api.lipkit.dev/v1/phonemes"
    )
    
    # Custom API
    custom_api_endpoint: StringProperty(
        name="Custom API Endpoint",
        description="Your own phoneme extraction API endpoint",
        default=""
    )
    
    custom_api_key: StringProperty(
        name="Custom API Key",
        description="API key for custom endpoint",
        default="",
        subtype='PASSWORD'
    )
    
    # Debug Settings
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Enable debug logging",
        default=False
    )
    
    def draw(self, context):
        layout = self.layout
        
        # Local Tool Section
        box = layout.box()
        box.label(text="Local Phoneme Extraction", icon='FILE_SOUND')
        box.prop(self, "local_tool_path")
        box.prop(self, "use_cache")
        box.label(text="Install Rhubarb or Allosaurus for local extraction", icon='INFO')
        
        layout.separator()
        
        # Cloud API Section
        box = layout.box()
        box.label(text="LipKit Cloud API (Premium)", icon='WORLD')
        box.prop(self, "api_key")
        box.prop(self, "api_endpoint")
        
        if not self.api_key:
            box.label(text="Get API key at lipkit.dev", icon='URL')
        
        layout.separator()
        
        # Custom API Section
        box = layout.box()
        box.label(text="Custom API", icon='SCRIPT')
        box.prop(self, "custom_api_endpoint")
        box.prop(self, "custom_api_key")
        
        layout.separator()
        
        # Debug
        box = layout.box()
        box.prop(self, "debug_mode")


def get_preferences(context=None) -> LipKitPreferences:
    """Get addon preferences - works with both addon and extension formats"""
    if context is None:
        context = bpy.context
    
    # Try both "lipkit" and full module name
    addons = context.preferences.addons
    
    # Try direct name first
    if "lipkit" in addons:
        return addons["lipkit"].preferences
    
    # Try with package name if it's an extension
    for addon_name in addons.keys():
        if "lipkit" in addon_name.lower():
            return addons[addon_name].preferences
    
    # If not found, return defaults (non-blocking)
    print(f"⚠ LipKit preferences not found. Available addons: {list(addons.keys())}")
    return LipKitPreferences()


def register():
    bpy.utils.register_class(LipKitPreferences)


def unregister():
    bpy.utils.unregister_class(LipKitPreferences)
