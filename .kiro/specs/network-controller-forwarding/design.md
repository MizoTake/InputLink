# Design Document

## Overview

The Network Controller Forwarding system consists of two main applications: a Sender application that captures controller inputs and a Receiver application that simulates those inputs. The system uses Python as the primary language due to its excellent cross-platform support and rich ecosystem for both controller input handling and WebSocket communication.

**Technology Stack:**
- **Language:** Python 3.8+ (cross-platform compatibility)
- **Controller Input:** `pygame` for cross-platform controller detection and input capture
- **WebSocket:** `websockets` library for real-time communication
- **Windows Input Simulation:** `ViGEmBus` via `pyvigem` Python wrapper
- **macOS Input Simulation:** `pygame` with virtual controller creation or `pynput` for system-level input
- **Configuration:** JSON files for persistent settings
- **GUI Framework:** `tkinter` (built-in) or `PyQt5/6` for cross-platform interface

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

## Components and Interfaces

### Sender Application Components

#### 1. Controller Manager
- **Purpose:** Detect, enumerate, and manage physical controllers
- **Key Methods:**
  - `detect_controllers()` - Scan for connected controllers
  - `assign_controller_number(controller_id, number)` - Assign logical numbers
  - `get_controller_info(controller_id)` - Get controller capabilities
  - `set_input_method(controller_id, method)` - Choose DInput/XInput preference

#### 2. Input Capture Engine
- **Purpose:** Continuously poll controller inputs and format data
- **Key Methods:**
  - `start_polling()` - Begin input capture loop
  - `stop_polling()` - Stop input capture
  - `get_controller_state(controller_id)` - Get current input state
  - `format_input_data(controller_id, state)` - Format for transmission

#### 3. WebSocket Client
- **Purpose:** Establish connection and transmit input data
- **Key Methods:**
  - `connect(host, port)` - Connect to receiver
  - `send_input_data(data)` - Transmit controller input
  - `handle_connection_loss()` - Reconnection logic
  - `queue_data(data)` - Queue data during disconnection

### Receiver Application Components

#### 1. WebSocket Server
- **Purpose:** Listen for connections and receive input data
- **Key Methods:**
  - `start_server(port)` - Start listening for connections
  - `handle_client_connection(websocket)` - Manage client connections
  - `receive_input_data()` - Parse incoming controller data
  - `broadcast_status()` - Send status updates to clients

#### 2. Virtual Controller Manager
- **Purpose:** Create and manage virtual controller instances
- **Key Methods:**
  - `create_virtual_controller(controller_number)` - Create virtual device
  - `destroy_virtual_controller(controller_number)` - Remove virtual device
  - `get_virtual_controller(controller_number)` - Get controller instance
  - `list_active_controllers()` - List all virtual controllers

#### 3. Input Simulation Engine
- **Purpose:** Convert received data to system-level input events
- **Key Methods:**
  - `simulate_button_press(controller_id, button, state)` - Simulate button
  - `simulate_analog_input(controller_id, axis, value)` - Simulate analog input
  - `update_controller_state(controller_id, full_state)` - Update complete state
  - `validate_input_data(data)` - Validate received input data

## Data Models

### Controller Input Data Format (JSON)
```json
{
  "timestamp": 1640995200.123,
  "controller_number": 1,
  "controller_id": "xbox_controller_0",
  "input_method": "xinput",
  "buttons": {
    "a": true,
    "b": false,
    "x": false,
    "y": false,
    "lb": false,
    "rb": false,
    "back": false,
    "start": false,
    "ls": false,
    "rs": false,
    "dpad_up": false,
    "dpad_down": false,
    "dpad_left": false,
    "dpad_right": false
  },
  "axes": {
    "left_stick_x": 0.0,
    "left_stick_y": 0.0,
    "right_stick_x": 0.0,
    "right_stick_y": 0.0,
    "left_trigger": 0.0,
    "right_trigger": 0.0
  }
}
```

### Configuration Data Format
```json
{
  "sender_config": {
    "receiver_host": "192.168.1.100",
    "receiver_port": 8765,
    "polling_rate": 60,
    "controllers": {
      "xbox_controller_0": {
        "assigned_number": 1,
        "input_method": "xinput",
        "enabled": true
      }
    }
  },
  "receiver_config": {
    "listen_port": 8765,
    "max_controllers": 4,
    "auto_create_virtual": true,
    "platform_specific": {
      "windows": {
        "use_vigem": true
      },
      "macos": {
        "use_pygame_virtual": true
      }
    }
  }
}
```

## Error Handling

### Network Error Handling
- **Connection Timeout:** Implement exponential backoff reconnection (1s, 2s, 4s, 8s, max 30s)
- **Data Transmission Errors:** Queue failed transmissions and retry on reconnection
- **Invalid Data:** Log and skip malformed input data packets
- **Server Unavailable:** Display clear status messages and continue input capture

### Controller Error Handling
- **Controller Disconnection:** Detect disconnection and notify receiver to remove virtual controller
- **Input Method Conflicts:** Fallback to available input method if preferred method fails
- **Permission Errors:** Provide clear instructions for required permissions (especially on macOS)
- **Driver Issues:** Detect ViGEmBus availability on Windows and provide installation guidance

### Platform-Specific Error Handling
- **Windows:** Handle ViGEmBus driver not installed, insufficient permissions for driver access
- **macOS:** Handle Input Monitoring permissions, Accessibility permissions for input simulation
- **Cross-Platform:** Handle missing Python dependencies with clear installation instructions

## Testing Strategy

### Unit Testing
- **Controller Detection:** Mock controller connections and test detection logic
- **Input Parsing:** Test input data formatting and parsing with various controller types
- **WebSocket Communication:** Mock WebSocket connections and test data transmission
- **Virtual Controller Creation:** Test virtual controller lifecycle management

### Integration Testing
- **End-to-End Input Flow:** Test complete input capture → transmission → simulation pipeline
- **Multi-Controller Scenarios:** Test with multiple controllers connected simultaneously
- **Network Resilience:** Test reconnection behavior under various network conditions
- **Cross-Platform Compatibility:** Test sender/receiver combinations across Windows/Mac

### Performance Testing
- **Input Latency:** Measure end-to-end latency from physical input to virtual output
- **Polling Rate Impact:** Test different polling rates and their effect on system performance
- **Memory Usage:** Monitor memory consumption during extended operation
- **Network Bandwidth:** Measure data transmission requirements under various usage patterns

### Platform Testing
- **Windows Testing:** Test with various controller types, ViGEmBus versions, Windows versions
- **macOS Testing:** Test with different macOS versions, permission scenarios, controller types
- **Cross-Platform Testing:** Test Windows sender → Mac receiver and Mac sender → Windows receiver