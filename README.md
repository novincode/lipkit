# 🎬 LipKit: Blender Auto Lip Sync

**Automatic lip sync for 2D (Grease Pencil) and 3D (Shape Keys) animations.**

Real phoneme extraction using **Rhubarb Lip Sync**. Clean timeline. Professional animation.

**Works with:** Blender 4.2+ | Shape Keys | Grease Pencil

---

## �� Installation

1. **Unzip the ZIP file you downloaded**
2. Open Blender 4.2+
3. Go to **Edit → Preferences → Get Extensions → Install from Disk**
4. Select the ZIP file
5. Enable **LipKit** in the Extensions list
6. Press **N** to open the LipKit panel

---

## ⚡ Quick Start

### 1. Setup Rhubarb
- Open LipKit panel (Press **N**)
- Click **"📥 Download Rhubarb"** (1-2 minutes, auto setup)
- Or manually download from: https://github.com/DanielSWolf/rhubarb-lip-sync/releases

### 2. Create Mouth Shapes

Create **9 layers or shape keys** named:
- `X` - Closed mouth (REST)
- `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H` - Different mouth shapes

**For Grease Pencil:** Create layers, draw different mouths
**For Shape Keys:** Create keys, model different mouth poses

### 3. Generate Lip Sync

1. Load audio into Blender
2. Click **"Analyze Audio"** (extracts phonemes)
3. Select preset **"Rhubarb (A-H, X)"**
4. Click **"Load Preset"**
5. Select your mouth object
6. Click **"Auto-Map Targets"**
7. Click **"🚀 Generate Lip Sync"**

Done! Press **Space** to play.

---

## ✨ Features

- Real phoneme extraction with Rhubarb
- Clean timeline - one controller drives all
- 2D & 3D support
- Offline - no internet needed
- Fast - seconds to analyze
- Accurate - real speech recognition

---

## 📚 Help

- **Setup instructions**: See `SETUP.md`
- **Questions?**: Check `SETUP.md` troubleshooting section
- **More details**: See `docs/QUICKSTART.md`

---

## ⚖️ License

Proprietary software. See `LICENSE` file for terms.
