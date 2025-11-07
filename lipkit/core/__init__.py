"""
Core module for phoneme extraction and lip sync data structures
"""

from .phoneme_engine import (
    PhonemeData,
    LipSyncData,
    PhonemeProvider,
    PhonemeSet,
    ProviderError,
    AudioFileError,
    ExtractionError,
    NetworkError,
)
from .controller import LipSyncController
from .mapping import PhonemeMapping, PresetManager, VisemeMapper
from .animation_engine import AnimationEngine

__all__ = [
    'PhonemeData',
    'LipSyncData',
    'PhonemeProvider',
    'PhonemeSet',
    'ProviderError',
    'AudioFileError',
    'ExtractionError',
    'NetworkError',
    'LipSyncController',
    'PhonemeMapping',
    'PresetManager',
    'VisemeMapper',
    'AnimationEngine',
]
