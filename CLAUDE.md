# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Setup and Installation
```bash
# Install development dependencies
make install-dev

# Install package in development mode
make install
```

### Testing
```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test categories
pytest -m unit        # Unit tests
pytest -m integration # Integration tests
pytest -m e2e         # End-to-end tests

# Run single test file
pytest tests/unit/test_controller_manager.py -v

# Run with asyncio debugging
pytest tests/ -v --log-level=DEBUG
```

### Code Quality
```bash
# Lint code
make lint           # Run ruff check and mypy

# Format code
make format         # Run black and isort

# Combined check
make check          # Run lint and test
```

### Running Applications
```bash
# CLI applications (development)
make run-sender
make run-receiver
make run-gui

# Unified entry point
python main.py gui                 # GUI application
python main.py sender [OPTIONS]    # CLI sender
python main.py receiver [OPTIONS]  # CLI receiver

# Module execution
python -m input_link.apps.sender
python -m input_link.apps.receiver
python -m input_link.apps.gui_main

# Test controller detection
python main.py sender --list-controllers
```

### Building
```bash
# Build executables for current platform
make build

# Platform-specific builds
make build-windows  # Windows only
make build-macos    # macOS only

# Clean build artifacts
make clean
```

## Project Architecture

**Input Link** is a Network Controller Forwarding System that captures gamepad inputs on a sender PC and forwards them via WebSocket to a receiver PC for virtual controller simulation.

### Core Components

1. **Data Models** (`src/input_link/models/`):
   - `ControllerInputData`: Pydantic v2 validated controller input
   - `ConfigModel`: JSON configuration with CLI parameter override support

2. **Controller System** (`src/input_link/core/`):
   - `ControllerManager`: Cross-platform controller detection via pygame
   - `InputCaptureEngine`: Real-time 60Hz input polling with dead zone handling

3. **Network Layer** (`src/input_link/network/`):
   - `WebSocketClient`: Async client with automatic reconnection
   - `WebSocketServer`: Multi-client async server
   - `NetworkMessage`: Typed message protocol with JSON serialization

4. **Virtual Controllers** (`src/input_link/virtual/`):
   - `VirtualControllerFactory`: Platform-specific controller creation
   - `WindowsVirtualController`: ViGEm/vgamepad integration (Xbox 360 emulation)
   - `MacOSVirtualController`: Keyboard simulation fallback
   - `VirtualControllerManager`: Multi-controller lifecycle management

5. **Applications** (`src/input_link/apps/` & `src/input_link/gui/`):
   - CLI Applications: `SenderApp` and `ReceiverApp` with callback support
   - GUI Applications: Apple HIG-compliant PySide6 interface
   - Unified entry point via `main.py` with subcommands

### Key Architecture Patterns

- **Async/Await**: All I/O operations use asyncio
- **Factory Pattern**: Platform-specific virtual controller creation
- **Observer Pattern**: Status updates via callbacks and Qt signals
- **Dependency Injection**: Components accept callbacks for testability

### Technology Stack

**Core**:
- Python 3.8+ with asyncio
- pygame (controller input)
- websockets (async WebSocket)
- pydantic v2 (data validation)

**Platform Integration**:
- vgamepad (Windows virtual controllers via ViGEm)
- pynput (macOS keyboard simulation)
- PySide6 (cross-platform Qt GUI)

**Development**:
- pytest with asyncio support
- black/isort/ruff (code quality)
- mypy (static type checking)
- PyInstaller (executable creation)

## Development Workflows

### Adding New Features
1. Create feature branch from `master`
2. Implement with proper type hints and async patterns
3. Add unit tests in `tests/unit/`
4. Update integration tests if needed
5. Run `make check` to validate
6. Submit PR to `master`

### Working with Controllers
- Physical controllers detected via pygame
- Controller identification uses stable identifiers (GUID + device_id format)
- Input polling at 60Hz with dead zone handling in `InputCaptureEngine`
- Multiple controllers supported (no internal limit, OS-dependent)
- Auto-assignment of controller numbers with `_get_next_available_number()`
- Controller state tracking through `ControllerConnectionState` enum

### Working with Virtual Controllers
- Windows: Uses ViGEm Bus Driver for Xbox 360 emulation via `vgamepad`
- macOS: Keyboard simulation (WASD + space) via `pynput`
- Auto-creation up to configured maximum in `VirtualControllerManager`
- 1:1 mapping from sender controller numbers to receiver virtual controllers
- Factory pattern implementation in `VirtualControllerFactory.create_controller()`

### Configuration Management
- Default location: `~/.input-link/config.json`
- Auto-generated with sensible defaults
- CLI parameters override config file
- Pydantic v2 validation with `ConfigModel`, `SenderConfig`, `ReceiverConfig`
- Runtime config injection into CLI apps via `config` attribute

### GUI Development
- Apple HIG-compliant design system with specific color palette
- PySide6 (Qt) with proper threading via `AsyncWorker` on separate thread
- Signal/slot communication for thread-safe GUI updates
- Multi-window navigation with `QStackedWidget`
- Real-time status updates via callback architecture

## Testing Strategy

- **Unit Tests**: Fast component testing with mocks (`tests/unit/`)
  - Mock pygame joystick objects for controller manager tests
  - Mock websocket connections for network layer tests
  - Pydantic model validation testing
- **Integration Tests**: Cross-component interaction (`tests/integration/`)
  - WebSocket client/server communication
  - Controller manager + input capture integration
- **E2E Tests**: Full workflow testing (`tests/e2e/`)
  - Complete sender -> receiver workflow
- **Test Markers**: Use `pytest -m unit|integration|e2e|slow|asyncio`
- **Async Testing**: Tests use `pytest-asyncio` for async/await patterns

## Important Notes

### Platform Considerations
- Windows requires ViGEm Bus Driver for virtual controllers
- macOS requires accessibility permissions for input simulation
- Cross-platform pygame controller support

### Network Protocol
- JSON messages over WebSocket
- Automatic reconnection with exponential backoff
- Multi-client server support

### Build System
- PyInstaller creates standalone executables
- Three builds: Sender, Receiver, unified GUI
- Platform-specific installers (NSIS/DMG)
- GitHub Actions for automated releases

## Key Implementation Patterns

### Async Architecture
- All I/O operations use `asyncio` for non-blocking execution
- WebSocket client has automatic reconnection with exponential backoff
- Message queuing with bounded `_LenQueue` wrapper around `asyncio.Queue`
- Proper async context managers (`__aenter__`/`__aexit__`)

### Error Handling & Logging
- Centralized logging via `setup_application_logging()`
- Callback-based logging integration for GUI apps
- Graceful error handling with try/catch blocks
- Connection state tracking with status callbacks

### Data Validation
- Pydantic v2 models with strict validation (`validate_assignment=True`)
- Field validators for clamping controller input values (triggers, sticks)
- JSON serialization/deserialization built into models
- Configuration validation with CLI parameter override support

### Threading & GUI Integration
- `AsyncWorker` thread runs separate asyncio event loop
- Qt signals/slots for thread-safe communication
- `_schedule()` method for running coroutines on worker thread
- Proper cleanup in `_on_about_to_quit()` handler

### Controller Management
- Stable controller identification via `f"{guid}_{device_id}"`
- Auto-assignment with `_get_next_available_number()` (no fixed upper bound)
- Controller type detection (`is_xbox_controller()`, `is_playstation_controller()`)
- Dynamic controller mapping with live updates during runtime

### Network Protocol
- Typed message protocol via `NetworkMessage` class
- JSON-based serialization with message type identification
- Client connection state tracking and auto-reconnection
- Server supports multiple concurrent clients

### Virtual Controller Patterns
- Platform-specific factory pattern for controller creation
- Lifecycle management with creation/destruction callbacks
- Auto-creation of virtual controllers on-demand
- State synchronization with input data validation

## Coding Rules

### Error Handling
- **Do NOT use try-catch blocks** - This is a strict coding rule for this project
- Use alternative error handling patterns such as:
  - Return value checking
  - Status codes or result objects
  - Early returns with validation
  - Optional/Result type patterns where applicable