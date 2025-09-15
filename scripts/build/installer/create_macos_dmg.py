#!/usr/bin/env python3
"""Create macOS DMG installer for Input Link."""

import os
import subprocess
import sys
from pathlib import Path
import tempfile
import json


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent.parent


def create_dmg_installer():
    """Create DMG installer for macOS."""
    project_root = get_project_root()
    dist_dir = project_root / "dist"
    
    # Check if apps exist
    sender_app = dist_dir / "InputLink-Sender.app"
    receiver_app = dist_dir / "InputLink-Receiver.app"
    
    if not sender_app.exists() or not receiver_app.exists():
        print("❌ App bundles not found. Run build first.")
        return False
    
    print("📦 Creating macOS DMG installer...")
    
    # Create temporary directory for DMG contents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dmg_contents = temp_path / "InputLink"
        dmg_contents.mkdir()
        
        # Copy app bundles
        print("  📱 Copying app bundles...")
        subprocess.run([
            "cp", "-R", str(sender_app), str(dmg_contents)
        ], check=True)
        
        subprocess.run([
            "cp", "-R", str(receiver_app), str(dmg_contents)
        ], check=True)
        
        # Copy documentation
        readme_src = project_root / "README.md"
        license_src = project_root / "LICENSE"
        
        if readme_src.exists():
            subprocess.run([
                "cp", str(readme_src), str(dmg_contents)
            ], check=True)
        
        if license_src.exists():
            subprocess.run([
                "cp", str(license_src), str(dmg_contents)
            ], check=True)
        
        # Create Applications symlink
        applications_link = dmg_contents / "Applications"
        applications_link.symlink_to("/Applications")
        
        # Create DS_Store file for nice layout (optional)
        create_ds_store(dmg_contents)
        
        # Create DMG
        dmg_name = "InputLink-1.0.0-macOS.dmg"
        dmg_path = project_root / dmg_name
        
        print(f"  💾 Creating DMG: {dmg_name}")
        
        try:
            # Remove existing DMG
            if dmg_path.exists():
                dmg_path.unlink()
            
            # Create DMG using hdiutil
            subprocess.run([
                "hdiutil", "create",
                "-srcfolder", str(dmg_contents),
                "-volname", "Input Link",
                "-format", "UDZO",
                "-imagekey", "zlib-level=9",
                str(dmg_path)
            ], check=True)
            
            print(f"✅ DMG created successfully: {dmg_path}")
            print(f"   Size: {dmg_path.stat().st_size / (1024*1024):.1f} MB")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create DMG: {e}")
            return False


def create_ds_store(dmg_contents: Path):
    """Create .DS_Store file for DMG layout."""
    try:
        # Create a simple AppleScript to set up the DMG layout
        applescript = f'''
tell application "Finder"
    tell disk "Input Link"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {{100, 100, 800, 500}}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 128
        set position of item "InputLink-Sender.app" of container window to {{200, 200}}
        set position of item "InputLink-Receiver.app" of container window to {{400, 200}}
        set position of item "Applications" of container window to {{600, 200}}
        close
    end tell
end tell
'''
        # Note: This would need to be run after mounting the DMG
        # For now, we'll skip the DS_Store creation
        pass
        
    except Exception as e:
        print(f"Warning: Could not create .DS_Store: {e}")


def create_pkg_installer():
    """Create macOS PKG installer as alternative."""
    project_root = get_project_root()
    dist_dir = project_root / "dist"
    
    # Check if apps exist
    sender_app = dist_dir / "InputLink-Sender.app"
    receiver_app = dist_dir / "InputLink-Receiver.app"
    
    if not sender_app.exists() or not receiver_app.exists():
        print("❌ App bundles not found. Run build first.")
        return False
    
    print("📦 Creating macOS PKG installer...")
    
    try:
        # Create package structure
        pkg_root = dist_dir / "pkg_root" / "Applications"
        pkg_root.mkdir(parents=True, exist_ok=True)
        
        # Copy apps to package root
        subprocess.run([
            "cp", "-R", str(sender_app), str(pkg_root)
        ], check=True)
        
        subprocess.run([
            "cp", "-R", str(receiver_app), str(pkg_root)
        ], check=True)
        
        # Create package info
        pkg_info = {
            "identifier": "com.inputlink.inputlink",
            "version": "1.0.0",
            "title": "Input Link",
            "description": "Network Controller Forwarding System"
        }
        
        # Build package
        pkg_name = "InputLink-1.0.0-macOS.pkg"
        pkg_path = project_root / pkg_name
        
        subprocess.run([
            "pkgbuild",
            "--root", str(dist_dir / "pkg_root"),
            "--identifier", pkg_info["identifier"],
            "--version", pkg_info["version"],
            str(pkg_path)
        ], check=True)
        
        print(f"✅ PKG created successfully: {pkg_path}")
        
        # Cleanup
        subprocess.run([
            "rm", "-rf", str(dist_dir / "pkg_root")
        ], check=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create PKG: {e}")
        return False


def main():
    """Main function."""
    if sys.platform != "darwin":
        print("❌ This script must be run on macOS")
        sys.exit(1)
    
    success = False
    
    # Try to create DMG first
    try:
        success = create_dmg_installer()
    except Exception as e:
        print(f"❌ DMG creation failed: {e}")
    
    # Fallback to PKG if DMG fails
    if not success:
        print("🔄 Falling back to PKG installer...")
        success = create_pkg_installer()
    
    if success:
        print("🎉 macOS installer created successfully!")
    else:
        print("❌ Failed to create macOS installer")
        sys.exit(1)


if __name__ == "__main__":
    main()