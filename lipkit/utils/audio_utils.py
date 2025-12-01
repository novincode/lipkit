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


def get_audio_from_vse(strip_identifier: str) -> Optional[str]:
    """
    Extract audio file path from Video Sequence Editor strip or direct sound
    
    Args:
        strip_identifier: Strip identifier in format:
            - "scene_name::strip_name" (VSE strip)
            - "SOUND::sound_name" (direct sound from bpy.data.sounds)
            - "strip_name" (legacy fallback - current scene)
        
    Returns:
        Absolute path to audio file, or None if not found
    """
    # Handle direct sound reference (from bpy.data.sounds)
    if strip_identifier.startswith("SOUND::"):
        sound_name = strip_identifier[7:]  # Remove "SOUND::" prefix
        sound = bpy.data.sounds.get(sound_name)
        if sound and sound.filepath:
            return bpy.path.abspath(sound.filepath)
        return None
    
    # Handle scene::strip format
    if "::" in strip_identifier:
        scene_name, strip_name = strip_identifier.split("::", 1)
        scene = bpy.data.scenes.get(scene_name)
    else:
        # Fallback: try current scene
        scene = bpy.context.scene
        strip_name = strip_identifier
    
    if not scene:
        return None
    
    # Get sequence editor
    seq_editor = getattr(scene, 'sequence_editor', None)
    if not seq_editor:
        return None
    
    # Try to get sequences
    sequences = None
    if hasattr(seq_editor, 'sequences_all') and seq_editor.sequences_all:
        sequences = seq_editor.sequences_all
    elif hasattr(seq_editor, 'sequences') and seq_editor.sequences:
        sequences = seq_editor.sequences
    
    if not sequences:
        return None
    
    # Find the strip
    strip = sequences.get(strip_name)
    
    if not strip:
        return None
    
    if strip.type != 'SOUND':
        return None
    
    # Get sound and return absolute path
    sound = getattr(strip, 'sound', None)
    if sound and sound.filepath:
        return bpy.path.abspath(sound.filepath)
    
    return None


def get_vse_strip_info(strip_identifier: str) -> Optional[dict]:
    """
    Get information about a VSE sound strip
    
    Args:
        strip_identifier: Strip identifier in format "scene_name::strip_name" or just "strip_name"
    
    Returns:
        Dictionary with strip info: start_frame, duration_frames, fps, audio_path
    """
    # Parse the identifier
    if "::" in strip_identifier:
        scene_name, strip_name = strip_identifier.split("::", 1)
        scene = bpy.data.scenes.get(scene_name)
    else:
        scene = bpy.context.scene
        strip_name = strip_identifier
    
    if not scene or not scene.sequence_editor:
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
        "scene": scene.name,
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


def save_phoneme_data_to_file(filepath: str, lipsync_data: LipSyncData) -> Tuple[bool, str]:
    """
    Save phoneme data to a JSON file (user-specified location)
    
    Args:
        filepath: User-selected file path
        lipsync_data: LipSync data to save
        
    Returns:
        (success, message)
    """
    try:
        # Ensure .json extension
        if not filepath.endswith('.json'):
            filepath += '.json'
        
        with open(filepath, 'w') as f:
            json.dump(lipsync_data.to_dict(), f, indent=2)
        
        return True, f"Saved phoneme data to: {filepath}"
    except Exception as e:
        return False, f"Failed to save: {str(e)}"


def load_phoneme_data_from_file(filepath: str) -> Tuple[bool, Optional[LipSyncData], str]:
    """
    Load phoneme data from a JSON file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        (success, lipsync_data_or_none, message)
    """
    try:
        if not os.path.exists(filepath):
            return False, None, f"File not found: {filepath}"
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        lipsync_data = LipSyncData.from_dict(data)
        return True, lipsync_data, f"Loaded phoneme data from: {filepath}"
    
    except Exception as e:
        return False, None, f"Failed to load: {str(e)}"


def time_to_frame(time_seconds: float, fps: float) -> int:
    """Convert time in seconds to frame number"""
    return round(time_seconds * fps)


def frame_to_time(frame: int, fps: float) -> float:
    """Convert frame number to time in seconds"""
    return frame / fps


def convert_audio_to_wav(input_path: str, output_path: str = None) -> Tuple[bool, str]:
    """
    Convert audio file to WAV format
    
    Supports: MP3, M4A, OGG, FLAC, AAC
    Uses ffmpeg if available
    
    Args:
        input_path: Path to input audio file
        output_path: Path for output WAV (default: same name with .wav)
        
    Returns:
        (success, output_path_or_error_message)
    """
    import subprocess
    
    if not os.path.exists(input_path):
        return False, f"File not found: {input_path}"
    
    # Check if already WAV
    if input_path.lower().endswith('.wav'):
        return True, input_path
    
    # Generate output path if not provided
    if output_path is None:
        base_path = os.path.splitext(input_path)[0]
        output_path = base_path + "_converted.wav"
    
    # Check if ffmpeg is available
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=2
        )
        if result.returncode != 0:
            return False, "ffmpeg not found. Please install ffmpeg to convert audio formats."
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "ffmpeg not found. Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
    
    # Convert to WAV
    try:
        print(f"🔄 Converting {os.path.basename(input_path)} to WAV...")
        
        result = subprocess.run(
            [
                'ffmpeg',
                '-i', input_path,
                '-acodec', 'pcm_s16le',  # Standard WAV codec
                '-ar', '16000',           # 16kHz is good for speech
                '-y',                      # Overwrite output file
                output_path
            ],
            capture_output=True,
            timeout=60
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"✅ Converted to: {output_path}")
            return True, output_path
        else:
            error = result.stderr.decode('utf-8', errors='ignore')
            return False, f"ffmpeg conversion failed: {error}"
    
    except subprocess.TimeoutExpired:
        return False, "Audio conversion timed out (> 60 seconds)"
    except Exception as e:
        return False, f"Conversion error: {str(e)}"
