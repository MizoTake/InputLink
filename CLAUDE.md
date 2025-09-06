# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Building and Running
```bash
# Build executables for current platform
make build

# Run applications
make run-sender
make run-receiver

# Clean build artifacts
make clean
```

### Testing
```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test categories
pytest -m unit
pytest -m integration
```

### Development Tools
```bash
# Install development dependencies
make install-dev

# Format and lint code
make format lint

# Type checking
mypy src
```

## Project Structure

```
src/input_link/              # Main package
├── __init__.py              # Package version and metadata
├── models/                  # Pydantic data models
│   ├── __init__.py         # Model exports  
│   ├── controller.py       # ControllerInputData, ButtonState, ControllerState
│   └── config.py           # ConfigModel, SenderConfig, ReceiverConfig
├── core/                   # Controller detection and input capture
│   ├── __init__.py         # Core exports
│   ├── controller_manager.py  # ControllerManager, DetectedController
│   └── input_capture.py    # InputCaptureEngine
├── network/                # WebSocket communication
│   ├── __init__.py         # Network exports
│   ├── message_protocol.py # NetworkMessage, MessageType
│   ├── websocket_client.py # WebSocketClient
│   └── websocket_server.py # WebSocketServer
├── virtual/                # Virtual controller management
│   ├── __init__.py         # Virtual controller exports
│   ├── base.py             # VirtualController, VirtualControllerFactory
│   ├── windows.py          # WindowsVirtualController (vgamepad)
│   ├── macos.py            # MacOSVirtualController (keyboard simulation)
│   └── controller_manager.py # VirtualControllerManager
└── apps/                   # CLI applications
    ├── __init__.py         # App exports
    ├── sender.py           # SenderApp CLI
    └── receiver.py         # ReceiverApp CLI

build/                      # Build system
├── build.py                # Python build script
├── build.bat              # Windows build script
├── build.sh               # macOS/Linux build script
└── installer/             # Installer creation
    ├── windows_installer.nsi    # NSIS installer script
    └── create_macos_dmg.py     # DMG creation script

tests/                      # Test suite
├── unit/                   # Unit tests
│   ├── test_models.py      # Data model tests
│   ├── test_controller_manager.py # Controller system tests
│   ├── test_input_capture.py # Input capture tests
│   ├── test_network.py     # Network communication tests
│   └── test_virtual.py     # Virtual controller tests
├── integration/            # Integration tests
└── e2e/                   # End-to-end tests

.kiro/specs/               # Original specifications
├── design.md              # Architecture design document
├── requirements.md        # User stories and requirements
└── tasks.md              # Implementation task breakdown
```

## Architecture Overview

**Input Link** is a Network Controller Forwarding System that captures controller inputs on a sender PC and transmits them over WebSocket to a receiver PC for virtual controller simulation.

### Key Components

1. **Data Models** (`models/`):
   - `ControllerInputData`: Validated controller input with Pydantic v2
   - `ConfigModel`: JSON configuration with cross-platform settings
   - Strict validation ensures data integrity

2. **Controller System** (`core/`):
   - `ControllerManager`: Cross-platform controller detection via pygame
   - `InputCaptureEngine`: Real-time input polling (60Hz) with dead zone handling
   - Xbox/PlayStation controller auto-detection

3. **Network Layer** (`network/`):
   - `WebSocketClient`: Async client with automatic reconnection
   - `WebSocketServer`: Multi-client async server
   - `NetworkMessage`: Typed message protocol with JSON serialization

4. **Virtual Controllers** (`virtual/`):
   - `VirtualControllerFactory`: Platform-specific controller creation
   - `WindowsVirtualController`: ViGEm/vgamepad integration
   - `MacOSVirtualController`: Keyboard simulation fallback
   - `VirtualControllerManager`: Multi-controller lifecycle management

5. **CLI Applications** (`apps/`):
   - `SenderApp`: Controller capture and WebSocket transmission
   - `ReceiverApp`: Input reception and virtual controller simulation
   - Click-based CLI with configuration overrides

### Data Flow

1. **Sender**: Pygame captures controller inputs → InputCaptureEngine processes → WebSocketClient transmits
2. **Network**: JSON messages over WebSocket with automatic reconnection
3. **Receiver**: WebSocketServer receives → VirtualControllerManager creates virtual controllers → Platform-specific simulation

### Technology Stack

- **Python 3.8+**: Cross-platform compatibility
- **pygame**: Controller input capture
- **websockets**: Async WebSocket communication  
- **pydantic v2**: Data validation and serialization
- **vgamepad** (Windows): ViGEm virtual controller integration
- **pynput**: macOS keyboard simulation
- **click**: CLI interface
- **pytest**: Test framework with async support
- **PyInstaller**: Executable creation

### Platform Support

**Windows**:
- Virtual controllers via ViGEm Bus Driver (Xbox 360 emulation)
- DirectInput and XInput support
- Executable builds with NSIS installer

**macOS**:  
- Keyboard simulation for virtual input
- App bundle creation with DMG installer
- Accessibility permissions required

## Build System

### PyInstaller Configuration
- One-file executables with embedded dependencies
- Hidden imports for dynamic modules (pygame, websockets, vgamepad)
- Platform-specific exclusions to reduce size
- Icon support and console/GUI mode selection

### Cross-Platform Building
- GitHub Actions for automated builds
- Platform-specific scripts (build.bat, build.sh)
- Make targets for development workflow
- Installer creation (NSIS for Windows, DMG for macOS)

### Distribution
- Standalone executables with no Python dependency
- Installers include driver setup (ViGEm on Windows)
- Code signing preparation (certificates not included)

## Testing Strategy

### Test Categories
- **Unit tests**: Individual component testing with mocks
- **Integration tests**: Cross-component interaction testing
- **E2E tests**: Full system workflow testing

### Test Tools
- pytest with asyncio support
- Mock/patch for external dependencies  
- Temporary file fixtures for configuration testing
- Coverage reporting with pytest-cov

### CI/CD
- GitHub Actions for cross-platform testing
- Automated releases on git tags
- Artifact upload for Windows/macOS builds

## Development Notes

- **Testable Design**: All components support dependency injection and mocking
- **Type Safety**: Complete type hints with mypy validation
- **Error Handling**: Comprehensive logging and graceful degradation
- **Performance**: Async I/O throughout, efficient input polling
- **Security**: No hardcoded credentials, configurable network settings

### Code Quality Tools
- **black**: Code formatting
- **isort**: Import organization  
- **ruff**: Fast linting and static analysis
- **mypy**: Static type checking

### Configuration Management
- JSON files in ~/.input-link/ directory
- CLI parameter overrides
- Platform-specific settings with validation
- Automatic config creation with sensible defaults