# LipKit Project Structure

```
lipsync-blender/
├── README.md                          # Main entry point
├── SETUP.md                           # Detailed setup guide
├── LICENSE                            # MIT License
├── .gitignore                         # Git ignore rules
│
├── lipkit/                            # Main extension folder
│   ├── __init__.py                    # Extension entry point & registration
│   ├── blender_manifest.toml          # Blender 4.2+ extension metadata
│   ├── preferences.py                 # Addon preferences (Rhubarb setup)
│   ├── properties.py                  # Scene property groups
│   ├── operators.py                   # Blender operators
│   ├── ui.py                          # UI panels
│   │
│   ├── core/                          # Core logic (Blender-independent)
│   │   ├── __init__.py
│   │   ├── phoneme_engine.py          # Data structures & provider base
│   │   ├── controller.py              # Single-property controller system
│   │   ├── mapping.py                 # Phoneme-to-visual mapping
│   │   └── animation_engine.py        # Keyframe & driver generation
│   │
│   ├── phoneme_providers/             # Phoneme extraction implementations
│   │   ├── __init__.py
│   │   ├── local_provider.py          # Local tools (Rhubarb)
│   │   └── api_provider.py            # Cloud API & custom endpoints
│   │
│   ├── visual_systems/                # Visual target handlers
│   │   ├── __init__.py
│   │   └── visual_system.py           # GP layers, shape keys, etc.
│   │
│   ├── utils/                         # Utilities
│   │   ├── __init__.py
│   │   ├── audio_utils.py             # Audio loading, VSE, caching, conversion
│   │   ├── easing_utils.py            # Animation easing curves
│   │   ├── rhubarb_manager.py         # GitHub download & installation
│   │   └── property_selector.py       # UI property selection
│   │
│   └── presets/                       # Phoneme presets (JSON)
│       ├── arpabet.json               # Full English phoneme set
│       ├── preston_blair.json         # Classic 9-shape preset
│       └── rhubarb.json               # Rhubarb-optimized (A-H, X)
│
└── docs/                              # Documentation
    ├── QUICKSTART.md                  # Quick start workflow
    ├── ARCHITECTURE.md                # Technical design & internals
    ├── API.md                         # Python API reference
    ├── PROJECT_STRUCTURE.md           # This file
    └── DEVELOPMENT.md                 # Contributing & extending guide
```

## File Count Summary

- **Python files**: 15 (core + providers + systems + utils + UI)
- **JSON presets**: 3 (arpabet, preston_blair, rhubarb)
- **Documentation**: 5 files (README, SETUP, QUICKSTART, ARCHITECTURE, API, PROJECT_STRUCTURE, DEVELOPMENT)
- **Configuration**: 2 files (.gitignore, blender_manifest.toml)

**Total**: ~25 files organized in 7 directories

## Key Design Decisions

### 1. **Modular Architecture**
- `core/` contains all business logic (testable, reusable)
- `phoneme_providers/` are pluggable (easy to add new providers)
- `visual_systems/` are extensible (support new target types)

### 2. **Single Controller Pattern**
- One `Empty` object with one custom property: `phoneme_index`
- All mouth shapes controlled via drivers reading this property
- **Result**: Clean timeline with only one animated channel!

### 3. **Headless-First Design**
- Core logic has no Blender UI dependencies
- Can be used programmatically via Python API
- UI is thin wrapper around core functionality

### 4. **Preset System**
- Mappings stored as JSON files
- Easy to share and version control
- Users can create custom presets

### 5. **Cache System**
- Phoneme extraction results cached in temp dir
- Hash-based keys (audio content + language + provider)
- Speeds up iteration during animation refinement

## Quick Stats

### Lines of Code (approximate)
- Core engine: ~800 lines
- Phoneme providers: ~400 lines
- Visual systems: ~300 lines
- UI & operators: ~600 lines
- Utilities: ~200 lines
- **Total**: ~2,300 lines of Python

### Features Implemented
✅ Local phoneme extraction (Rhubarb - auto-download or manual)
✅ Real-time audio analysis (non-blocking)
✅ Audio format conversion (MP3, M4A, OGG → WAV)
✅ Smooth mouth transitions (easing curves)
✅ Grease Pencil layer opacity control
✅ Shape key value control
✅ Clean animation timeline (single controller property)
✅ Driver generation with mapping
✅ NLA strip support
✅ Audio from file or VSE strip
✅ Phoneme preset system (3 presets included)
✅ Smart auto-mapping based on layer/key names
✅ "Clean All Keyframes" operator
✅ Comprehensive error handling
✅ Preferences UI for setup & configuration

### Features Planned (Future)
- Cloud API provider integration
- Custom API provider template
- Image sequence texture switching
- Geometry Nodes attribute drivers
- Real-time preview
- Batch processing
- Whisper speech recognition integration
- Multi-language support
- Animation preview in viewport

## How to Use This Structure

### For Users
1. Copy `lipkit/` folder to Blender extensions directory
2. Enable in Blender preferences
3. Follow QUICKSTART.md

### For Developers
1. Read ARCHITECTURE.md to understand design
2. Read DEVELOPMENT.md for contribution guidelines
3. Use API.md for Python scripting reference
4. Core code in `core/` is Blender-independent (easier to test)

### For Contributors
- New phoneme providers → `phoneme_providers/`
- New visual systems → `visual_systems/`
- New presets → `presets/` (JSON files)
- Documentation → `docs/`

## Dependencies

### Required (Built-in to Blender)
- bpy (Blender Python API)
- Python 3.10+ standard library

### Optional (for providers)
- `requests` - for API providers (may need to install in Blender's Python)
- External tools:
  - Rhubarb Lip Sync (local provider)
  - Allosaurus (local provider)

### No External Dependencies for Core
The core engine works with mock data, so users can test without installing tools!

## Testing the Installation

Run this in Blender's Python console to verify:

```python
import lipkit
from lipkit.core import LipSyncController, PhonemeMapping
from lipkit.phoneme_providers import LocalPhonemeProvider

print("✅ LipKit imported successfully!")
print(f"Version: {lipkit.bl_info['version']}")

# Test controller creation
controller = LipSyncController.create_controller()
print(f"✅ Controller created: {controller.name}")

# Test provider (uses mock data)
provider = LocalPhonemeProvider()
print(f"✅ Provider available: {provider.is_available()}")
```

## Next Steps After Installation

1. **Test with mock data**: Follow QUICKSTART.md to generate lip sync
2. **Install Rhubarb**: Download from GitHub for real phoneme extraction
3. **Configure API**: Get API key from lipkit.dev (coming soon)
4. **Create custom presets**: Copy JSON preset and modify for your character
5. **Explore Python API**: Use `quick_generate()` function for scripting

## Support & Community

- 📖 Read docs/ for detailed information
- 🐛 Report issues on GitHub
- 💬 Ask questions in Discussions
- 🤝 Contribute via pull requests

---

**Built with ❤️ for the Blender animation community**
