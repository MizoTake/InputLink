# Input Link

Network Controller Forwarding System that enables forwarding controller inputs from a sender PC to a receiver PC over a local network via WebSocket.

## Features

- **Cross-platform support**: Windows, macOS
- **Real-time input forwarding**: Low-latency controller input transmission
- **Universal controller support**: DInput and XInput controllers
- **Virtual controller simulation**: Driver-level input simulation on receiver
- **Automatic reconnection**: Robust WebSocket communication
- **Multiple controllers**: Support for up to 8 controllers simultaneously
- **Easy configuration**: JSON-based configuration with CLI overrides

## Quick Start

### Download Prebuilt Executables

**Windows:**
1. Download `InputLink-Windows-Installer.exe` from [Releases](../../releases)
2. Run installer (includes ViGEm driver setup)
3. Launch "Input Link Sender" and "Input Link Receiver" from Start Menu

**macOS:**
1. Download `InputLink-macOS.dmg` from [Releases](../../releases)
2. Mount DMG and drag apps to Applications folder
3. Launch from Applications or Launchpad

### Command Line Usage

**Sender (captures controller inputs):**
```bash
# Connect to receiver at default address
input-link-sender

# Connect to specific receiver
input-link-sender --host 192.168.1.100 --port 8765

# Enable verbose logging
input-link-sender --verbose
```

**Receiver (simulates controller inputs):**
```bash
# Start receiver on default port
input-link-receiver

# Start on specific port with more controllers
input-link-receiver --port 9000 --max-controllers 8

# Enable verbose logging  
input-link-receiver --verbose
```

## Building from Source

### Prerequisites

- Python 3.8+
- Git

### Development Setup

```bash
# Clone repository
git clone https://github.com/inputlink/inputlink.git
cd inputlink

# Install with development dependencies
make install-dev

# Run tests
make test

# Format and lint code
make format lint
```

### Building Executables

```bash
# Build for current platform
make build

# Clean build artifacts
make clean
```

**Platform-specific builds:**
- Windows: `build\build.bat` or `make build-windows`
- macOS: `./build/build.sh` or `make build-macos`

See [BUILD.md](BUILD.md) for detailed build instructions.

## Architecture

```
┌─────────────────┐    WebSocket     ┌─────────────────┐
│   Sender PC     │ ◄──────────────► │   Receiver PC   │
│                 │                  │                 │
│ ┌─────────────┐ │                  │ ┌─────────────┐ │
│ │ Controller  │ │                  │ │ Virtual     │ │
│ │ Manager     │ │                  │ │ Controller  │ │
│ └─────────────┘ │                  │ │ Manager     │ │
│ ┌─────────────┐ │                  │ └─────────────┘ │
│ │ Input       │ │                  │ ┌─────────────┐ │
│ │ Capture     │ │                  │ │ Input       │ │
│ └─────────────┘ │                  │ │ Simulation  │ │
│ ┌─────────────┐ │                  │ └─────────────┘ │
│ │ WebSocket   │ │                  │ ┌─────────────┐ │
│ │ Client      │ │                  │ │ WebSocket   │ │
│ └─────────────┘ │                  │ │ Server      │ │
└─────────────────┘                  │ └─────────────┘ │
                                     └─────────────────┘
```

**Key Components:**
- **Sender**: Captures controller inputs using pygame and transmits via WebSocket
- **Receiver**: Receives input data and simulates virtual controllers
- **Models**: Pydantic-validated data structures for robust input transmission
- **Network**: Async WebSocket communication with error handling and reconnection

## Platform Support

### Windows
- **Virtual Controllers**: ViGEm Bus Driver (Xbox 360 controller emulation)
- **Input Methods**: DirectInput and XInput
- **Requirements**: Windows 10/11, ViGEm driver (auto-installed)

### macOS
- **Virtual Controllers**: Keyboard simulation (WASD + other keys)
- **Input Methods**: Generic HID via pygame
- **Requirements**: macOS 10.12+, Accessibility permissions for input simulation

## Configuration

Configuration files stored in `~/.input-link/config.json`:

```json
{
  "sender_config": {
    "receiver_host": "127.0.0.1",
    "receiver_port": 8765,
    "polling_rate": 60,
    "retry_interval": 1.0,
    "max_retry_attempts": 10
  },
  "receiver_config": {
    "listen_port": 8765,
    "max_controllers": 4,
    "auto_create_virtual": true,
    "connection_timeout": 30.0
  }
}
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test types
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m e2e         # End-to-end tests only
```

## Contributing

1. **Code Style**: Use `black`, `isort`, `ruff` for formatting and linting
2. **Testing**: Write tests for new features (pytest)
3. **Type Hints**: Include complete type annotations
4. **Documentation**: Update relevant documentation
5. **Commits**: Use conventional commit format

### Development Commands

```bash
make help              # Show available commands
make install-dev       # Install development dependencies
make test              # Run tests
make lint              # Run linting
make format            # Format code
make build             # Build executables
make clean             # Clean build artifacts
```

## License

[Insert License Here]

## Support

- **Issues**: [GitHub Issues](../../issues)
- **Documentation**: See [BUILD.md](BUILD.md) for build instructions
- **Releases**: [GitHub Releases](../../releases) for prebuilt executables