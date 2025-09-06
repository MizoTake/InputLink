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
make run-gui         # Run GUI application

# Clean build artifacts
make clean

# Alternative entry points
python main.py gui     # Unified entry point for GUI
python main.py sender  # CLI sender
python main.py receiver # CLI receiver
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
├── gui/                    # GUI applications (Apple HIG compliant)
│   ├── __init__.py         # GUI component exports
│   ├── application.py      # InputLinkApplication, AsyncWorker
│   ├── main_window.py      # MainWindow, ModernButton, StatusCard
│   ├── sender_window.py    # SenderWindow, ControllerCard
│   └── receiver_window.py  # ReceiverWindow, VirtualControllerCard
└── apps/                   # Application entry points
    ├── __init__.py         # App exports
    ├── sender.py           # SenderApp CLI with callback support
    ├── receiver.py         # ReceiverApp CLI with callback support
    ├── gui_main.py         # Unified GUI entry point
    ├── gui_sender.py       # GUI-specific sender entry
    └── gui_receiver.py     # GUI-specific receiver entry

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

5. **Applications** (`apps/` & `gui/`):
   - **CLI Applications**: `SenderApp` and `ReceiverApp` with async architecture
   - **GUI Applications**: Apple HIG-compliant PySide6 interface
   - **Unified Entry Point**: `main.py` with subcommands for CLI/GUI modes
   - **Callback Architecture**: CLI apps support log/status callbacks for GUI integration

### Data Flow

1. **Sender**: Pygame captures controller inputs → InputCaptureEngine processes → WebSocketClient transmits
2. **Network**: JSON messages over WebSocket with automatic reconnection
3. **Receiver**: WebSocketServer receives → VirtualControllerManager creates virtual controllers → Platform-specific simulation

### Technology Stack

**Core Framework**:
- **Python 3.8+**: Cross-platform compatibility
- **pygame**: Controller input capture
- **websockets**: Async WebSocket communication  
- **pydantic v2**: Data validation and serialization
- **asyncio**: Async architecture throughout

**Platform Integration**:
- **vgamepad** (Windows): ViGEm virtual controller integration
- **pynput**: macOS keyboard simulation
- **PySide6**: Cross-platform GUI framework (Qt-based)

**Development Tools**:
- **click**: CLI interface framework
- **pytest**: Test framework with async support
- **PyInstaller**: Executable creation
- **black/isort/ruff**: Code formatting and linting
- **mypy**: Static type checking

### Platform Support

**Windows**:
- Virtual controllers via ViGEm Bus Driver (Xbox 360 emulation)
- DirectInput and XInput support
- Executable builds: `InputLink-Sender.exe`, `InputLink-Receiver.exe`, `InputLink-GUI.exe`
- NSIS installer available

**macOS**:  
- Keyboard simulation for virtual input (no driver required)
- App bundle creation (.app files) with DMG installer
- Accessibility permissions required for input simulation

## GUI Architecture

### Apple HIG Compliance
- **Design System**: Follows Apple Human Interface Guidelines for consistency
- **Color Palette**: Apple system colors (#007AFF, #34C759, #FF3B30, etc.)
- **Typography**: San Francisco font system (-apple-system stack)
- **Layout**: Proper spacing (16-24px), rounded corners (8-12px), visual hierarchy

### GUI Components
- **MainWindow**: Application overview with status cards and navigation
- **SenderWindow**: Controller detection, configuration, and capture controls
- **ReceiverWindow**: Virtual controller management and server status
- **ModernButton**: Apple HIG-compliant button styles (primary, secondary, destructive)
- **StatusCard**: Real-time status display with color-coded states
- **ControllerCard**: Individual controller management with enable/disable toggles

### Threading Architecture
- **Main Thread**: Qt GUI event loop
- **AsyncWorker Thread**: Separate thread with asyncio event loop for backend operations
- **Signal/Slot Communication**: Qt signals for thread-safe GUI updates
- **Graceful Shutdown**: Proper cleanup of async tasks and resources

### Integration Patterns
- **Callback Architecture**: CLI apps (`SenderApp`, `ReceiverApp`) support callback functions
- **Status Updates**: Real-time status propagation from backend to GUI
- **Log Integration**: Centralized logging with GUI display
- **Window Management**: Multi-window navigation with proper state management

## Build System

### PyInstaller Configuration
- One-file executables with embedded dependencies
- Hidden imports for dynamic modules (pygame, websockets, vgamepad, PySide6)
- Platform-specific exclusions to reduce size (PyQt5/6, tkinter, matplotlib)
- Icon support and console/GUI mode selection (automatic GUI detection)
- Three executables generated: Sender, Receiver, and unified GUI application

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

## Application Entry Points

### Unified Entry Point
```bash
python main.py                    # Show usage information
python main.py --version          # Show version
python main.py gui                # Launch GUI application
python main.py sender [OPTIONS]   # CLI sender with options
python main.py receiver [OPTIONS] # CLI receiver with options
```

### Direct Module Execution
```bash
# CLI applications (for development)
python -m input_link.apps.sender
python -m input_link.apps.receiver

# GUI applications (for development/testing)
python -m input_link.apps.gui_main
python -m input_link.gui.application
```

### Built Executables
```bash
# Windows
.\dist\InputLink-GUI.exe        # Unified GUI application
.\dist\InputLink-Sender.exe     # CLI sender
.\dist\InputLink-Receiver.exe   # CLI receiver

# macOS
./dist/InputLink-GUI.app        # GUI application bundle
./dist/InputLink-Sender.app     # Sender app bundle  
./dist/InputLink-Receiver.app   # Receiver app bundle
```

### Configuration Files
- Default location: `~/.input-link/config.json`
- Auto-generated on first run with sensible defaults
- CLI parameters override config file settings
- JSON schema validation via Pydantic models

## Development Notes

### Architecture Patterns
- **Async/Await**: All I/O operations use asyncio for non-blocking execution
- **Dependency Injection**: Components accept callbacks/dependencies for testability
- **Factory Pattern**: Platform-specific virtual controller creation
- **Observer Pattern**: Status updates via callbacks and Qt signals
- **Model-View Separation**: Core logic separate from GUI presentation

### Key Implementation Details
- **Thread Safety**: Qt signals/slots ensure thread-safe GUI updates
- **Error Handling**: Comprehensive try/catch with graceful degradation
- **Resource Management**: Proper cleanup of async tasks, threads, and hardware
- **Input Polling**: 60Hz polling rate with dead zone handling for controllers
- **Network Resilience**: Automatic WebSocket reconnection with exponential backoff

### Common Development Patterns
```python
# Adding new callback support to CLI apps
class MyApp:
    def __init__(self, log_callback=None, status_callback=None):
        self._log_callback = log_callback
        self._status_callback = status_callback

# GUI-backend integration via AsyncWorker
@Slot()
def my_gui_action(self):
    self.async_worker.do_something()

# Pydantic v2 model definition
class MyModel(BaseModel):
    field: str = Field(..., min_length=1)
    model_config = ConfigDict(validate_assignment=True)
```

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