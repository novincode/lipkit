# LipKit Development Guide

## Project Setup

### Prerequisites
- Blender 4.2 or later
- Python 3.10+ (comes with Blender)
- Git

### Development Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lipkit.git
cd lipkit
```

2. Symlink to Blender extensions directory:

**macOS/Linux**:
```bash
ln -s $(pwd)/lipkit ~/Library/Application\ Support/Blender/4.2/extensions/user_default/lipkit
```

**Windows**:
```cmd
mklink /D "%APPDATA%\Blender Foundation\Blender\4.2\extensions\user_default\lipkit" "%CD%\lipkit"
```

3. Enable in Blender:
   - Edit → Preferences → Get Extensions
   - Enable "LipKit"

### Development Workflow

1. Make changes to code
2. In Blender: F3 → "Reload Scripts" (or restart Blender)
3. Test changes
4. Commit

## Code Style

### Python Style Guide

Follow PEP 8 with these specifics:

- **Indentation**: 4 spaces
- **Line length**: 100 characters (soft limit)
- **Quotes**: Use double quotes for strings
- **Imports**: Group stdlib, third-party, local

```python
# Good
from typing import List, Optional
import bpy

from ..core import LipSyncData
from .utils import validate_audio

# Bad
from ..core import LipSyncData
import bpy
from typing import List
```

### Blender Conventions

- **Class names**: `CATEGORY_MT_name` for menus, `CATEGORY_OT_name` for operators
- **bl_idname**: Lowercase with dots: `"lipkit.generate"`
- **Properties**: Use Blender's property types, not plain Python attributes

### Documentation

All public APIs need docstrings:

```python
def extract_phonemes(self, audio_path: str, language: str = "en") -> LipSyncData:
    """
    Extract phonemes from audio file
    
    Args:
        audio_path: Absolute path to audio file
        language: Language code (ISO 639-1)
        
    Returns:
        LipSyncData with phoneme timing information
        
    Raises:
        AudioFileError: If file doesn't exist or is invalid
        ExtractionError: If phoneme extraction fails
    """
```

## Project Structure

```
lipkit/
├── __init__.py              # Main registration
├── blender_manifest.toml    # Extension metadata
├── preferences.py           # Addon preferences
├── properties.py            # Property groups
├── operators.py             # Blender operators
├── ui.py                    # UI panels
├── core/                    # Core logic (Blender-independent)
│   ├── phoneme_engine.py
│   ├── controller.py
│   ├── mapping.py
│   └── animation_engine.py
├── phoneme_providers/       # Phoneme extraction
│   ├── local_provider.py
│   └── api_provider.py
├── visual_systems/          # Target system handlers
│   └── visual_system.py
├── utils/                   # Utilities
│   └── audio_utils.py
└── presets/                 # JSON presets
    ├── preston_blair.json
    └── arpabet.json
```

## Adding Features

### Adding a Phoneme Provider

1. Create new file in `phoneme_providers/`:

```python
# phoneme_providers/whisper_provider.py
from ..core import PhonemeProvider, LipSyncData, PhonemeData

class WhisperProvider(PhonemeProvider):
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.model = None
    
    @property
    def name(self):
        return f"Whisper ({self.model_size})"
    
    @property
    def description(self):
        return "OpenAI Whisper for phoneme extraction"
    
    def is_available(self):
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    def get_supported_languages(self):
        return ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"]
    
    def extract_phonemes(self, audio_path, language="en", **kwargs):
        if not self.model:
            import whisper
            self.model = whisper.load_model(self.model_size)
        
        # Extract with word-level timestamps
        result = self.model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True
        )
        
        # Convert to phonemes (simplified - real implementation needs phonemizer)
        phonemes = []
        for segment in result["segments"]:
            for word in segment.get("words", []):
                # TODO: Convert word to phonemes
                phonemes.append(PhonemeData(
                    phoneme="AH",  # Placeholder
                    start_time=word["start"],
                    end_time=word["end"],
                    confidence=1.0
                ))
        
        return LipSyncData(
            phonemes=phonemes,
            duration=result["duration"],
            language=language
        )
```

2. Register in `phoneme_providers/__init__.py`:

```python
from .whisper_provider import WhisperProvider

__all__ = [
    'LocalPhonemeProvider',
    'APIPhonemeProvider',
    'CustomAPIProvider',
    'WhisperProvider',  # Add here
]
```

3. Add to UI enum in `properties.py`:

```python
phoneme_provider: EnumProperty(
    items=[
        ('LOCAL', 'Local (Free)', 'Local phoneme extraction'),
        ('API', 'Cloud API (Premium)', 'Cloud-based extraction'),
        ('WHISPER', 'Whisper', 'OpenAI Whisper model'),  # Add here
        ('CUSTOM', 'Custom API', 'Custom API endpoint'),
    ]
)
```

### Adding a Visual System

1. Create system in `visual_systems/visual_system.py`:

```python
class BoneTransformSystem(VisualSystem):
    """Control jaw bone rotation based on phonemes"""
    
    @property
    def system_name(self):
        return "Bone Transform"
    
    @property
    def system_type(self):
        return "bone_transform"
    
    def validate_target(self, target_object, **kwargs):
        if target_object.type != 'ARMATURE':
            return False
        
        bone_name = kwargs.get("bone_name")
        if bone_name and bone_name not in target_object.pose.bones:
            return False
        
        return True
    
    def create_driver(self, controller, target_object, phoneme_index, **kwargs):
        bone_name = kwargs.get("bone_name")
        transform_type = kwargs.get("transform_type", "rotation_euler")
        axis = kwargs.get("axis", 2)  # Z axis
        
        # Get bone
        bone = target_object.pose.bones[bone_name]
        
        # Create driver on rotation
        data_path = f'pose.bones["{bone_name}"].{transform_type}'
        fcurve = target_object.driver_add(data_path, axis)
        
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        
        # Variable
        var = driver.variables.new()
        var.name = "phoneme"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = controller
        var.targets[0].data_path = '["phoneme_index"]'
        
        # Expression: rotate jaw based on openness
        # Different phonemes have different openness
        openness_map = {0: 0.0, 1: 0.5, 2: 0.2, 3: 0.4, 4: 0.1}
        driver.expression = f"({openness_map.get(phoneme_index, 0.0)} if phoneme == {phoneme_index} else 0.0)"
        
        return fcurve
```

2. Register in `visual_systems/visual_system.py`:

```python
VISUAL_SYSTEMS = {
    "gp_layer": GreasePencilLayerSystem(),
    "shape_key": ShapeKeySystem(),
    "bone_transform": BoneTransformSystem(),  # Add here
}
```

### Adding a Preset

1. Create JSON file in `presets/`:

```json
{
  "name": "My Custom Set",
  "description": "Custom phoneme set for my character",
  "phoneme_set": "custom",
  "mappings": [
    {"phoneme": "REST", "index": 0, "description": "Closed mouth"},
    {"phoneme": "OPEN", "index": 1, "description": "Wide open"},
    {"phoneme": "SMILE", "index": 2, "description": "Smiling"}
  ]
}
```

2. It will automatically appear in preset dropdown

## Testing

### Manual Testing Checklist

Create a test scene with:
- [ ] Grease Pencil object with mouth layers
- [ ] Mesh with shape keys
- [ ] Sample audio file
- [ ] VSE with audio strip

Test workflow:
1. [ ] Select audio (file and VSE)
2. [ ] Analyze audio
3. [ ] Load preset
4. [ ] Auto-map targets
5. [ ] Create controller
6. [ ] Generate lip sync
7. [ ] Verify animation plays correctly
8. [ ] Check timeline is clean (only controller animated)
9. [ ] Test NLA strip mode
10. [ ] Clear and regenerate

### Debugging

Enable debug mode in preferences for detailed logging:

```python
prefs = context.preferences.addons["lipkit"].preferences
if prefs.debug_mode:
    print(f"Debug: Extracting phonemes from {audio_path}")
```

View console output:
- **Windows**: Window → Toggle System Console
- **macOS/Linux**: Run Blender from terminal

## Common Issues

### "Module not found" errors
- Blender's Python is isolated
- Install packages in Blender's Python:
```bash
/Applications/Blender.app/Contents/Resources/4.2/python/bin/python3.10 -m pip install package_name
```

### Changes not reflecting
- Use F3 → "Reload Scripts"
- Or restart Blender
- Check for Python syntax errors in console

### Driver not updating
- Check driver expression in Graph Editor → Drivers
- Ensure controller object exists and has `phoneme_index` property
- Verify data path is correct

## Building for Distribution

### Package Extension

1. Remove development files:
```bash
rm -rf lipkit/__pycache__
rm -rf lipkit/*/__pycache__
```

2. Create distribution:
```bash
zip -r lipkit-v0.1.0.zip lipkit/ -x "*.pyc" -x "*__pycache__*" -x "*.git*"
```

3. Test installation:
   - Fresh Blender install
   - Install from zip
   - Test all features

### Version Bumping

Update version in:
1. `blender_manifest.toml`: `version = "0.1.0"`
2. `__init__.py`: `"version": (0, 1, 0)`
3. Create git tag: `git tag v0.1.0`

## Contributing Guidelines

### Pull Request Process

1. **Fork** the repository
2. **Create branch** from `main`: `git checkout -b feature/my-feature`
3. **Make changes** with clear commit messages
4. **Test** thoroughly
5. **Update docs** if needed
6. **Submit PR** with description of changes

### Commit Messages

Follow conventional commits:
```
feat: Add Whisper phoneme provider
fix: Correct frame calculation for 30fps
docs: Update installation instructions
refactor: Simplify driver creation logic
```

### Code Review

Pull requests require:
- [ ] Code follows style guide
- [ ] New features have docstrings
- [ ] No breaking changes (or clearly documented)
- [ ] Works in Blender 4.2+

## Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create git tag
4. Build distribution zip
5. Create GitHub release with zip
6. Update documentation site

## Resources

- [Blender Python API Docs](https://docs.blender.org/api/current/)
- [Blender Extensions](https://docs.blender.org/manual/en/latest/advanced/extensions/index.html)
- [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync)
- [ARPAbet Phonemes](https://en.wikipedia.org/wiki/ARPABET)

## Contact

- GitHub Issues: For bugs and feature requests
- Discussions: For questions and community chat
- Email: dev@lipkit.dev

---

**Happy coding! 🚀**
