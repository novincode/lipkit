"""
Rhubarb Lip Sync Manager
Handles automatic download, extraction, and setup of Rhubarb

Copyright (C) 2024-2025 Shayan Moradi
SPDX-License-Identifier: GPL-3.0-or-later
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Tuple, Optional
import platform
import bpy


def is_online_access_allowed() -> bool:
    """
    Check if online access is allowed by user preference.
    Required by Blender Extension Guidelines (Rule 4.2).
    
    Returns:
        True if online access is permitted, False otherwise
    """
    # bpy.app.online_access is read-only and reflects user preference
    # plus any command-line overrides (--offline-mode / --online-mode)
    return getattr(bpy.app, 'online_access', True)


def get_rhubarb_cache_dir() -> Path:
    """Get the directory where Rhubarb should be installed.

    Blender extensions must not assume their own directory is writable.
    Prefer Blender's per-user extension directory so it survives upgrades.
    """
    # Blender 4.2+ provides bpy.utils.extension_path_user.
    try:
        # We want the top-level extension package id ("lipkit"), not "lipkit.utils".
        try:
            from .. import __package__ as base_package
            package_id = base_package
        except Exception:
            package_id = (__package__ or "").split('.')[0] or "lipkit"

        base_dir = bpy.utils.extension_path_user(package_id, path="", create=True)
        return Path(base_dir) / "rhubarb"
    except Exception:
        # Fallback: keep previous behavior if Blender API changes or is unavailable.
        if platform.system() == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Blender" / "lipkit_rhubarb"
        if platform.system() == "Windows":
            return Path.home() / "AppData" / "Local" / "Blender" / "lipkit_rhubarb"
        return Path.home() / ".local" / "share" / "Blender" / "lipkit_rhubarb"


def _is_within_directory(base_dir: Path, target_path: Path) -> bool:
    """Return True if target_path is within base_dir after resolving."""
    try:
        base_resolved = base_dir.resolve()
        target_resolved = target_path.resolve()
        return str(target_resolved).startswith(str(base_resolved) + os.sep) or target_resolved == base_resolved
    except Exception:
        return False


def _safe_extract_zip(zip_ref, dest_dir: Path) -> None:
    for member in zip_ref.infolist():
        member_path = dest_dir / member.filename
        if not _is_within_directory(dest_dir, member_path):
            raise ValueError(f"Unsafe path in zip: {member.filename}")
    zip_ref.extractall(dest_dir)


def _safe_extract_tar(tar_ref, dest_dir: Path) -> None:
    for member in tar_ref.getmembers():
        member_path = dest_dir / member.name
        if not _is_within_directory(dest_dir, member_path):
            raise ValueError(f"Unsafe path in tar: {member.name}")
    tar_ref.extractall(dest_dir)


def get_effective_rhubarb_path(props=None, prefs=None) -> Optional[str]:
    """
    Get the effective Rhubarb path from all possible sources.
    
    Priority:
    1. Scene property (props.rhubarb_path)
    2. Preferences manual path (prefs.local_tool_path)
    3. Auto-downloaded (get_rhubarb_executable())
    
    Args:
        props: Scene lipkit properties (optional)
        prefs: Addon preferences (optional)
    
    Returns:
        Path to rhubarb executable or None if not found anywhere
    """
    # Try scene-specific path first
    if props and hasattr(props, 'rhubarb_path') and props.rhubarb_path:
        if os.path.exists(props.rhubarb_path):
            return props.rhubarb_path
    
    # Try preferences manual path
    if prefs and hasattr(prefs, 'local_tool_path') and prefs.local_tool_path:
        if os.path.exists(prefs.local_tool_path):
            return prefs.local_tool_path
    
    # Try auto-downloaded
    auto_path = get_rhubarb_executable()
    if auto_path and os.path.exists(auto_path):
        return auto_path
    
    return None


def get_rhubarb_executable() -> Optional[str]:
    """
    Get path to Rhubarb executable if installed
    Searches recursively in cache directory
    Also ensures the file has execute permissions on Unix systems.
    
    Returns:
        Path to rhubarb executable or None if not found
    """
    cache_dir = get_rhubarb_cache_dir()
    
    if not cache_dir.exists():
        return None
    
    # Look for executable with correct name based on OS
    if platform.system() == "Windows":
        exe_name = "rhubarb.exe"
    else:
        exe_name = "rhubarb"
    
    # First try standard locations
    standard_paths = [
        cache_dir / "rhubarb" / exe_name,
        cache_dir / exe_name,
    ]
    
    exe_path = None
    
    for path in standard_paths:
        if path.exists() and path.is_file():
            exe_path = str(path)
            break
    
    # Search recursively if not found in standard locations
    if not exe_path:
        for root, dirs, files in os.walk(cache_dir):
            if exe_name in files:
                found_path = Path(root) / exe_name
                if found_path.is_file():
                    exe_path = str(found_path)
                    break
    
    # Ensure execute permissions on Unix
    if exe_path and platform.system() != "Windows":
        try:
            current_mode = os.stat(exe_path).st_mode
            if not (current_mode & 0o111):  # No execute bits set
                print(f"🔧 Setting execute permissions on {exe_path}")
                os.chmod(exe_path, current_mode | 0o755)
        except Exception as e:
            print(f"⚠️ Could not set execute permissions: {e}")
    
    return exe_path


def get_latest_rhubarb_release() -> Optional[dict]:
    """
    Fetch latest Rhubarb release info from GitHub API.
    Respects user's online access preference.
    
    Returns:
        Dict with 'version', 'download_url', 'filename'
        or None if unable to fetch
    """
    import urllib.request
    
    # Check online access permission first
    if not is_online_access_allowed():
        print("LipKit: Online access disabled - cannot fetch Rhubarb release info")
        return None
    
    try:
        url = "https://api.github.com/repos/DanielSWolf/rhubarb-lip-sync/releases/latest"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        version = data.get('tag_name', 'unknown')
        system = platform.system()
        
        # Map system names to Rhubarb release names
        if system == "Darwin":  # macOS
            # Look for macOS release
            for asset in data.get('assets', []):
                name = asset['name'].lower()
                if 'mac' in name or 'macos' in name:
                    return {
                        'version': version,
                        'download_url': asset['browser_download_url'],
                        'filename': asset['name']
                    }
        
        elif system == "Windows":
            for asset in data.get('assets', []):
                name = asset['name'].lower()
                if 'win' in name or 'windows' in name:
                    return {
                        'version': version,
                        'download_url': asset['browser_download_url'],
                        'filename': asset['name']
                    }
        
        elif system == "Linux":
            for asset in data.get('assets', []):
                name = asset['name'].lower()
                if 'linux' in name:
                    return {
                        'version': version,
                        'download_url': asset['browser_download_url'],
                        'filename': asset['name']
                    }
        
        return None
    
    except Exception as e:
        print(f"Failed to fetch Rhubarb release info: {e}")
        return None


def download_rhubarb() -> Tuple[bool, str]:
    """
    Download and extract latest Rhubarb release.
    Respects user's online access preference per Blender Extension Guidelines.
    
    Returns:
        (success, message_or_path)
    """
    import urllib.request
    import zipfile
    import tarfile
    
    # Check online access permission (Blender Extension Guidelines Rule 4.2)
    if not is_online_access_allowed():
        return False, (
            "Online access is disabled in Blender preferences.\n"
            "Enable 'Allow Online Access' in Edit → Preferences → System,\n"
            "or download Rhubarb manually from:\n"
            "https://github.com/DanielSWolf/rhubarb-lip-sync/releases"
        )
    
    # Get release info
    release_info = get_latest_rhubarb_release()
    if not release_info:
        return False, "Could not fetch Rhubarb release information from GitHub"
    
    cache_dir = get_rhubarb_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    download_url = release_info['download_url']
    filename = release_info['filename']
    download_path = cache_dir / filename
    
    print(f"📥 Downloading Rhubarb {release_info['version']}...")
    print(f"   URL: {download_url}")
    
    try:
        # Download the file
        urllib.request.urlretrieve(download_url, download_path)
        print(f"✅ Downloaded to: {download_path}")
        
        # Extract
        print(f"📦 Extracting...")
        
        if filename.endswith('.zip'):
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                _safe_extract_zip(zip_ref, cache_dir)
        
        elif filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            with tarfile.open(download_path, 'r:gz') as tar_ref:
                _safe_extract_tar(tar_ref, cache_dir)
        
        else:
            return False, f"Unsupported archive format: {filename}"
        
        print(f"✅ Extracted")
        
        # Clean up download
        try:
            os.remove(download_path)
        except:
            pass
        
        # Find executable
        exe_path = get_rhubarb_executable()
        if exe_path:
            print(f"✅ Ready at: {exe_path}")
            
            # Make executable on Unix systems
            if not exe_path.endswith('.exe'):
                try:
                    os.chmod(exe_path, 0o755)
                except:
                    pass
            
            return True, exe_path
        
        else:
            return False, "Could not find rhubarb executable after extraction"
    
    except Exception as e:
        return False, f"Download/extraction failed: {str(e)}"


def verify_rhubarb(exe_path: str) -> Tuple[bool, str]:
    """
    Verify Rhubarb is functional
    
    Returns:
        (is_valid, message)
    """
    if not os.path.exists(exe_path):
        return False, f"Executable not found: {exe_path}"
    
    try:
        result = subprocess.run(
            [exe_path, '--version'],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version_info = result.stdout.decode('utf-8', errors='ignore').strip()
            return True, f"Rhubarb ready: {version_info}"
        else:
            error = result.stderr.decode('utf-8', errors='ignore')
            return False, f"Rhubarb test failed: {error}"
    
    except subprocess.TimeoutExpired:
        return False, "Rhubarb version check timed out"
    except Exception as e:
        return False, f"Could not verify Rhubarb: {str(e)}"
