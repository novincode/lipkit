"""
Core data structures and abstract base for phoneme extraction
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class PhonemeSet(Enum):
    """Standard phoneme sets supported by LipKit"""
    PRESTON_BLAIR = "preston_blair"  # 9 classic shapes
    ARPAbet = "arpabet"  # English phonemes
    IPA = "ipa"  # International Phonetic Alphabet
    CUSTOM = "custom"  # User-defined


@dataclass
class PhonemeData:
    """Single phoneme with timing information"""
    phoneme: str  # e.g., "AH", "EE", "M", "REST"
    start_time: float  # seconds
    end_time: float  # seconds
    confidence: float = 1.0  # 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Duration of phoneme in seconds"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "phoneme": self.phoneme,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PhonemeData':
        """Create from dictionary"""
        return cls(
            phoneme=data["phoneme"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LipSyncData:
    """Complete lip sync data with phonemes and metadata"""
    phonemes: List[PhonemeData]
    duration: float  # total duration in seconds
    sample_rate: int = 44100
    language: str = "en"
    phoneme_set: str = PhonemeSet.ARPAbet.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "phonemes": [p.to_dict() for p in self.phonemes],
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "language": self.language,
            "phoneme_set": self.phoneme_set,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LipSyncData':
        """Create from dictionary"""
        return cls(
            phonemes=[PhonemeData.from_dict(p) for p in data["phonemes"]],
            duration=data["duration"],
            sample_rate=data.get("sample_rate", 44100),
            language=data.get("language", "en"),
            phoneme_set=data.get("phoneme_set", PhonemeSet.ARPAbet.value),
            metadata=data.get("metadata", {}),
        )
    
    def get_phoneme_at_time(self, time: float) -> Optional[PhonemeData]:
        """Get the phoneme active at a given time"""
        for phoneme in self.phonemes:
            if phoneme.start_time <= time < phoneme.end_time:
                return phoneme
        return None
    
    def get_frame_mapping(self, fps: float, start_frame: int = 1) -> Dict[int, PhonemeData]:
        """Map frames to phonemes"""
        frame_map = {}
        for phoneme in self.phonemes:
            frame = start_frame + int(phoneme.start_time * fps)
            frame_map[frame] = phoneme
        return frame_map


class PhonemeProvider(ABC):
    """Abstract base class for phoneme extraction providers"""
    
    @abstractmethod
    def extract_phonemes(
        self, 
        audio_path: str, 
        language: str = "en",
        **kwargs
    ) -> LipSyncData:
        """
        Extract phonemes from audio file
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr')
            **kwargs: Provider-specific options
            
        Returns:
            LipSyncData object with phoneme timing information
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available and properly configured"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this provider"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of this provider"""
        pass
    
    def validate_audio(self, audio_path: str) -> bool:
        """Validate audio file exists and is readable"""
        import os
        return os.path.exists(audio_path) and os.path.isfile(audio_path)


class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class AudioFileError(ProviderError):
    """Error related to audio file"""
    pass


class ExtractionError(ProviderError):
    """Error during phoneme extraction"""
    pass


class NetworkError(ProviderError):
    """Network-related error for API providers"""
    pass
