#!/usr/bin/env python3
"""
Build script for LipKit Blender Extension

Creates a single lipkit.zip that works for:
  - Blender Extensions Platform (extensions.blender.org)
  - GitHub releases
  - Direct "Install from Disk" installation

Copyright (C) 2024-2025 Shayan Moradi
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os
import zipfile
import shutil
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
LIPKIT_SOURCE = REPO_ROOT / "lipkit"
BUILD_DIR = REPO_ROOT / "build"
DIST_DIR = BUILD_DIR / "dist"

# Files/folders to exclude from the build
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.pyc',
    '.git',
    '.DS_Store',
    'Thumbs.db',
]


def should_exclude(path: Path) -> bool:
    """Check if a path should be excluded from the build"""
    path_str = str(path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True
    return False


def create_extension_zip():
    """
    Create lipkit.zip - the Blender extension package.
    
    This single zip works for:
    - extensions.blender.org submission
    - GitHub releases  
    - Direct installation via "Install from Disk"
    """
    zip_name = "lipkit.zip"
    zip_path = DIST_DIR / zip_name
    
    print(f"📦 Building {zip_name}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(LIPKIT_SOURCE):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(Path(d))]
            
            for file in files:
                file_path = Path(root) / file
                
                if should_exclude(file_path):
                    continue
                
                # Archive path: lipkit/...
                arcname = Path("lipkit") / file_path.relative_to(LIPKIT_SOURCE)
                zipf.write(file_path, arcname)
                
    return zip_path


def main():
    # Create directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    
    # Clean previous build
    for old_zip in DIST_DIR.glob("*.zip"):
        old_zip.unlink()
    
    # Build extension zip
    zip_path = create_extension_zip()
    
    # Get version from manifest
    version = "unknown"
    manifest_path = LIPKIT_SOURCE / "blender_manifest.toml"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            for line in f:
                if line.startswith('version'):
                    version = line.split('=')[1].strip().strip('"')
                    break
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ BUILD COMPLETE")
    print("=" * 50)
    print(f"\n📁 Output: {DIST_DIR}")
    print(f"📦 Package: {zip_path.name}")
    print(f"🏷️  Version: {version}")
    print(f"📊 Size: {zip_path.stat().st_size / 1024:.1f} KB")
    print("\n📋 This package is ready for:")
    print("   • extensions.blender.org submission")
    print("   • GitHub releases")
    print("   • Direct installation (Edit → Preferences → Get Extensions → Install from Disk)")
    print("=" * 50)


if __name__ == "__main__":
    main()
