# LipKit Architecture

## Overview

LipKit is designed as a **modular, headless, extensible** lip sync system for Blender. The core philosophy is separation of concerns and clean abstractions.

## Design Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Extensibility**: Easy to add new phoneme providers or visual systems
3. **Timeline Cleanliness**: One animated property controls everything
4. **Headless-First**: Core logic independent of UI
5. **No Vendor Lock-in**: Support local and cloud processing

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                    (Blender Panels & Operators)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼─────────┐        ┌───────▼──────────┐
│  Phoneme Engine │        │  Visual Systems  │
│  (Extract)      │        │  (Render)        │
└────────┬────────┘        └────────┬─────────┘
         │                          │
         │    ┌─────────────────────┘
         │    │
    ┌────▼────▼─────┐
    │  Controller   │
    │  (Coordinate) │
    └────┬──────────┘
         │
    ┌────▼────────┐
    │  Animation  │
    │  Engine     │
    └─────────────┘
```

## Module Breakdown

### 1. Core (`core/`)

**Responsibility**: Data structures and core logic

#### `phoneme_engine.py`
- **PhonemeData**: Single phoneme with timing
- **LipSyncData**: Complete phoneme sequence
- **PhonemeProvider**: Abstract base for extraction

**Key Design**: Provider pattern allows swapping extraction methods without changing downstream code.

#### `controller.py`
- **LipSyncController**: Manages the single control object
- Creates Empty with `phoneme_index` custom property
- Keyframe management with CONSTANT interpolation
- NLA strip creation for non-destructive workflow

**Key Innovation**: Single integer property + drivers = clean timeline!

#### `mapping.py`
- **PhonemeMapping**: Phoneme → visual target mapping
- **PresetManager**: Load/save JSON presets
- **VisemeMapper**: Phoneme → viseme reduction

**Key Feature**: JSON-based presets for portability and sharing

#### `animation_engine.py`
- **AnimationEngine**: Orchestrates generation
- Converts LipSyncData → keyframes + drivers
- Handles frame calculations and timing

**Key Role**: The "conductor" that connects all pieces

### 2. Phoneme Providers (`phoneme_providers/`)

**Responsibility**: Extract phonemes from audio

#### `local_provider.py`
- Calls external tools via subprocess (Rhubarb, Allosaurus)
- Falls back to mock data for development
- No internet required

#### `api_provider.py`
- **APIPhonemeProvider**: LipKit Cloud service
- **CustomAPIProvider**: User's own endpoint
- Handles authentication, retries, errors

**Extensibility**: Create custom providers by subclassing PhonemeProvider

### 3. Visual Systems (`visual_systems/`)

**Responsibility**: Create drivers for different target types

#### `visual_system.py`
- **VisualSystem**: Abstract base
- **GreasePencilLayerSystem**: GP layer opacity drivers
- **ShapeKeySystem**: Shape key value drivers
- **ImageSequenceSystem**: Texture switching (TODO)
- **GeometryNodesSystem**: GN attribute drivers (TODO)

**Key Pattern**: Each system knows how to:
1. Validate a target object
2. Create a driver linking controller → target
3. Set up driver expression (e.g., `phoneme == index`)

**Driver Expression**:
```python
# For instant switching
"1.0 if phoneme == {index} else 0.0"

# For smooth blending
"max(0.0, 1.0 - abs(phoneme - {index}) / {blend_range})"
```

### 4. Utilities (`utils/`)

#### `audio_utils.py`
- VSE integration (extract audio from strips)
- Audio file validation
- Cache management (hash-based)
- Time ↔ frame conversion

**Cache System**:
- Key: `hash(audio_content + language + provider)`
- Stored in Blender temp dir
- Prevents re-extraction on iteration

### 5. UI (`ui.py`, `operators.py`, `properties.py`)

**Responsibility**: Blender integration

#### `properties.py`
- Scene-level property groups
- Stores user selections (audio, target, mappings)
- Uses Blender's PointerProperty for object references

#### `operators.py`
- **LIPKIT_OT_create_controller**: Creates Empty
- **LIPKIT_OT_analyze_audio**: Extracts phonemes
- **LIPKIT_OT_generate**: Runs full pipeline
- Each operator is self-contained with error handling

#### `ui.py`
- Panel hierarchy in N-sidebar
- Collapsible sections for clean UX
- Real-time validation (shows issues before generation)

### 6. Preferences (`preferences.py`)

**Responsibility**: Global settings

- Local tool path
- API keys (Cloud, Custom)
- Cache settings
- Debug mode

## Data Flow

### Phoneme Extraction Flow

```
Audio File
    ↓
[Validate Audio]
    ↓
[Check Cache] ─→ Found? ─→ Return Cached Data
    ↓ Not Found
[PhonemeProvider.extract_phonemes()]
    ↓
[Parse Tool Output]
    ↓
[Create LipSyncData]
    ↓
[Save to Cache]
    ↓
Return LipSyncData
```

### Animation Generation Flow

```
LipSyncData + Mapping + Controller
    ↓
[Build Phoneme → Index Map]
    ↓
[Calculate Frame Positions] (time * fps + start_frame)
    ↓
[Create Keyframes on Controller]
    ↓
[For Each Unique Index:]
    ├─ Find Target Name from Mapping
    ├─ Get Visual System
    └─ Create Driver (controller → target)
    ↓
Return Statistics
```

### Driver Evaluation (Runtime)

```
Frame Changes
    ↓
Blender Evaluates Keyframes
    ↓
Controller.phoneme_index = N
    ↓
Drivers Read phoneme_index
    ↓
Driver Expression Evaluates
    ↓
Target Property Updated (opacity=1.0 or 0.0)
    ↓
Correct Mouth Shape Visible
```

## Key Algorithms

### Phoneme-to-Viseme Mapping

```python
VISEME_GROUPS = {
    "AH": ["AA", "AE", "AH", "K", "G", ...],
    "EE": ["IH", "IY", "EH", "EY", ...],
    # ...
}

def phoneme_to_viseme(phoneme):
    for viseme, phoneme_list in VISEME_GROUPS.items():
        if phoneme in phoneme_list:
            return viseme
    return "REST"
```

Reduces 40+ ARPAbet phonemes → 9 Preston Blair visemes

### Frame Calculation

```python
def time_to_frame(time_seconds, fps):
    return round(time_seconds * fps)

frame = start_frame + time_to_frame(phoneme.start_time, fps)
```

### Driver Creation

```python
# Add FCurve with driver
fcurve = target.data.driver_add(data_path)
driver = fcurve.driver
driver.type = 'SCRIPTED'

# Add variable pointing to controller
var = driver.variables.new()
var.name = "phoneme"
var.type = 'SINGLE_PROP'
var.targets[0].id = controller
var.targets[0].data_path = '["phoneme_index"]'

# Set expression
driver.expression = f"1.0 if phoneme == {index} else 0.0"
```

## Extension Points

### Adding a Phoneme Provider

```python
from lipkit.core import PhonemeProvider, LipSyncData

class MyProvider(PhonemeProvider):
    @property
    def name(self):
        return "My Custom Provider"
    
    def is_available(self):
        return True  # Check dependencies
    
    def extract_phonemes(self, audio_path, language="en"):
        # Your extraction logic
        phonemes = [...]
        return LipSyncData(phonemes=phonemes, duration=5.0)
    
    def get_supported_languages(self):
        return ["en", "fr"]
```

### Adding a Visual System

```python
from lipkit.visual_systems import VisualSystem, register_visual_system

class VertexColorSystem(VisualSystem):
    @property
    def system_type(self):
        return "vertex_color"
    
    @property
    def system_name(self):
        return "Vertex Colors"
    
    def validate_target(self, obj, **kwargs):
        return obj.type == 'MESH'
    
    def create_driver(self, controller, target, phoneme_index, **kwargs):
        # Create driver for vertex color attribute
        pass

# Register it
register_visual_system("vertex_color", VertexColorSystem())
```

## Performance Considerations

### Timeline Efficiency
- **Traditional approach**: N layers × M keyframes = clutter
- **LipKit approach**: 1 controller × M keyframes = clean
- Drivers have minimal overhead (evaluated per frame like any animation)

### Cache Strategy
- Hash audio content (not path) to detect changes
- Cache invalidated if: audio changes, language changes, provider changes
- Cache files in Blender temp dir (auto-cleaned on quit)

### Driver Performance
- Drivers are lightweight Python expressions
- Evaluated once per frame per target
- For 9 visemes: 9 drivers × frame rate = negligible overhead

## Error Handling

### Graceful Degradation
1. **No phoneme tool?** → Use mock data (allows testing UI)
2. **No API key?** → Fall back to local provider
3. **No cache?** → Re-extract (slower but works)
4. **Invalid mapping?** → Skip that phoneme, continue

### User Feedback
- All operators report status via `self.report()`
- Info messages for success
- Warning for non-critical issues
- Error for blocking issues

## Future Enhancements

### Planned Features
1. **Real-time Preview**: Scrub timeline to preview phonemes
2. **Batch Processing**: Multiple audio files → multiple actions
3. **Emotion Modifiers**: Adjust visemes based on emotion
4. **Co-articulation**: Smooth transitions between phonemes
5. **Whisper Integration**: Direct Whisper model support (no external tool)

### Architecture Support
The current design supports these features without major refactoring:
- Phoneme engine is already abstracted (easy to add Whisper provider)
- Visual systems are pluggable (easy to add new target types)
- Mapping is JSON-based (easy to add emotion overrides)

## Testing Strategy

### Unit Tests (Future)
- Test PhonemeData serialization
- Test mapping logic
- Test frame calculations
- Mock Blender API for core logic

### Integration Tests
- Test with real Blender scenes
- Test GP layer system
- Test shape key system
- Test VSE integration

### Manual Testing
- Create test scenes with known phoneme sequences
- Verify visual output matches audio
- Test all UI paths

## Conclusion

LipKit's architecture prioritizes:
1. **Clean abstraction**: Core logic independent of UI
2. **Extensibility**: Easy to add providers and systems
3. **User experience**: Clean timeline, intuitive workflow
4. **Professional workflow**: NLA strips, caching, presets

The single-controller design is the core innovation that keeps Blender's timeline clean while maintaining full flexibility for different art styles and workflows.
