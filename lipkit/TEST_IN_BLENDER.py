#!/usr/bin/env python3
"""
Diagnostic script for LipKit - run in Blender's Python console
"""

import bpy
import sys

print("\n" + "="*60)
print("LipKit Diagnostic Report")
print("="*60)

# Check if lipkit is importable
try:
    import lipkit
    print("✅ lipkit module loaded")
    print(f"   Version: {lipkit.bl_info['version']}")
except Exception as e:
    print(f"❌ lipkit import failed: {e}")

# Check if scene properties exist
try:
    props = bpy.context.scene.lipkit
    print("✅ bpy.context.scene.lipkit properties exist")
except:
    print("❌ bpy.context.scene.lipkit NOT FOUND")
    print("   Panels won't work without this!")

# Check registered classes
print("\n✓ Registered panel classes:")
for cls in dir(bpy.types):
    if "LIPKIT" in cls and "PT" in cls:
        print(f"   - {cls}")

# Check if preferences exist
try:
    prefs = bpy.context.preferences.addons.get('lipkit')
    if prefs:
        print("\n✅ LipKit addon found in preferences")
        print(f"   Enabled: {prefs.enabled if hasattr(prefs, 'enabled') else 'N/A'}")
    else:
        print("\n❌ LipKit addon NOT in preferences")
except Exception as e:
    print(f"❌ Error checking preferences: {e}")

print("\n" + "="*60)
print("If you see '❌ bpy.context.scene.lipkit NOT FOUND',")
print("the panel won't work. Try:")
print("  1. Restart Blender completely")
print("  2. Make sure lipkit is ENABLED in Preferences")
print("  3. Check system console for errors")
print("="*60 + "\n")
