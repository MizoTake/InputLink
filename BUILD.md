# Building Input Link

This document describes how to build Input Link executable files for Windows and macOS.

## Prerequisites

- Python 3.8 or higher
- Git
- Platform-specific requirements (see below)

### Windows Requirements

- Visual Studio Build Tools or Visual Studio (for Python extensions)
- Windows SDK (usually installed with Visual Studio)

### macOS Requirements

- Xcode Command Line Tools: `xcode-select --install`
- For DMG creation: macOS 10.12+ recommended

## Quick Start

### Using Make (Recommended)

```bash
# Install dependencies and build
make install-dev
make build
```

### Manual Build

1. **Install dependencies:**
   ```bash
   pip install -e ".[build]"
   ```

2. **Build executables:**
   
   **Windows:**
   ```cmd
   build\build.bat
   ```
   
   **macOS/Linux:**
   ```bash
   ./build/build.sh
   ```

## Build Outputs

### Windows
- `dist/InputLink-Sender.exe` - Standalone sender executable
- `dist/InputLink-Receiver.exe` - Standalone receiver executable

### macOS
- `dist/InputLink-Sender.app` - Sender app bundle
- `dist/InputLink-Receiver.app` - Receiver app bundle

## Creating Installers

### Windows Installer (NSIS)

1. Install [NSIS](https://nsis.sourceforge.io/Download) (Nullsoft Scriptable Install System)

2. Build executables first:
   ```cmd
   make build
   ```

3. Create installer:
   ```cmd
   makensis build\installer\windows_installer.nsi
   ```

   This creates `InputLink-1.0.0-Windows-Installer.exe`

### macOS Installer (DMG)

1. Build app bundles first:
   ```bash
   make build
   ```

2. Create DMG:
   ```bash
   python build/installer/create_macos_dmg.py
   ```

   This creates `InputLink-1.0.0-macOS.dmg`

## Build Configuration

### PyInstaller Options

The build system uses PyInstaller with these key settings:

- **One-file mode**: All dependencies bundled into single executable
- **Console mode**: CLI applications show terminal output
- **Icon support**: Platform-appropriate icons included
- **Hidden imports**: Critical modules explicitly included
- **Exclusions**: Unnecessary packages excluded to reduce size

### Platform-Specific Settings

**Windows:**
- Uses `.exe` extension
- Includes Windows-specific dependencies (vgamepad, win32 modules)
- ViGEm driver integration supported

**macOS:**
- Creates `.app` bundles with proper Info.plist
- Includes macOS-specific dependencies
- Keyboard simulation fallback for virtual controllers

## Troubleshooting

### Common Build Issues

1. **Missing dependencies:**
   ```bash
   pip install -e ".[build]" --upgrade
   ```

2. **Import errors during build:**
   - Check `hidden_imports` list in `build/build.py`
   - Add missing modules to the list

3. **Large executable size:**
   - Review `excludes` list in build script
   - Consider excluding unused packages

4. **Runtime errors in built executable:**
   - Test with `--debug` PyInstaller flag
   - Check for missing data files or dynamic imports

### Platform-Specific Issues

**Windows:**
- Ensure Visual Studio Build Tools installed
- For ViGEm support, build on Windows with vgamepad available
- Windows Defender may flag executables (add exclusion)

**macOS:**
- Requires building on macOS for app bundles
- Code signing needed for distribution (not included in build)
- Gatekeeper may block unsigned apps

## Advanced Configuration

### Custom Build Script

Modify `build/build.py` for custom requirements:

```python
# Add custom hidden imports
hidden_imports.extend([
    'your_custom_module',
    'another_dependency'
])

# Add data files
datas = [
    ('path/to/data', 'data_folder'),
]

# Custom exclusions
excludes.extend([
    'unused_package',
])
```

### Cross-Platform Considerations

- Build Windows executables on Windows
- Build macOS apps on macOS
- Use GitHub Actions for automated cross-platform builds
- Consider using containers for Linux builds

## Distribution

### Windows
- Distribute `.exe` files directly or use NSIS installer
- Include ViGEm driver installation instructions
- Consider code signing for trust

### macOS
- Distribute `.app` bundles in DMG
- Consider PKG installer for system-wide installation
- Code signing and notarization recommended for distribution

### Security Notes

- Built executables may be flagged by antivirus software
- Code signing reduces false positives
- Document any network communication for security reviews
- Include privacy policy if collecting any user data

## Automated Builds

GitHub Actions workflow (`.github/workflows/build.yml`) provides:

- Cross-platform building
- Automated testing
- Release artifact creation
- Tagged release deployment

Trigger builds by pushing tags:
```bash
git tag v1.0.0
git push origin v1.0.0
```

## Performance Optimization

### Startup Time
- One-file executables are slower to start (extraction time)
- Consider one-directory mode for faster startup
- Profile startup to identify bottlenecks

### Size Optimization
- Use `--exclude-module` for large unused dependencies
- Consider UPX compression (enabled by default)
- Remove debug symbols in production builds

### Runtime Performance
- Built executables should perform similarly to Python scripts
- Profile any performance differences
- Consider platform-specific optimizations