# 🎯 LipKit - How to Use

The extension is now working! Here's the complete workflow:

## Quick Setup (2 minutes)

### 1. Create Your Character
- **For 2D (Grease Pencil)**:
  - Create a Grease Pencil object
  - Add layers named like: `Mouth_AH`, `Mouth_EE`, `Mouth_M`, etc.
  - Draw 9 mouth shapes (Preston Blair preset)

- **For 3D (Shape Keys)**:
  - Select your mesh
  - Add shape keys: Object Data Properties → Shape Keys
  - Name them: `AH`, `EE`, `OH`, `M`, `F`, `L`, `S`, `OO`, `REST`
  - Create different shapes for each

### 2. Add Audio
- Put an audio file in your Video Sequence Editor (VSE)
  - Go to Video Editing workspace
  - Add → Sound → Select your audio file
  
  OR use File source:
  - Set Audio Source to "File"
  - Select your .wav/.mp3

### 3. Configure LipKit
1. Open LipKit panel (N key → LipKit tab)
2. **Phoneme Engine**: Select "FREE" (local, no setup needed)
3. **Audio Source**: Select VSE Strip or File
4. **Visual System**: Choose "Grease Pencil Layers" or "Shape Keys"
5. **Target Object**: Select your mouth object

### 4. Generate!
1. Click **"Analyze Audio"** ← Extracts mouth shapes from audio
2. **Phoneme Preset**: Keep "Preston Blair" (9 shapes)
3. Click **"Load Preset"** ← Loads the 9 shapes
4. Click **"Auto-Map Targets"** ← Matches shapes to your layers/keys
5. Click **"🚀 Generate Lip Sync"** ← Creates the animation!

## What Happens Next
- A controller object is created with one animated property
- All your mouth shapes are driven by this property
- Timeline stays clean (no clutter)
- Press Space to playback

## Troubleshooting

**"No phoneme data" message**
- Make sure you clicked "Analyze Audio"
- Check that audio source is correct
- Check system console for errors (Window → Toggle System Console)

**"No mappings" message**
- Click "Load Preset" first
- Then click "Auto-Map Targets"

**"Auto-map didn't find anything"**
- Your layer/shape key names might not match
- Manually set target names in the Mapping panel
- Example: For `Mouth_AH` layer, set `AH` mapping to target `Mouth_AH`

**Audio not loading**
- For VSE: Make sure sound strip exists in Video Editor
- For File: Use .wav or .mp3 files
- Check the file path is correct

## Next Steps

### Install Real Phoneme Engine (Optional)
For better accuracy, install Rhubarb Lip Sync:
- Download: https://github.com/DanielSWolf/rhubarb-lip-sync
- Set path in LipKit preferences
- Phoneme extraction will be more accurate

### Customize Phoneme Preset
Edit `lipkit/presets/preston_blair.json` to add more shapes or change mappings

### Use Multiple Dialogues
- Create NLA strips for each dialogue
- Layer animations on top of base rig

---

**That's it! You're ready to lip sync.** 🎬
