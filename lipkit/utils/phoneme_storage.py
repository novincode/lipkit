"""
Phoneme Data Storage - saves analyzed phoneme data inside .blend file
Uses bpy.data.texts to store JSON data - persists with the file!
"""

import bpy
import json
import hashlib
from typing import Optional, Tuple, List
from pathlib import Path
from ..core import LipSyncData


def get_audio_hash(audio_path: str) -> str:
    """Get MD5 hash of audio file content"""
    try:
        with open(audio_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"[LipKit] Failed to hash audio: {e}")
        return ""


def get_storage_name(audio_hash: str) -> str:
    """Get the bpy.data.texts name for storing phoneme data"""
    return f".lipkit_phoneme_{audio_hash}"


def save_phoneme_data(audio_path: str, lipsync_data: LipSyncData) -> Tuple[bool, str]:
    """
    Save phoneme data to bpy.data.texts (stored inside .blend file)
    
    Args:
        audio_path: Path to the audio file
        lipsync_data: The phoneme data to save
        
    Returns:
        (success, message)
    """
    try:
        # Get audio hash
        audio_hash = get_audio_hash(audio_path)
        if not audio_hash:
            return False, "Failed to hash audio file"
        
        # Create storage name
        storage_name = get_storage_name(audio_hash)
        
        # Prepare data with metadata
        data = {
            "audio_hash": audio_hash,
            "audio_filename": Path(audio_path).name,
            "phoneme_data": lipsync_data.to_dict()
        }
        
        # Convert to JSON
        json_str = json.dumps(data, indent=2)
        
        # Save to bpy.data.texts (create or update)
        if storage_name in bpy.data.texts:
            text_block = bpy.data.texts[storage_name]
            text_block.clear()
        else:
            text_block = bpy.data.texts.new(storage_name)
        
        text_block.from_string(json_str)
        
        return True, f"✓ Saved phoneme data for {Path(audio_path).name}"
    
    except Exception as e:
        return False, f"Failed to save: {str(e)}"


def load_phoneme_data(audio_path: str) -> Tuple[bool, Optional[LipSyncData], str]:
    """
    Load phoneme data from bpy.data.texts
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        (success, lipsync_data_or_none, message)
    """
    try:
        # Get audio hash
        audio_hash = get_audio_hash(audio_path)
        if not audio_hash:
            return False, None, "Failed to hash audio file"
        
        # Check if data exists
        storage_name = get_storage_name(audio_hash)
        
        if storage_name not in bpy.data.texts:
            return False, None, "No saved data for this audio file"
        
        # Load and parse JSON
        text_block = bpy.data.texts[storage_name]
        json_str = text_block.as_string()
        data = json.loads(json_str)
        
        # Verify hash matches
        if data.get("audio_hash") != audio_hash:
            return False, None, "Audio file has changed - data is outdated"
        
        # Parse phoneme data
        lipsync_data = LipSyncData.from_dict(data["phoneme_data"])
        
        filename = data.get("audio_filename", Path(audio_path).name)
        return True, lipsync_data, f"✓ Loaded phoneme data for {filename}"
    
    except Exception as e:
        return False, None, f"Failed to load: {str(e)}"


def has_phoneme_data(audio_path: str) -> bool:
    """Check if phoneme data exists for this audio file"""
    try:
        audio_hash = get_audio_hash(audio_path)
        if not audio_hash:
            return False
        
        storage_name = get_storage_name(audio_hash)
        return storage_name in bpy.data.texts
    
    except:
        return False


def delete_phoneme_data(audio_path: str) -> Tuple[bool, str]:
    """
    Delete saved phoneme data for an audio file
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        (success, message)
    """
    try:
        audio_hash = get_audio_hash(audio_path)
        if not audio_hash:
            return False, "Failed to hash audio file"
        
        storage_name = get_storage_name(audio_hash)
        
        if storage_name not in bpy.data.texts:
            return False, "No data to delete"
        
        # Remove the text block
        text_block = bpy.data.texts[storage_name]
        bpy.data.texts.remove(text_block)
        
        return True, "✓ Phoneme data deleted"
    
    except Exception as e:
        return False, f"Failed to delete: {str(e)}"


def list_all_stored_data() -> List[Tuple[str, str]]:
    """
    List all stored phoneme data
    
    Returns:
        List of (audio_hash, filename) tuples
    """
    stored = []
    
    for text_block in bpy.data.texts:
        if text_block.name.startswith(".lipkit_phoneme_"):
            try:
                data = json.loads(text_block.as_string())
                audio_hash = data.get("audio_hash", "")
                filename = data.get("audio_filename", "Unknown")
                stored.append((audio_hash, filename))
            except:
                pass
    
    return stored


def cleanup_all_data() -> int:
    """
    Remove all LipKit phoneme data from the blend file
    
    Returns:
        Number of items removed
    """
    count = 0
    
    to_remove = [
        text_block for text_block in bpy.data.texts
        if text_block.name.startswith(".lipkit_phoneme_")
    ]
    
    for text_block in to_remove:
        bpy.data.texts.remove(text_block)
        count += 1
    
    return count
