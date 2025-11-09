# 🎬 LipKit: Blender Auto Lip Sync for 3D/2D Mouths

**Automatic lip sync for 2D (Grease Pencil) and 3D (Shape Keys) animations.**

Real phoneme extraction with **Rhubarb Lip Sync**. Clean timeline. Production-ready.

**Works with:** Blender 3.2+ | Shape Keys | Grease Pencil Layers

---

## ⚡ Quick Start (2 minutes)

### 1. Install LipKit Extension
- Add this repository as a local extension in Blender
- Enable "LipKit" in Preferences → Extensions

### 2. Setup Rhubarb (Auto or Manual)
**Option A: Auto-Download (Recommended)**
1. Open Blender Preferences → Extensions → LipKit
2. Set "Rhubarb Setup" to **Auto**
3. Click **"📥 Download Rhubarb"**
4. Wait 1-2 minutes ✓

**Option B: Manual Setup**
1. Download from: https://github.com/DanielSWolf/rhubarb-lip-sync/releases
2. Set "Rhubarb Setup" to **Manual**
3. Click **"📁 Select Rhubarb Folder"**
4. Navigate to your `rhubarb` executable

**Status should show: ✅ Ready**

### 3. Create Mouth Shapes

**For Grease Pencil (2D):**
- Create 9 layers named: `X`, `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`
- Or: `Mouth_X`, `Mouth_A`, etc.
- Draw different mouth shapes on each

**For 3D (Shape Keys):**
- Add shape keys named: `X`, `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`
- Model different mouth shapes

**What each shape means:**
- `X` = REST (closed mouth)
- `A` = AH (father, hot)
- `B` = M/B/P (lips closed)
- `C` = EE (see, tree)
- `D` = L/D/T (tongue up)
- `E` = OH (go, show)
- `F` = F/V (lip to teeth)
- `G` = K/G (tongue back)
- `H` = OO (food, you)

### 4. Generate Lip Sync

1. Add audio to VSE (or use File source)
2. Click **"Analyze Audio"** ← Rhubarb extracts phonemes
3. Select **"Rhubarb (A-H, X)"** preset
4. Click **"Load Preset"** (refresh icon)
5. Select your GP object or mesh
6. Click **"Auto-Map Targets"** ← Matches layers/keys
7. Click **"Create Controller"** (if not exists)
8. Click **"🚀 Generate Lip Sync"**

**Done!** Press Space to play.

---

## 🎯 Features

- ✅ **Real phoneme extraction** with Rhubarb Lip Sync
- ✅ **Clean timeline** - single controller property drives all shapes
- ✅ **2D & 3D support** - Grease Pencil layers or Shape Keys
- ✅ **Offline** - no API calls, no internet needed
- ✅ **Fast** - processes audio in seconds
- ✅ **Accurate** - uses speech recognition
- ✅ **Open source** - MIT licensed

---

## 📖 Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup guide
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Quick workflow
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical details
- **[docs/API.md](docs/API.md)** - Python API reference

---

## 🔧 Troubleshooting

### "Tool not found" or "Not configured"
1. Download Rhubarb from GitHub releases
2. Open Setup panel in LipKit (N-sidebar)
3. Click "Configure Tool Path"
4. Select the `rhubarb` executable (not the folder)

### "Auto-mapped 0 targets"
- Your layers/shape keys don't have the right names
- Must contain: `X`, `A`, `B`, `C`, `D`, `E`, `F`, `G`, or `H`
- Case-insensitive: `mouth_a` or `Mouth_A` both work

### "Invalid command line" (Rhubarb error)
- Make sure you're pointing to the `rhubarb` executable
- On macOS: Right-click → Open first time to bypass security
- Check system console (Window → Toggle System Console) for full errors

### Animation doesn't play
- Make sure controller object exists (Create Controller)
- Check drivers in Graph Editor → Drivers tab
- Verify mouth object is correct

---

## 🎨 How It Works

Traditional lip sync clutters your timeline with hundreds of keyframes. LipKit uses a **single controller property** that drives all mouth shapes via expressions.

**Result**: 
- ✅ One animated channel
- ✅ Clean timeline
- ✅ Easy to adjust timing
- ✅ Works with NLA strips

**Under the hood**:
1. Rhubarb analyzes audio → extracts phonemes
2. LipKit creates a controller with `phoneme_index` property
3. Drivers on your mouth shapes read this property
4. Each driver: "Show this shape when phoneme_index = X"

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

**Made with ❤️ for the Blender community**
