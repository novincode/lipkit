# Test script - paste into Blender's Python console to verify fix

import bpy

# Test 1: Preferences loading
print("Test 1: Preferences...")
try:
    from lipkit.preferences import get_preferences
    prefs = get_preferences()
    print(f"✅ Preferences loaded: {prefs}")
except Exception as e:
    print(f"❌ Preferences failed: {e}")

# Test 2: Scene properties exist
print("\nTest 2: Scene properties...")
try:
    props = bpy.context.scene.lipkit
    print(f"✅ Scene properties loaded: {props}")
    print(f"   - phoneme_preset: {props.phoneme_preset}")
    print(f"   - phoneme_mappings: {len(props.phoneme_mappings)} items")
except Exception as e:
    print(f"❌ Scene properties failed: {e}")

# Test 3: Load preset
print("\nTest 3: Loading preset...")
try:
    bpy.ops.lipkit.load_preset()
    print(f"✅ Preset loaded")
    print(f"   - Mappings: {len(props.phoneme_mappings)}")
except Exception as e:
    print(f"❌ Load preset failed: {e}")

print("\n" + "="*50)
print("If all tests pass, you can:")
print("1. Select a Grease Pencil or mesh object (with shape keys)")
print("2. Select audio (VSE or File)")
print("3. Click 'Analyze Audio'")
print("4. Click 'Auto-Map Targets'")
print("5. Click 'Generate Lip Sync'")
print("="*50)
