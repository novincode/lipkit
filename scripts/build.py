#!/usr/bin/env python3
"""
Build script for LipKit
Creates: 
  1. lipkit_v1.1.0_[date].zip - The plugin itself
  2. LipKit_v1.1.0_[date].zip - Gumroad package (plugin + instructions + license)
"""
import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

# Paths
REPO_ROOT = Path(__file__).parent.parent
LIPKIT_SOURCE = REPO_ROOT / "lipkit"
BUILD_DIR = REPO_ROOT / "build"
DIST_DIR = BUILD_DIR / "dist"
STAGING_DIR = BUILD_DIR / "staging"

def create_plugin_zip():
    """Create lipkit_v1.1.0_[date].zip - the raw plugin"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"lipkit_v1.1.0_{timestamp}.zip"
    zip_path = DIST_DIR / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(LIPKIT_SOURCE):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.pyc'):
                    continue
                file_path = Path(root) / file
                arcname = Path("lipkit") / file_path.relative_to(LIPKIT_SOURCE)
                zipf.write(file_path, arcname)
    
    return zip_path

def create_install_txt():
    """Create simple text instructions"""
    return """LipKit - Installation Guide
============================

STEP 1: Extract Files
You've already extracted this! Inside you'll find:
  • lipkit_v0.1.0_[date].zip (the plugin)
  • INSTALL.txt (this file)
  • LICENSE.txt


STEP 2: Install Plugin in Blender
1. Open Blender 4.2 or newer
2. Go to: Edit → Preferences → Get Extensions
3. Click the button: "Install from Disk"
4. Select: lipkit_v0.1.0_[date].zip
5. Wait for installation to complete


STEP 3: Enable LipKit
1. Go to: Edit → Preferences → Add-ons
2. Search for "LipKit"
3. Click the checkbox next to LipKit to enable it


STEP 4: Open LipKit
1. Press N in the 3D viewport (right side panel opens)
2. Click the "LipKit" tab
3. You're ready to use it!


RHUBARB SETUP (One-time setup)
==============================
LipKit automatically downloads and sets up Rhubarb on first use.

If automatic download fails (you'll see an error):

1. Visit: https://github.com/DanielSWolf/rhubarb-lip-sync/releases
2. Download the latest version for your OS (macOS/Windows/Linux)
3. Extract the ZIP file
4. In Blender:
   - Open LipKit panel (Press N)
   - Look for "Rhubarb Lip Sync Tool" section at the top
   - Click "📁 Select Rhubarb" button
   - Navigate to the extracted folder
   - It will show ✅ Ready when done


NEED HELP?
==========
• Website: https://codeideal.com/contact
• Email: ideyenovin@gmail.com

Enjoy! 🎬
"""

def create_license_txt():
    """Create license as .txt"""
    return """LipKit License Agreement
========================

WHAT YOU GET:
• Professional lip sync plugin for Blender
• Works with 2D (Grease Pencil) and 3D (Shape Keys)
• Lifetime updates to v0.x series


WHAT YOU CAN DO:
✓ Use in personal projects
✓ Use in commercial projects
✓ Use for client/freelance work
✓ Sell animations created WITH LipKit
✓ Use on multiple personal computers


WHAT YOU CANNOT DO:
✗ Share or redistribute the plugin
✗ Resell LipKit as your own
✗ Modify and sell as a different product
✗ Share your license key
✗ Use on shared/team computers (1 license = 1 person)


SUPPORT:
Contact us at:
• Website: https://codeideal.com/contact
• Email: ideyenovin@gmail.com


---
Thank you for supporting independent software! 🎬
"""

def create_gumroad_package(plugin_zip_path):
    """Create the Gumroad download package"""
    
    # Clean staging
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(exist_ok=True)
    
    # Copy plugin zip to staging
    shutil.copy2(plugin_zip_path, STAGING_DIR / plugin_zip_path.name)
    
    # Create text files
    install_txt = STAGING_DIR / "INSTALL.txt"
    with open(install_txt, 'w') as f:
        f.write(create_install_txt())
    
    license_txt = STAGING_DIR / "LICENSE.txt"
    with open(license_txt, 'w') as f:
        f.write(create_license_txt())
    
    # Create the final Gumroad zip
    timestamp = datetime.now().strftime("%Y%m%d")
    gumroad_zip = DIST_DIR / f"LipKit_v0.1.0_{timestamp}.zip"
    
    with zipfile.ZipFile(gumroad_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in STAGING_DIR.iterdir():
            arcname = file_path.name
            zipf.write(file_path, arcname)
    
    return gumroad_zip

def main():
    # Create directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    
    # Step 1: Build plugin zip
    print("🔨 Building plugin zip...")
    plugin_zip = create_plugin_zip()
    print(f"✅ Plugin: {plugin_zip.name}")
    
    # Step 2: Create Gumroad package
    print("📦 Creating Gumroad package...")
    gumroad_zip = create_gumroad_package(plugin_zip)
    print(f"✅ Gumroad: {gumroad_zip.name}")
    
    # Summary
    print("\n" + "="*50)
    print("BUILD COMPLETE")
    print("="*50)
    print(f"\n📁 Location: {DIST_DIR}")
    print(f"\n📦 For Gumroad: {gumroad_zip.name}")
    print(f"   → Users download this one file")
    print(f"   → Extract to get plugin + instructions")
    print(f"\n🔧 For Testing: {plugin_zip.name}")
    print(f"   → Raw plugin (no instructions)")
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
