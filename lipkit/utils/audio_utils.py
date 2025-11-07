"""
Audio handling utilities
"""

import bpy
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple
from ..core import LipSyncData


def get_audio_from_vse(strip_name: str) -> Optional[str]:
    """
    Extract audio file path from Video Sequence Editor strip
    
    Args:
        strip_name: Name of the sound strip
        
    Returns:
        Absolute path to audio file, or None if not found
    """
    scene = bpy.context.scene
    
    if not scene.sequence_editor:
        return None
    
    # Find the strip
    strip = scene.sequence_editor.sequences_all.get(strip_name)
    
    if not strip:
        return None
    
    if strip.type != 'SOUND':
        return None
    
    # Get absolute path
    return bpy.path.abspath(strip.sound.filepath)


def get_vse_strip_info(strip_name: str) -> Optional[dict]:
    """
    Get information about a VSE sound strip
    
    Returns:
        Dictionary with strip info: start_frame, duration_frames, fps, audio_path
    """
    scene = bpy.context.scene
    
    if not scene.sequence_editor:
        return None
    
    strip = scene.sequence_editor.sequences_all.get(strip_name)
    
    if not strip or strip.type != 'SOUND':
        return None
    
    return {
        "start_frame": strip.frame_start,
        "duration_frames": strip.frame_final_duration,
        "fps": scene.render.fps,
        "audio_path": bpy.path.abspath(strip.sound.filepath),
        "channel": strip.channel,
    }


def get_all_sound_strips() -> list:
    """
    Get list of all sound strips in VSE
    
    Returns:
        List of (strip_name, strip_object) tuples
    """
    scene = bpy.context.scene
    
    if not scene.sequence_editor:
        return []
    
    sound_strips = []
    for strip in scene.sequence_editor.sequences_all:
        if strip.type == 'SOUND':
            sound_strips.append((strip.name, strip))
    
    return sound_strips


def validate_audio_file(filepath: str) -> Tuple[bool, str]:
    """
    Validate audio file exists and is readable
    
    Returns:
        (is_valid, error_message)
    """
    if not filepath:
        return False, "No file path provided"
    
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    if not os.path.isfile(filepath):
        return False, f"Path is not a file: {filepath}"
    
    # Check file extension
    valid_extensions = {'.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac'}
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext not in valid_extensions:
        return False, f"Unsupported audio format: {ext}"
    
    # Check file size
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return False, "Audio file is empty"
    
    # Basic validation passed
    return True, ""


def get_audio_duration(filepath: str) -> float:
    """
    Get duration of audio file in seconds
    
    This is a simplified version - in production would use a proper audio library
    
    Returns:
        Duration in seconds, or 0.0 if unable to determine
    """
    # Try to load as Blender sound
    try:
        sound = bpy.data.sounds.load(filepath, check_existing=True)
        # Blender doesn't expose duration directly in a simple way
        # Would need to use external library like librosa or pydub
        # For now, return a placeholder
        return 5.0
    except:
        return 0.0


def get_cache_dir() -> Path:
    """Get cache directory for phoneme data"""
    # Use Blender's temp directory
    temp_dir = Path(bpy.app.tempdir)
    cache_dir = temp_dir / "lipkit_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def get_cache_key(audio_path: str, language: str, provider: str) -> str:
    """
    Generate cache key for phoneme data
    
    Args:
        audio_path: Path to audio file
        language: Language code
        provider: Provider name
        
    Returns:
        Cache key string
    """
    # Hash audio file content + language + provider
    with open(audio_path, 'rb') as f:
        audio_hash = hashlib.md5(f.read()).hexdigest()
    
    cache_string = f"{audio_hash}_{language}_{provider}"
    return hashlib.md5(cache_string.encode()).hexdigest()


def save_to_cache(
    audio_path: str,
    language: str,
    provider: str,
    lipsync_data: LipSyncData
) -> None:
    """
    Save phoneme data to cache
    
    Args:
        audio_path: Path to audio file
        language: Language code
        provider: Provider name
        lipsync_data: LipSync data to cache
    """
    cache_dir = get_cache_dir()
    cache_key = get_cache_key(audio_path, language, provider)
    cache_file = cache_dir / f"{cache_key}.json"
    
    with open(cache_file, 'w') as f:
        json.dump(lipsync_data.to_dict(), f)


def load_from_cache(
    audio_path: str,
    language: str,
    provider: str
) -> Optional[LipSyncData]:
    """
    Load phoneme data from cache
    
    Returns:
        LipSyncData if found in cache, None otherwise
    """
    try:
        cache_dir = get_cache_dir()
        cache_key = get_cache_key(audio_path, language, provider)
        cache_file = cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        return LipSyncData.from_dict(data)
    
    except Exception as e:
        print(f"Failed to load from cache: {e}")
        return None


def clear_cache() -> None:
    """Clear all cached phoneme data"""
    cache_dir = get_cache_dir()
    
    for cache_file in cache_dir.glob("*.json"):
        try:
            cache_file.unlink()
        except:
            pass


def time_to_frame(time_seconds: float, fps: float) -> int:
    """Convert time in seconds to frame number"""
    return round(time_seconds * fps)


def frame_to_time(frame: int, fps: float) -> float:
    """Convert frame number to time in seconds"""
    return frame / fps
