# LipKit - Universal Lip Sync for Blender

**Headless, scalable lip sync system for 2D and 3D animations**

LipKit is a professional-grade Blender extension that provides automatic lip synchronization for both 2D (Grease Pencil) and 3D (Shape Keys) workflows. Built with a clean, extensible architecture that keeps your timeline organized.

## 🚀 Features

- **Universal System**: Works with Grease Pencil layers, Shape Keys, and extensible for custom systems
- **Clean Timeline**: Single controller property drives all animations via drivers - no cluttered timeline!
- **Multiple Phoneme Engines**:
  - **Local (Free)**: Use Rhubarb or Allosaurus locally, no internet required
  - **Cloud API (Premium)**: High-accuracy cloud extraction with multi-language support
  - **Custom API**: Connect your own phoneme extraction service
- **Audio Sources**: Load from file or use Video Sequence Editor strips
- **Preset System**: Preston Blair (9 shapes) and ARPAbet included, create custom mappings
- **Non-Destructive**: Optional NLA strip output for layered workflows
- **Cache System**: Speeds up iteration by caching phoneme data

## 📦 Installation

### For Blender 4.2+

1. Download the latest release
2. Open Blender → Edit → Preferences → Get Extensions
3. Install from Disk → Select `lipkit` folder
4. Enable "LipKit" extension

### Manual Installation

Copy the `lipkit` folder to your Blender extensions directory:
- **Windows**: `%USERPROFILE%\AppData\Roaming\Blender Foundation\Blender\4.2\extensions\user_default\`
- **macOS**: `~/Library/Application Support/Blender/4.2/extensions/user_default/`
- **Linux**: `~/.config/blender/4.2/extensions/user_default/`

## 🎯 Quick Start

### 2D Animation (Grease Pencil)

1. **Prepare Your Mouth Drawings**:
   - Create a Grease Pencil object
   - Draw different mouth shapes on separate layers
   - Name layers: "Mouth_AH", "Mouth_EE", "Mouth_M", etc.

2. **Set Up LipKit**:
   - Open sidebar (N key) → LipKit tab
   - **Audio Source**: Select your audio file or VSE strip
   - **Phoneme Engine**: Choose "Local (Free)" for testing
   - Click "Analyze Audio"

3. **Configure Visual System**:
   - **Visual System**: Select "Grease Pencil Layers"
   - **Target Object**: Select your GP object
   - **Preset**: Choose "Preston Blair (9)"
   - Click "Load Preset"
   - Click "Auto-Map Targets" to match layers

4. **Generate**:
   - Click "Create Controller" (creates the single control object)
   - Set start frame
   - Click "🚀 Generate Lip Sync"

Done! Your mouth shapes will automatically switch based on the audio.

### 3D Animation (Shape Keys)

1. **Prepare Shape Keys**:
   - Select your head mesh
   - Add shape keys for different mouth positions
   - Name them: "AH", "EE", "OH", "M", etc.

2. **Follow same steps as above**, but:
   - **Visual System**: Select "Shape Keys (3D)"
   - Rest is identical!

## 🎨 How It Works

### The Controller System

Unlike traditional lip sync that clutters your timeline with hundreds of keyframes across multiple layers, LipKit uses a **single controller property**:

1. **Controller Object** holds one custom property: `phoneme_index` (integer)
2. **Keyframes** are placed only on this property (CONSTANT interpolation)
3. **Drivers** on your mouth targets read the controller value
4. Each driver shows/hides its target when `phoneme_index` matches

**Result**: Clean timeline with one animated channel controlling everything!

### Phoneme → Viseme Mapping

LipKit intelligently reduces phonemes to visemes (visual mouth shapes):

- **ARPAbet phonemes** (40+) → **Preston Blair visemes** (9 shapes)
- Example: "AA", "AE", "AH" all map to "AH" viseme
- Customizable for your art style

## 📚 Presets

### Preston Blair (9 Shapes)
Classic 2D animation standard:
- **REST**: Closed mouth
- **AH**: Open (father, hot)
- **EE**: Wide (see, tree)
- **OH**: Round (go, show)
- **OO**: Pursed (moon, you)
- **M**: Lips closed (M, B, P)
- **F**: Lip to teeth (F, V)
- **L**: Tongue up (L, D, T)
- **S**: Teeth together (S, Z)

### ARPAbet
Full English phoneme set with 40+ sounds mapped to 9 visemes.

## ⚙️ Configuration

### Preferences (Edit → Preferences → Extensions → LipKit)

**Local Tool**:
- Set path to Rhubarb or Allosaurus executable
- Enable cache for faster iteration

**Cloud API**:
- Enter API key from lipkit.dev
- Premium features: better accuracy, more languages

**Custom API**:
- Point to your own phoneme extraction service
- Must return LipKit JSON format

## 🔧 Advanced Usage

### Custom Mappings

Create your own phoneme sets:

```python
# In Python API or operator
from lipkit.core import PhonemeMapping

mapping = PhonemeMapping()
mapping.add_mapping("AH", 0, "MyLayer_Open")
mapping.add_mapping("EE", 1, "MyLayer_Smile")
mapping.save_to_file("my_preset.json")
```

### Programmatic Generation

```python
import bpy
from lipkit.core import AnimationEngine, LipSyncController
from lipkit.phoneme_providers import LocalPhonemeProvider

# Extract phonemes
provider = LocalPhonemeProvider()
lipsync_data = provider.extract_phonemes("/path/to/audio.wav")

# Create controller
controller = LipSyncController.create_controller()

# Generate (simplified - see full docs)
engine = AnimationEngine(lipsync_data, mapping, controller)
results = engine.generate(target_object, start_frame=1)
```

## 🐛 Troubleshooting

### "Provider not available"
- **Local**: Install Rhubarb or Allosaurus, set path in preferences
- **API**: Check API key, internet connection

### "No mappings"
- Load a preset first, then run Auto-Map Targets
- Or manually set target names for each phoneme

### "Shape keys not found"
- Ensure mesh has shape keys: Mesh → Shape Keys → Add Shape Key
- Must have both Basis and at least one other shape key

### Timeline is cluttered
- You're not using LipKit correctly!
- Should only see one property animated: Controller's `phoneme_index`
- Check that drivers are created (Graph Editor → Drivers)

## 📖 Documentation

Full documentation in `/docs`:
- `ARCHITECTURE.md`: Technical design and internals
- `API.md`: Python API reference
- `USER_GUIDE.md`: Complete user manual
- `DEVELOPMENT.md`: Contributing guide

## 🤝 Contributing

LipKit is open source! Contributions welcome:

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

### Extending LipKit

Add your own visual system:

```python
from lipkit.visual_systems import VisualSystem, register_visual_system

class MyCustomSystem(VisualSystem):
    @property
    def system_type(self):
        return "my_system"
    
    def create_driver(self, controller, target, phoneme_index, **kwargs):
        # Your driver creation logic
        pass

register_visual_system("my_system", MyCustomSystem())
```

## 📜 License

MIT License - See LICENSE file

## 💰 Premium Features

### LipKit Cloud API

- **Higher accuracy**: ML-powered phoneme detection
- **Multi-language**: English, Spanish, French, German, Japanese, and more
- **Batch processing**: Process multiple files
- **Priority support**

Get API key at: **lipkit.dev** (coming soon)

## 🙏 Credits

- Inspired by Adobe Animate's lip sync system
- Built for the Blender community
- Thanks to Rhubarb Lip Sync and Allosaurus projects

## 📮 Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: support@lipkit.dev

---

**Made with ❤️ for animators**
