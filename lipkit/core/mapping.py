"""
Mapping system - converts phonemes to visual targets
Handles loading/saving presets and phoneme-to-viseme mappings
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class PhonemeMapping:
    """
    Manages mapping between phonemes and visual targets
    """
    
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
        """
        Add a phoneme-to-target mapping
        
        Args:
            phoneme: Phoneme string (e.g., "AH", "EE")
            phoneme_index: Integer index for controller
            target_name: Name of target (layer name, shape key name, etc.)
            **kwargs: Additional properties (blend_range, etc.)
        """
        self.mappings[phoneme] = {
            "index": phoneme_index,
            "target": target_name,
            **kwargs
        }
    
    def get_mapping(self, phoneme: str) -> Optional[Dict]:
        """Get mapping for a phoneme"""
        return self.mappings.get(phoneme)
    
    def get_target_for_phoneme(self, phoneme: str) -> Optional[str]:
        """Get target name for a phoneme"""
        mapping = self.get_mapping(phoneme)
        return mapping["target"] if mapping else None
    
    def get_index_for_phoneme(self, phoneme: str) -> Optional[int]:
        """Get controller index for a phoneme"""
        mapping = self.get_mapping(phoneme)
        return mapping["index"] if mapping else None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "phoneme_set": self.phoneme_set,
            "visual_system": self.visual_system,
            "target_object": self.target_object,
            "mappings": self.mappings
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PhonemeMapping':
        """Create from dictionary"""
        mapping = cls()
        mapping.name = data.get("name", "Untitled")
        mapping.description = data.get("description", "")
        mapping.phoneme_set = data.get("phoneme_set", "arpabet")
        mapping.visual_system = data.get("visual_system", "gp_layer")
        mapping.target_object = data.get("target_object", "")
        mapping.mappings = data.get("mappings", {})
        return mapping
    
    def save_to_file(self, filepath: str) -> None:
        """Save mapping to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'PhonemeMapping':
        """Load mapping from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class PresetManager:
    """
    Manages phoneme preset files
    """
    
    @staticmethod
    def get_presets_dir() -> Path:
        """Get the presets directory"""
        addon_dir = Path(__file__).parent.parent
        return addon_dir / "presets"
    
    @staticmethod
    def get_available_presets() -> List[str]:
        """Get list of available preset files"""
        presets_dir = PresetManager.get_presets_dir()
        
        if not presets_dir.exists():
            return []
        
        presets = []
        for file in presets_dir.glob("*.json"):
            presets.append(file.stem)
        
        return sorted(presets)
    
    @staticmethod
    def load_preset(preset_name: str) -> Optional[dict]:
        """
        Load a preset by name
        
        Args:
            preset_name: Name of preset (without .json extension)
            
        Returns:
            Preset data dictionary or None if not found
        """
        presets_dir = PresetManager.get_presets_dir()
        preset_path = presets_dir / f"{preset_name}.json"
        
        if not preset_path.exists():
            return None
        
        with open(preset_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_preset(preset_name: str, data: dict) -> None:
        """
        Save a preset
        
        Args:
            preset_name: Name for preset (without .json extension)
            data: Preset data dictionary
        """
        presets_dir = PresetManager.get_presets_dir()
        presets_dir.mkdir(exist_ok=True)
        
        preset_path = presets_dir / f"{preset_name}.json"
        
        with open(preset_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def get_phoneme_to_viseme_map(preset_name: str) -> Dict[str, int]:
        """
        Get a simplified phoneme -> index mapping from a preset
        
        Args:
            preset_name: Name of preset
            
        Returns:
            Dictionary mapping phoneme strings to indices
        """
        preset = PresetManager.load_preset(preset_name)
        if not preset:
            return {}
        
        mapping = {}
        for item in preset.get("mappings", []):
            phoneme = item.get("phoneme", "")
            index = item.get("index", 0)
            mapping[phoneme] = index
        
        return mapping
    
    @staticmethod
    def create_default_presets() -> None:
        """Create default preset files if they don't exist"""
        # This is called on addon initialization
        # Presets are already in the presets/ directory
        pass


class VisemeMapper:
    """
    Maps phonemes to visemes (visual mouth shapes)
    Handles phoneme-to-viseme reduction for simplified animation
    """
    
    # Standard viseme groupings
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
        """
        Convert a phoneme to its corresponding viseme
        
        Args:
            phoneme: Phoneme string (e.g., "AA", "IY")
            
        Returns:
            Viseme string (e.g., "AH", "EE")
        """
        phoneme = phoneme.upper()
        
        for viseme, phoneme_list in VisemeMapper.STANDARD_VISEMES.items():
            if phoneme in phoneme_list:
                return viseme
        
        # Default to REST if not found
        return "REST"
    
    @staticmethod
    def get_viseme_index(viseme: str) -> int:
        """Get standard index for a viseme"""
        viseme_order = ["REST", "AH", "EE", "OH", "OO", "M", "F", "L", "S"]
        try:
            return viseme_order.index(viseme.upper())
        except ValueError:
            return 0  # Default to REST
    
    @staticmethod
    def create_viseme_mapping(
        phoneme_list: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create a mapping from phonemes to visemes with indices
        
        Args:
            phoneme_list: List of phonemes to map
            
        Returns:
            Dictionary mapping phoneme -> {viseme, index}
        """
        mapping = {}
        
        for phoneme in phoneme_list:
            viseme = VisemeMapper.phoneme_to_viseme(phoneme)
            index = VisemeMapper.get_viseme_index(viseme)
            
            mapping[phoneme] = {
                "viseme": viseme,
                "index": index
            }
        
        return mapping
