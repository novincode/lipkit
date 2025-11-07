# LipKit Quick Start Guide

## 🚀 5-Minute Setup

### Prerequisites
- Blender 4.2 or newer
- Audio file with dialogue
- Character with mouth drawings/shapes

### Installation
1. Download `lipkit` folder
2. Place in Blender extensions directory
3. Enable in Preferences → Get Extensions

## 📝 Basic Workflow

### For 2D (Grease Pencil)

**1. Prepare Mouth Drawings**
- Create GP object
- Draw 9 mouth shapes on separate layers:
  - `Mouth_REST` - closed
  - `Mouth_AH` - open wide
  - `Mouth_EE` - smiling
  - `Mouth_OH` - round
  - `Mouth_OO` - pucker
  - `Mouth_M` - lips closed
  - `Mouth_F` - lip to teeth
  - `Mouth_L` - tongue up
  - `Mouth_S` - teeth showing

**2. Open LipKit Panel**
- Press `N` to open sidebar
- Click "LipKit" tab

**3. Load Audio**
- Audio Source → File
- Browse to your audio file
- Click "Analyze Audio"

**4. Set Up Target**
- Visual System → "Grease Pencil Layers"
- Target Object → Select your GP object
- Preset → "Preston Blair (9)"
- Click "Load Preset"
- Click "Auto-Map Targets"

**5. Generate**
- Click "Create Controller"
- Set Start Frame
- Check "Use NLA Strip"
- Click "🚀 Generate Lip Sync"

**Done!** Press Space to play animation.

### For 3D (Shape Keys)

**1. Prepare Shape Keys**
- Select head mesh
- Add shape keys (Object Data Properties → Shape Keys)
- Create keys for: AH, EE, OH, OO, M, F, L, S

**2-5. Same as 2D**, but choose:
- Visual System → "Shape Keys (3D)"

## 🎨 Tips & Tricks

### Naming Conventions
**Good names** (auto-maps easily):
- `Mouth_AH`, `Mouth_EE`
- `AH_shape`, `EE_shape`
- `viseme_ah`, `viseme_ee`

**Bad names**:
- `Layer 1`, `Layer 2`
- Random names

### Audio Sources
You can use either:
- **External file**: Any .wav, .mp3, .ogg
- **VSE strip**: Audio already in timeline

### Timeline Organization
LipKit keeps timeline clean:
- ✅ Only controller is animated
- ✅ One property channel
- ✅ Mouth shapes controlled by drivers

Traditional method would clutter timeline with hundreds of keyframes!

### Testing Without Phoneme Tool
LipKit includes mock data for testing:
- Works without installing Rhubarb/Allosaurus
- Perfect for testing your setup
- Real tool needed for production

## 🔧 Common Issues

### "No mappings"
1. Load a preset first
2. Run Auto-Map Targets
3. Or manually set target names

### "Phoneme data not found"
1. Check audio file path
2. Click "Analyze Audio"
3. Wait for processing

### Animation doesn't play
1. Check controller exists
2. Verify drivers in Graph Editor → Drivers
3. Ensure target object is correct

### Layers not switching
1. Check layer names match mappings
2. Verify drivers are created
3. Scrub timeline - should see controller.phoneme_index changing

## 📖 Next Steps

**Improve Results**:
- Install Rhubarb for better phoneme detection
- Use Cloud API for multi-language support
- Adjust timing by moving keyframes on controller

**Advanced Features**:
- Create custom presets
- Use NLA strips for multiple dialogues
- Combine with other animations

**Learn More**:
- `/docs/ARCHITECTURE.md` - How it works
- `/docs/API.md` - Python scripting
- `/docs/DEVELOPMENT.md` - Extend LipKit

## 💡 Example Scene Setup

```python
# Quick test in Blender Python console
import bpy
from lipkit.core.animation_engine import quick_generate

# Generate lip sync with one function!
results = quick_generate(
    audio_path="/path/to/audio.wav",
    target_object=bpy.data.objects["GP_Mouth"],
    visual_system_type="gp_layer",
    preset_name="preston_blair",
    start_frame=1
)

print(f"Done! {results['keyframes_created']} keyframes created")
```

## 🎓 Video Tutorial

Coming soon: Step-by-step video walkthrough

## 📮 Get Help

- GitHub Issues: Report bugs
- Discussions: Ask questions
- Discord: Community chat (coming soon)

---

**Happy animating! 🎬**
