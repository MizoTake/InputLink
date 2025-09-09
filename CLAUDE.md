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
- Controller identification uses stable identifiers
- Input polling at 60Hz with dead zone handling
- Multiple controllers supported (internal limit removed)

### Working with Virtual Controllers
- Windows: Uses ViGEm Bus Driver for Xbox 360 emulation
- macOS: Keyboard simulation (WASD + space) via pynput
- Auto-creation up to configured maximum
- 1:1 mapping from sender controller numbers to receiver virtual controllers

### Configuration Management
- Default location: `~/.input-link/config.json`
- Auto-generated with sensible defaults
- CLI parameters override config file
- Pydantic validation ensures correctness

### GUI Development
- Apple HIG-compliant design system
- PySide6 (Qt) with proper threading
- AsyncWorker pattern for backend integration
- Multi-window navigation with state management

## Testing Strategy

- **Unit Tests**: Fast component testing with mocks (`tests/unit/`)
- **Integration Tests**: Cross-component interaction (`tests/integration/`)
- **E2E Tests**: Full workflow testing (`tests/e2e/`)
- **Markers**: Use `pytest -m unit|integration|e2e|slow|asyncio`

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