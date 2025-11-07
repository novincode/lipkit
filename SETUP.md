# 🎬 LipKit Setup - Get It Working Now

## The Issue You Had

You were seeing "9 phonemes extracted" but it was **FAKE DATA**. No real phoneme extraction was happening.

## The Fix

LipKit now requires **Rhubarb Lip Sync** - a free, open-source tool that actually analyzes audio.

---

## Step 1: Download Rhubarb (2 minutes)

1. Go to: https://github.com/DanielSWolf/rhubarb-lip-sync/releases
2. Download the latest version for macOS:
   - Look for `Rhubarb-Lip-Sync-X.X.X-macOS.zip`
3. Extract the ZIP file
4. Move `rhubarb` (the executable) somewhere permanent:
   - **Recommended**: `/Users/shayanmoradi/Applications/rhubarb`
   - Or: Anywhere you won't delete it

## Step 2: Configure LipKit (30 seconds)

1. Open Blender
2. Go to: **Edit → Preferences → Extensions → LipKit**
3. Find "Local Tool Path"
4. Click the folder icon
5. Navigate to where you put `rhubarb`
6. Select it
7. Click OK

## Step 3: Test It (1 minute)

1. In Blender, add an audio file to VSE (Video Editing workspace)
2. Open LipKit panel (N key → LipKit tab)
3. Select your audio in "Audio Source"
4. Click **"Analyze Audio"**

**You should see**:
```
Running: /path/to/rhubarb -f json --recognizer pocketsphinx audio.wav
Extracted 47 phonemes (3.2s)
```

**NOT the fake**:
```
Extracted 9 phonemes (5.0s)  ← This was bullshit
```

---

## Step 4: Create Mouth Shapes

### For Grease Pencil (2D):

Create 9 layers with these **exact names**:
- `X` or `Mouth_X` - REST (closed mouth)
- `A` or `Mouth_A` - AH sound (father, hot)
- `B` or `Mouth_B` - M, B, P (lips closed)
- `C` or `Mouth_C` - EE sound (see, tree)
- `D` or `Mouth_D` - L, D, T (tongue up)
- `E` or `Mouth_E` - OH sound (go, show)
- `F` or `Mouth_F` - F, V (lip to teeth)
- `G` or `Mouth_G` - K, G (tongue back)
- `H` or `Mouth_H` - OO sound (food, you)

Draw different mouth shapes on each layer.

### For Shape Keys (3D):

Add shape keys to your mesh with these names:
- `X`, `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`

---

## Step 5: Generate Animation

1. **Analyze Audio** (extracts phonemes with Rhubarb)
2. **Load Preset**: Select "Rhubarb (A-H, X)"
3. Click **"Load Preset"** (the refresh icon)
4. Select your Grease Pencil or Mesh object
5. Click **"Auto-Map Targets"**
6. Click **"Create Controller"**
7. Click **"🚀 Generate Lip Sync"**

Done! Press Space to play.

---

## Why This Is Better

**Before**: Fake data, no real analysis
**Now**: Real phoneme extraction from actual audio

Rhubarb is:
- ✅ Free and open-source
- ✅ Works offline (no API needed)
- ✅ Fast (processes audio in seconds)
- ✅ Accurate (uses speech recognition)

---

## Troubleshooting

**"Tool not found at /path/to/rhubarb"**
- Check the path is correct
- Make sure you selected the `rhubarb` executable, not the folder
- On macOS, you might need to right-click → Open first to allow it

**"Auto-mapped 0 targets"**
- Your layer/shape key names don't match
- Name them: `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`, `X`
- Or: `Mouth_A`, `Mouth_B`, etc.
- Must include the letter (case-insensitive)

**"No phoneme data"**
- Click "Analyze Audio" first
- Check system console for Rhubarb errors
- Make sure audio file is valid (.wav, .mp3, .ogg)

---

**Now you have REAL lip sync!** 🎉
