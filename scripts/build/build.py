#!/usr/bin/env python3
"""Build script for creating executable files."""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
import tempfile


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def get_platform_info() -> tuple[str, str]:
    """Get platform information.
    
    Returns:
        Tuple of (platform_name, file_extension)
    """
    system = platform.system().lower()
    
    if system == "windows":
        return ("windows", ".exe")
    elif system == "darwin":
        return ("macos", ".app")
    else:
        return ("linux", "")


def create_spec_file(
    app_name: str,
    entry_point: str,
    output_name: str,
    icon_path: Path = None,
    is_gui: bool = False
) -> str:
    """Create PyInstaller spec file content.
    
    Args:
        app_name: Application name
        entry_point: Entry point module path
        output_name: Output executable name
        icon_path: Path to icon file
        is_gui: Whether this is a GUI application
        
    Returns:
        Spec file content as string
    """
    project_root = get_project_root()
    src_path = project_root / "src"
    
    # Build pathex list (normalize paths for cross-platform compatibility)
    pathex = [str(src_path).replace('\\', '/')]
    
    # Build hidden imports list (common problematic imports)
    hidden_imports = [
        'pygame',
        'websockets',
        'pydantic',
        'pynput',
        'click',
        'asyncio',
        'concurrent.futures',
        'multiprocessing',
        'queue',
        'PySide6',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
    ]
    
    # Add platform-specific hidden imports
    platform_name, _ = get_platform_info()
    if platform_name == "windows":
        hidden_imports.extend([
            'vgamepad',
            'win32api',
            'win32con',
            'win32gui',
            'winsound',
        ])
    
    # Build datas list (include any data files)
    datas = []
    
    # Icon path (fix Windows path escaping)
    if icon_path:
        icon_str = f"r'{icon_path}'"
    else:
        icon_str = "None"
    
    # Console setting
    console = "False" if is_gui else "True"
    
    # Normalize paths for cross-platform compatibility
    entry_point_norm = entry_point.replace('\\', '/')
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{entry_point_norm}'],
    pathex={pathex!r},
    binaries=[],
    datas={datas!r},
    hiddenimports={hidden_imports!r},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{output_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon_str},
)
"""
    
    # Add macOS app bundle creation
    if platform_name == "macos":
        spec_content += f"""
app = BUNDLE(
    exe,
    name='{output_name}.app',
    icon={icon_str},
    bundle_identifier='com.inputlink.{app_name.lower()}',
    info_plist={{
        'CFBundleDisplayName': '{app_name}',
        'CFBundleExecutableFile': '{output_name}',
        'CFBundleIdentifier': 'com.inputlink.{app_name.lower()}',
        'CFBundleName': '{app_name}',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    }},
)
"""
    
    return spec_content


def create_icons() -> tuple[Path, Path]:
    """Create application icons.
    
    Returns:
        Tuple of (sender_icon_path, receiver_icon_path)
    """
    build_dir = get_project_root() / "build"
    icons_dir = build_dir / "icons"
    icons_dir.mkdir(exist_ok=True)
    
    # Create simple icons using PIL
    try:
        from PIL import Image, ImageDraw
        
        def create_icon(text: str, color: str, filename: str) -> Path:
            # Create 256x256 icon
            size = 256
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw background circle
            padding = 20
            draw.ellipse(
                [padding, padding, size - padding, size - padding],
                fill=color
            )
            
            # Draw text
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (size - text_width) // 2
            y = (size - text_height) // 2
            draw.text((x, y), text, fill='white')
            
            # Save icon
            icon_path = icons_dir / filename
            image.save(icon_path)
            return icon_path
            
        sender_icon = create_icon("S", "#4A90E2", "sender.png")
        receiver_icon = create_icon("R", "#7ED321", "receiver.png")
        
        return sender_icon, receiver_icon
        
    except ImportError:
        print("PIL not available, skipping icon creation")
        return None, None


def build_application(
    app_name: str,
    entry_point: str,
    output_name: str,
    icon_path: Path = None,
    is_gui: bool = None
) -> bool:
    """Build application using PyInstaller.
    
    Args:
        app_name: Application name
        entry_point: Entry point module path
        output_name: Output executable name
        icon_path: Path to icon file
        
    Returns:
        True if build successful, False otherwise
    """
    project_root = get_project_root()
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    print(f"Building {app_name}...")
    
    try:
        # Auto-detect GUI application
        if is_gui is None:
            is_gui = "gui" in app_name.lower() or "gui" in entry_point.lower()
            
        # Create spec file
        spec_content = create_spec_file(
            app_name, entry_point, output_name, icon_path, is_gui
        )
        
        spec_file = build_dir / f"{output_name}.spec"
        spec_file.write_text(spec_content)
        
        # Run PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "--distpath", str(dist_dir),
            "--workpath", str(build_dir / "work"),
            str(spec_file)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=project_root, check=True)
        
        print(f"Successfully built {app_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to build {app_name}: {e}")
        return False
    except Exception as e:
        print(f"Build error for {app_name}: {e}")
        return False


def main():
    """Main build function."""
    project_root = get_project_root()
    platform_name, ext = get_platform_info()
    
    print(f"Building Input Link for {platform_name}...")
    
    # Ensure we're in a virtual environment or have required packages
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)
    
    # Create build directories
    (project_root / "build").mkdir(exist_ok=True)
    (project_root / "dist").mkdir(exist_ok=True)
    
    # Create icons
    sender_icon, receiver_icon = create_icons()
    
    # Create GUI icon
    gui_icon = None
    if sender_icon:
        try:
            from PIL import Image, ImageDraw
            
            # Create GUI icon (combined S+R)
            size = 256
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw background circle
            padding = 20
            draw.ellipse(
                [padding, padding, size - padding, size - padding],
                fill='#007AFF'
            )
            
            # Draw S+R text
            text = "SR"
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (size - text_width) // 2
            y = (size - text_height) // 2
            draw.text((x, y), text, fill='white')
            
            # Save GUI icon
            icons_dir = project_root / "build" / "icons"
            gui_icon = icons_dir / "gui.png"
            image.save(gui_icon)
        except Exception:
            pass
    
    # Build applications
    builds = [
        ("Input Link Sender", str(project_root / "src" / "input_link" / "apps" / "sender.py"), f"InputLink-Sender{ext}", sender_icon),
        ("Input Link Receiver", str(project_root / "src" / "input_link" / "apps" / "receiver.py"), f"InputLink-Receiver{ext}", receiver_icon),
        ("Input Link GUI", str(project_root / "src" / "input_link" / "apps" / "gui_main.py"), f"InputLink-GUI{ext}", gui_icon),
    ]
    
    success_count = 0
    for app_name, entry_point, output_name, icon_path in builds:
        if build_application(app_name, entry_point, output_name, icon_path):
            success_count += 1
    
    print(f"\nBuild Summary:")
    print(f"  Platform: {platform_name}")
    print(f"  Successful: {success_count}/{len(builds)}")
    print(f"  Output directory: {project_root / 'dist'}")
    
    if success_count == len(builds):
        print("All builds completed successfully!")
        
        # List built files
        dist_dir = project_root / "dist"
        if dist_dir.exists():
            print(f"\nBuilt files:")
            for item in sorted(dist_dir.iterdir()):
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    print(f"  {item.name} ({size_mb:.1f} MB)")
                elif item.is_dir():
                    print(f"  {item.name}/")
    else:
        print("Some builds failed")
        sys.exit(1)


if __name__ == "__main__":
    main()