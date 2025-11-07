# 🚀 LipKit - Setup Instructions

## Installation Status: ✅ Extension Recognized

Blender is now recognizing LipKit in your User Repository. Now we need to get it actually working.

## If LipKit Panel Doesn't Show:

### Step 1: Check System Console
1. Open Blender
2. **Window → Toggle System Console** (macOS: run Blender from terminal)
3. Look for errors that start with `lipkit`
4. Screenshot errors and share them

### Step 2: Run Diagnostic
1. In Blender, go to **Scripting** workspace
2. Open file: `lipkit/TEST_IN_BLENDER.py`
3. Run the script (Alt+P or click play button)
4. Check the console output

### Step 3: Manual Property Test
In Blender's **Python Console**, run:

```python
import bpy
import lipkit

# Check if scene properties exist
try:
    props = bpy.context.scene.lipkit
    print(f"✅ Properties loaded: {props}")
except AttributeError as e:
    print(f"❌ Properties error: {e}")
    print("\nTrying manual registration...")
    lipkit.register()
    print("Registered. Try pressing F3 → 'Reload Scripts'")
```

### Step 4: Reload Scripts
If properties aren't showing:
1. Press **F3** in Blender
2. Type "Reload Scripts"
3. Hit Enter
4. Press N to open sidebar

## If Still Not Working:

**The Problem**: Scene properties (`lipkit`) might not be initialized.

**The Solution**: Edit `lipkit/properties.py` and ensure it has this at the end:

```python
bpy.types.Scene.lipkit = PointerProperty(type=LipKitSceneProperties)
```

## Complete Setup Process

1. **Install locally**:
   - In Blender: Edit → Preferences → File Paths → Script Directories
   - Add: `/Users/shayanmoradi/Desktop/Work` (parent of lipsync-blender)
   - Add `/Users/shayanmoradi/Desktop/Work/lipsync-blender` as a local repository

2. **Enable addon**:
   - Edit → Preferences → Add-ons
   - Search: "LipKit"
   - Enable it (checkbox)

3. **Check for errors**:
   - Window → Toggle System Console
   - Any red text?

4. **Reload if needed**:
   - F3 → "Reload Scripts"
   - Or restart Blender completely

5. **Open N-panel**:
   - Press N in 3D viewport
   - Look for "LipKit" tab

## Debug: Check if Extension is Actually Loaded

```python
# In Blender Python console
import sys

# Check if lipkit path is in sys.path
for p in sys.path:
    if 'lipkit' in p or 'lipsync' in p:
        print(f"✓ Found: {p}")

# Try to import
try:
    from lipkit import bl_info
    print(f"✅ Import successful: {bl_info}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
```

## Expected Result

When working correctly:
- ✅ Extension shows in Preferences → Get Extensions
- ✅ Can enable it (checkbox appears)
- ✅ Panel appears when pressing N in viewport
- ✅ `import lipkit` works in Python console
- ✅ No red errors in system console

## If All Else Fails

Try the **nuclear option**:

```bash
# Delete the symlink/extension
rm -rf ~/Library/Application\ Support/Blender/4.5/extensions/user_default/lipkit

# Restart Blender

# Then re-add via local repository:
# Preferences → File Paths → Script Directories
# Add the parent folder, restart Blender
```

---

**Need help?** Check the system console for exact error messages.
