# LipKit Python API Reference

## Core Modules

### lipkit.core.phoneme_engine

#### PhonemeData
```python
@dataclass
class PhonemeData:
    """Single phoneme with timing information"""
    phoneme: str  # Phoneme code (e.g., "AH", "EE", "M")
    start_time: float  # Start time in seconds
    end_time: float  # End time in seconds
    confidence: float = 1.0  # Confidence score (0.0-1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Duration of phoneme in seconds"""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PhonemeData':
        """Create from dictionary"""
```

#### LipSyncData
```python
@dataclass
class LipSyncData:
    """Complete lip sync data with phonemes and metadata"""
    phonemes: List[PhonemeData]
    duration: float  # Total duration in seconds
    sample_rate: int = 44100
    language: str = "en"
    phoneme_set: str = "arpabet"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LipSyncData':
        """Create from dictionary"""
    
    def get_phoneme_at_time(self, time: float) -> Optional[PhonemeData]:
        """Get the phoneme active at a given time"""
    
    def get_frame_mapping(self, fps: float, start_frame: int = 1) -> Dict[int, PhonemeData]:
        """Map frames to phonemes"""
```

#### PhonemeProvider (Abstract)
```python
class PhonemeProvider(ABC):
    """Abstract base class for phoneme extraction providers"""
    
    @abstractmethod
    def extract_phonemes(
        self, 
        audio_path: str, 
        language: str = "en",
        **kwargs
    ) -> LipSyncData:
        """Extract phonemes from audio file"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available"""
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name"""
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of this provider"""
```

### lipkit.core.controller

#### LipSyncController
```python
class LipSyncController:
    """Manages the single controller object that drives all lip sync animations"""
    
    CONTROLLER_NAME_PREFIX = "LipKit_Controller"
    PROPERTY_NAME = "phoneme_index"
    
    @staticmethod
    def create_controller(
        name: Optional[str] = None,
        collection: Optional[bpy.types.Collection] = None
    ) -> bpy.types.Object:
        """Create a new lip sync controller object"""
    
    @staticmethod
    def get_controller(name: str) -> Optional[bpy.types.Object]:
        """Get controller object by name"""
    
    @staticmethod
    def find_controllers() -> list:
        """Find all LipKit controllers in the scene"""
    
    @staticmethod
    def is_controller(obj: bpy.types.Object) -> bool:
        """Check if object is a LipKit controller"""
    
    @staticmethod
    def add_keyframe(
        controller: bpy.types.Object,
        frame: int,
        phoneme_index: int,
        interpolation: str = 'CONSTANT'
    ) -> None:
        """Add a keyframe to the controller"""
    
    @staticmethod
    def clear_animation(controller: bpy.types.Object) -> None:
        """Clear all animation from controller"""
    
    @staticmethod
    def create_action(
        controller: bpy.types.Object,
        action_name: str,
        frame_data: Dict[int, int]
    ) -> bpy.types.Action:
        """Create an action with keyframes"""
    
    @staticmethod
    def create_nla_strip(
        controller: bpy.types.Object,
        action: bpy.types.Action,
        track_name: str = "LipSync",
        start_frame: int = 1
    ) -> bpy.types.NlaStrip:
        """Create an NLA strip from an action"""
```

### lipkit.core.mapping

#### PhonemeMapping
```python
class PhonemeMapping:
    """Manages mapping between phonemes and visual targets"""
    
    def __init__(self):
        self.mappings: Dict[str, Any] = {}
        self.name: str = "Untitled Mapping"
        self.description: str = ""
        self.phoneme_set: str = "arpabet"
        self.visual_system: str = "gp_layer"
        self.target_object: str = ""
    
    def add_mapping(
        self,
        phoneme: str,
        phoneme_index: int,
        target_name: str,
        **kwargs
    ) -> None:
        """Add a phoneme-to-target mapping"""
    
    def get_mapping(self, phoneme: str) -> Optional[Dict]:
        """Get mapping for a phoneme"""
    
    def get_target_for_phoneme(self, phoneme: str) -> Optional[str]:
        """Get target name for a phoneme"""
    
    def get_index_for_phoneme(self, phoneme: str) -> Optional[int]:
        """Get controller index for a phoneme"""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PhonemeMapping':
        """Create from dictionary"""
    
    def save_to_file(self, filepath: str) -> None:
        """Save mapping to JSON file"""
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'PhonemeMapping':
        """Load mapping from JSON file"""
```

#### PresetManager
```python
class PresetManager:
    """Manages phoneme preset files"""
    
    @staticmethod
    def get_presets_dir() -> Path:
        """Get the presets directory"""
    
    @staticmethod
    def get_available_presets() -> List[str]:
        """Get list of available preset files"""
    
    @staticmethod
    def load_preset(preset_name: str) -> Optional[dict]:
        """Load a preset by name"""
    
    @staticmethod
    def save_preset(preset_name: str, data: dict) -> None:
        """Save a preset"""
    
    @staticmethod
    def get_phoneme_to_viseme_map(preset_name: str) -> Dict[str, int]:
        """Get phoneme -> index mapping from preset"""
```

#### VisemeMapper
```python
class VisemeMapper:
    """Maps phonemes to visemes (visual mouth shapes)"""
    
    STANDARD_VISEMES = {
        "REST": ["REST", "SIL", "SP"],
        "AH": ["AA", "AE", "AH", "AW", "AY", "K", "G", "HH", "NG"],
        "EE": ["IH", "IY", "EH", "EY", "Y"],
        "OH": ["AO", "OW", "OY", "ER", "R"],
        "OO": ["UH", "UW", "W"],
        "M": ["M", "B", "P"],
        "F": ["F", "V"],
        "L": ["L", "D", "T", "N", "DH", "TH"],
        "S": ["S", "Z", "SH", "ZH", "CH", "JH"],
    }
    
    @staticmethod
    def phoneme_to_viseme(phoneme: str) -> str:
        """Convert a phoneme to its corresponding viseme"""
    
    @staticmethod
    def get_viseme_index(viseme: str) -> int:
        """Get standard index for a viseme"""
    
    @staticmethod
    def create_viseme_mapping(phoneme_list: List[str]) -> Dict[str, Dict[str, Any]]:
        """Create mapping from phonemes to visemes with indices"""
```

### lipkit.core.animation_engine

#### AnimationEngine
```python
class AnimationEngine:
    """Main animation engine that converts phoneme data into Blender keyframes"""
    
    def __init__(
        self,
        lipsync_data: LipSyncData,
        mapping: PhonemeMapping,
        controller: bpy.types.Object
    ):
        """Initialize animation engine"""
    
    def generate(
        self,
        target_object: bpy.types.Object,
        start_frame: int = 1,
        fps: Optional[float] = None,
        use_nla: bool = False,
        action_name: str = "LipSync"
    ) -> Dict[str, any]:
        """
        Generate lip sync animation
        
        Returns:
            Dictionary with generation results:
            {
                "success": True,
                "keyframes_created": 247,
                "drivers_created": 9,
                "start_frame": 1,
                "end_frame": 300,
                "phoneme_count": 247,
                "unique_phonemes": 9
            }
        """
    
    def preview_at_time(self, time_seconds: float, fps: Optional[float] = None) -> str:
        """Get which phoneme is active at a given time"""
```

#### Quick Generation Function
```python
def quick_generate(
    audio_path: str,
    target_object: bpy.types.Object,
    visual_system_type: str = "gp_layer",
    preset_name: str = "preston_blair",
    start_frame: int = 1,
    use_mock_data: bool = True
) -> Dict[str, any]:
    """
    Quick generation function for simple workflows
    
    Example:
        results = quick_generate(
            "/path/to/audio.wav",
            bpy.data.objects["GP_Mouth"],
            visual_system_type="gp_layer",
            preset_name="preston_blair"
        )
        print(f"Created {results['keyframes_created']} keyframes")
    """
```

## Phoneme Providers

### lipkit.phoneme_providers.LocalPhonemeProvider
```python
class LocalPhonemeProvider(PhonemeProvider):
    """Local phoneme extraction using external tools"""
    
    def __init__(self, tool_path: str = ""):
        """
        Args:
            tool_path: Path to phoneme extraction tool (Rhubarb, Allosaurus)
        """
    
    @property
    def name(self) -> str:
        return "Local (Free)"
```

### lipkit.phoneme_providers.APIPhonemeProvider
```python
class APIPhonemeProvider(PhonemeProvider):
    """Cloud API phoneme extraction service"""
    
    def __init__(
        self, 
        api_key: str = "",
        endpoint: str = "https://api.lipkit.dev/v1/phonemes"
    ):
        """
        Args:
            api_key: API key for authentication
            endpoint: API endpoint URL
        """
    
    @property
    def name(self) -> str:
        return "LipKit Cloud API (Premium)"
```

### lipkit.phoneme_providers.CustomAPIProvider
```python
class CustomAPIProvider(PhonemeProvider):
    """Custom API endpoint provider"""
    
    def __init__(
        self, 
        endpoint: str,
        api_key: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        """
        Args:
            endpoint: Custom API endpoint URL
            api_key: Optional API key
            headers: Optional custom headers
        """
```

## Visual Systems

### lipkit.visual_systems.VisualSystem (Abstract)
```python
class VisualSystem(ABC):
    """Abstract base class for visual systems"""
    
    @abstractmethod
    def create_driver(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_index: int,
        **kwargs
    ) -> bpy.types.FCurve:
        """Create a driver that activates target when controller == phoneme_index"""
    
    @abstractmethod
    def validate_target(self, target_object: bpy.types.Object, **kwargs) -> bool:
        """Validate that target object is compatible"""
    
    @property
    @abstractmethod
    def system_name(self) -> str:
        """Human-readable name"""
    
    @property
    @abstractmethod
    def system_type(self) -> str:
        """Unique identifier"""
```

### lipkit.visual_systems.GreasePencilLayerSystem
```python
class GreasePencilLayerSystem(VisualSystem):
    """Visual system for Grease Pencil layers"""
    
    def create_driver(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_index: int,
        layer_name: str,  # Required kwarg
        blend_range: int = 0  # Optional: smooth blending
    ) -> bpy.types.FCurve:
        """Create driver for GP layer opacity"""
    
    def setup_all_layers(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_mapping: Dict[str, str]
    ) -> List[bpy.types.FCurve]:
        """Set up drivers for all layers"""
```

### lipkit.visual_systems.ShapeKeySystem
```python
class ShapeKeySystem(VisualSystem):
    """Visual system for 3D shape keys"""
    
    def create_driver(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_index: int,
        shape_key_name: str,  # Required kwarg
        blend_range: int = 0
    ) -> bpy.types.FCurve:
        """Create driver for shape key value"""
    
    def setup_all_shape_keys(
        self,
        controller: bpy.types.Object,
        target_object: bpy.types.Object,
        phoneme_mapping: Dict[str, str]
    ) -> List[bpy.types.FCurve]:
        """Set up drivers for all shape keys"""
```

### Registering Custom Systems
```python
from lipkit.visual_systems import register_visual_system, VisualSystem

class MyCustomSystem(VisualSystem):
    # Implementation
    pass

register_visual_system("my_system", MyCustomSystem())
```

## Utilities

### lipkit.utils.audio_utils
```python
def get_audio_from_vse(strip_name: str) -> Optional[str]:
    """Extract audio file path from VSE strip"""

def get_vse_strip_info(strip_name: str) -> Optional[dict]:
    """Get information about a VSE sound strip"""

def get_all_sound_strips() -> list:
    """Get list of all sound strips in VSE"""

def validate_audio_file(filepath: str) -> Tuple[bool, str]:
    """Validate audio file - returns (is_valid, error_message)"""

def save_to_cache(
    audio_path: str,
    language: str,
    provider: str,
    lipsync_data: LipSyncData
) -> None:
    """Save phoneme data to cache"""

def load_from_cache(
    audio_path: str,
    language: str,
    provider: str
) -> Optional[LipSyncData]:
    """Load phoneme data from cache"""

def time_to_frame(time_seconds: float, fps: float) -> int:
    """Convert time in seconds to frame number"""

def frame_to_time(frame: int, fps: float) -> float:
    """Convert frame number to time in seconds"""
```

## Complete Usage Example

```python
import bpy
from lipkit.core import (
    LipSyncController,
    PhonemeMapping,
    AnimationEngine,
    PresetManager
)
from lipkit.phoneme_providers import LocalPhonemeProvider
from lipkit.visual_systems import GreasePencilLayerSystem

# 1. Extract phonemes
provider = LocalPhonemeProvider(tool_path="/usr/local/bin/rhubarb")
lipsync_data = provider.extract_phonemes(
    "/path/to/dialogue.wav",
    language="en"
)

print(f"Extracted {len(lipsync_data.phonemes)} phonemes")

# 2. Create controller
controller = LipSyncController.create_controller(name="Dialogue_Controller")

# 3. Set up mapping
mapping = PhonemeMapping()
mapping.name = "Character_Dialogue"
mapping.visual_system = "gp_layer"
mapping.target_object = "GP_Mouth"
mapping.phoneme_set = "preston_blair"

# Load preset
preset_data = PresetManager.load_preset("preston_blair")
for item in preset_data["mappings"]:
    mapping.add_mapping(
        phoneme=item["phoneme"],
        phoneme_index=item["index"],
        target_name=f"Mouth_{item['phoneme']}"
    )

# 4. Generate animation
mouth_obj = bpy.data.objects["GP_Mouth"]
engine = AnimationEngine(lipsync_data, mapping, controller)

results = engine.generate(
    mouth_object=mouth_obj,
    start_frame=1,
    fps=24,
    use_nla=True,
    action_name="Dialogue_LipSync"
)

print(f"Success! Created {results['keyframes_created']} keyframes")
print(f"Timeline frames: {results['start_frame']} to {results['end_frame']}")
```

## Error Handling

All providers and engines raise specific exceptions:

```python
from lipkit.core import (
    AudioFileError,
    ExtractionError,
    NetworkError
)

try:
    lipsync_data = provider.extract_phonemes(audio_path)
except AudioFileError as e:
    print(f"Audio file issue: {e}")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
except NetworkError as e:
    print(f"Network issue: {e}")
```
