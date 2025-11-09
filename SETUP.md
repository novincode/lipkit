# 🎬 LipKit Setup Guide

Get LipKit working in Blender with real phoneme extraction.

---

## Step 1: Install LipKit Extension

1. Download or clone this repository
2. In Blender: **Edit → Preferences → Get Extensions**
3. Click the folder icon → Select the `lipkit` folder
4. Enable **"LipKit"** in the Extensions list

---

## Step 2: Setup Rhubarb (Choose One)

### Option A: Auto-Download (Recommended, 2 minutes)

1. Open Blender Preferences → Extensions → LipKit
2. In "Rhubarb Setup" section, select **"Auto"**
3. Click **"📥 Download Rhubarb"**
4. Wait 1-2 minutes for download and extraction
5. You should see: **"✅ Installed: /path/to/rhubarb"**

LipKit automatically:
- Downloads the latest Rhubarb release for your OS (macOS/Windows/Linux)
- Extracts it to a safe location
- Verifies the installation

### Option B: Manual Setup (If Auto Fails)

1. Go to: https://github.com/DanielSWolf/rhubarb-lip-sync/releases
2. Download the latest version for your OS
3. Extract the ZIP file somewhere permanent
4. In Blender Preferences → LipKit, select **"Manual"**
5. Click **"📁 Select Rhubarb Folder"**
6. Navigate to the extracted folder (should contain the `rhubarb` executable)
7. Select it and click OK

---

## Step 3: Verify Installation

1. In Blender, open the LipKit panel (Press **N** → "LipKit" tab)
2. Check the status indicator:
   - ✅ **Ready** = Everything is working
   - ❌ **Not configured** = Rhubarb not found, try manual setup

---

## Step 4: Create Your Mouth Shapes

### For 2D (Grease Pencil):

1. Create a new Grease Pencil object
2. Create **9 drawing layers** (or more) with these names:
   - `X` - REST (mouth closed)
   - `A` - AH (father, hot)
   - `B` - M/B/P (lips together)
   - `C` - EE (see, tree)
   - `D` - L/D/T (tongue up)
   - `E` - OH (go, show)
   - `F` - F/V (lip to teeth)
   - `G` - K/G (tongue back)
   - `H` - OO (food, you)

3. Draw a different mouth shape on each layer

**Tips:**
- Use consistent art style across layers
- Layer names are case-insensitive: `Mouth_A` or `mouth_a` work too
- You can add extra layers (won't break anything)

### For 3D (Shape Keys):

1. Select your character's head mesh
2. Add shape keys in **Object Data Properties → Shape Keys**
3. Create keys with these names: `X`, `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`
4. Model different mouth shapes for each key

---

## Step 5: Generate Lip Sync

1. **Load audio:**
   - Add audio to VSE, OR
   - Use "File" source in LipKit panel

2. **Analyze:**
   - Click **"Analyze Audio"**
   - Rhubarb extracts real phonemes from your audio

3. **Setup target:**
   - Visual System: Choose "Grease Pencil Layers" or "Shape Keys"
   - Target Object: Select your mouth object
   - Preset: Select "Rhubarb (A-H, X)"
   - Click **"Load Preset"**

4. **Map phonemes:**
   - Click **"Auto-Map Targets"** (matches names automatically)
   - Or manually select shapes for each phoneme

5. **Generate:**
   - Click **"Create Controller"** (if doesn't exist)
   - Click **"🚀 Generate Lip Sync"**

**Done!** Press **Space** to play your animation.

---

## Troubleshooting

### "Rhubarb not found"
- **Auto mode failed?** Try Manual mode:
  - Download from GitHub releases manually
  - Set to Manual mode in Preferences
  - Click "Select Rhubarb Folder" and navigate to it

- **On macOS:** First time you use Rhubarb, you might see a security warning
  - Right-click the `rhubarb` executable
  - Click "Open"
  - Approve the security dialog

### "Auto-mapped 0 targets"
- Layer/shape key names don't match
- Verify they contain: `X`, `A`, `B`, `C`, `D`, `E`, `F`, `G`, or `H`
- Names are case-insensitive: `Mouth_A` = `mouth_a` = `A`

### "No phoneme data extracted"
- Click **"Analyze Audio"** first (blue progress bar should appear)
- Check your audio file format:
  - ✅ Supported: MP3, WAV, M4A, OGG, FLAC
  - Auto-converts to WAV for Rhubarb
  - Requires ffmpeg for MP3/M4A (run: `brew install ffmpeg` on macOS)

### "Animation doesn't play"
- Verify **Controller** object exists
- Check **Graph Editor → Drivers** tab to see drivers on mouth shapes
- Scrub timeline with **middle mouse** to preview

### Other Issues
- Check **Window → Toggle System Console** for detailed error messages
- See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for troubleshooting code

---

## Next Steps

- 🎨 [Quick Start Guide](docs/QUICKSTART.md) - Workflow overview
- 🏗️ [Architecture](docs/ARCHITECTURE.md) - How LipKit works
- 📚 [API Reference](docs/API.md) - Use LipKit programmatically
- 🔧 [Development](docs/DEVELOPMENT.md) - Extend LipKit
