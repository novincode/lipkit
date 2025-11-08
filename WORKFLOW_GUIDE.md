# LipKit - Clean Workflow Guide

## Quick Reference

### New Operator Added
- **Button**: "Clean All" (in Controller panel)
- **Command**: `lipkit.clear_all_keyframes`
- **What it does**: Removes all keyframes from controller and all mapped layers

---

## Simplified Workflow

### Step 1: Create Controller
- Click **"Create Controller"** in main panel
- This creates a single empty object with `phoneme_index` property

### Step 2: Select Target Object
- Pick your mouth object (Grease Pencil with mouth shape layers)
- Each layer represents one mouth position (A, E, I, M, etc.)

### Step 3: Load Audio & Extract Phonemes
1. Select audio source (File or VSE)
2. Select phoneme engine (Rhubarb recommended)
3. Click **"Analyze Audio"**

### Step 4: Map Phonemes to Mouth Layers
1. Load a preset (Rhubarb, Preston Blair, etc.)
2. For each phoneme, click **"Select"** and choose the matching mouth layer
3. All phonemes must be mapped before generating

### Step 5: Generate Animation
- Click **"🚀 Generate Lip Sync"**
- This creates:
  - Keyframes on controller's `phoneme_index` property
  - Drivers on each mouth layer's opacity

### Step 6: Adjust Tweaks in Timeline
- Go to Timeline
- Adjust controller's `phoneme_index` keyframes as needed
- The drivers automatically update layer opacities

### Step 7: Start Over (if needed)
- Controller panel has two buttons:
  - **"Clear"** - just removes controller animation
  - **"Clean All"** - removes all keyframes and layer animation

---

## What This System Does

✅ **What Works:**
- Opacity tweaking of mouth layers (drivers on layer opacity)
- Keyframe animation on controller property
- Non-destructive NLA workflow
- Easy regeneration

❌ **What's Removed:**
- Target layer copying system (never worked properly)
- Complex 2D output layer setup
- Stroke data duplication

---

## Key Concepts

### Controller Object
- Single Empty object with `phoneme_index` property (0-100)
- Drives all mouth layer opacity values via drivers
- Clean timeline - only one animated property

### Drivers
- Each mouth layer has a driver reading from controller's `phoneme_index`
- Driver maps index values to opacity (0-1)
- Automatically updates layer visibility based on index

### Mouth Library
- Simple Grease Pencil object with multiple layers
- Each layer = one mouth shape
- Opacity tweaking shows/hides shapes

---

## Tips

1. **Layer Naming**: Name layers after phonemes (A, E, I, M, etc.) for auto-mapping
2. **Regeneration**: Use "Clean All" then "Generate" to rebuild animation
3. **Testing**: Scrub through timeline to preview animation
4. **Multiple Characters**: Create separate controller for each character
