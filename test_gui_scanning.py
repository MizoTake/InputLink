#!/usr/bin/env python3
"""Test GUI scanning functionality by simulating user interactions."""

import sys
import time
import threading
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add src to path
sys.path.insert(0, 'src')

from input_link.gui.application import InputLinkApplication, AsyncWorker
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState

def simulate_controller_scanning():
    """Simulate controller scanning operations."""
    print("=== GUI Controller Scanning Test ===")

    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create minimal test setup
    async_worker = AsyncWorker()

    # Mock controller data
    test_controller = DetectedController(
        pygame_id=0,
        device_id=1,
        name="Test Xbox 360 Controller",
        guid="030003f05e0400008e02000000007200",
        num_axes=6,
        num_buttons=14,
        num_hats=1,
        state=ControllerConnectionState.CONNECTED,
        assigned_number=1
    )

    # Create mock controller manager
    mock_manager = Mock()
    mock_manager.scan_controllers.return_value = [test_controller]
    mock_manager.get_connected_controllers.return_value = [test_controller]
    async_worker.controller_manager = mock_manager

    # Track emitted signals
    detected_controllers = []
    log_messages = []

    async_worker.controller_detected.connect(lambda c: detected_controllers.append(c))
    async_worker.log_message.connect(lambda m: log_messages.append(m))

    print("1. Testing initial controller scan...")
    async_worker.scan_controllers()

    # Process Qt events
    app.processEvents()
    time.sleep(0.1)

    print(f"   Controllers detected: {len(detected_controllers[-1]) if detected_controllers else 0}")
    if detected_controllers:
        for i, controller in enumerate(detected_controllers[-1]):
            print(f"   [{i}] {controller.name} - State: {controller.state}")

    print(f"   Log messages: {log_messages[-1] if log_messages else 'None'}")

    print("\n2. Testing rescan with same controller...")
    async_worker.scan_controllers()

    # Process Qt events
    app.processEvents()
    time.sleep(0.1)

    print(f"   Controllers detected: {len(detected_controllers[-1]) if len(detected_controllers) > 1 else 0}")
    if len(detected_controllers) > 1:
        for i, controller in enumerate(detected_controllers[-1]):
            print(f"   [{i}] {controller.name} - State: {controller.state}")

    print(f"   Log messages: {log_messages[-1] if len(log_messages) > 1 else 'None'}")

    print("\n3. Testing scan with disconnected controller...")
    # Update mock to return disconnected controller
    disconnected_controller = DetectedController(
        pygame_id=0,
        device_id=1,
        name="Test Xbox 360 Controller",
        guid="030003f05e0400008e02000000007200",
        num_axes=6,
        num_buttons=14,
        num_hats=1,
        state=ControllerConnectionState.DISCONNECTED,
        assigned_number=1
    )

    mock_manager.scan_controllers.return_value = [disconnected_controller]
    mock_manager.get_connected_controllers.return_value = []  # No connected controllers

    async_worker.scan_controllers()

    # Process Qt events
    app.processEvents()
    time.sleep(0.1)

    print(f"   Controllers detected: {len(detected_controllers[-1]) if len(detected_controllers) > 2 else 0}")
    print(f"   Log messages: {log_messages[-1] if len(log_messages) > 2 else 'None'}")

    print("\n4. Testing scan with controller reconnected...")
    # Reconnect controller
    mock_manager.scan_controllers.return_value = [test_controller]
    mock_manager.get_connected_controllers.return_value = [test_controller]

    async_worker.scan_controllers()

    # Process Qt events
    app.processEvents()
    time.sleep(0.1)

    print(f"   Controllers detected: {len(detected_controllers[-1]) if len(detected_controllers) > 3 else 0}")
    if len(detected_controllers) > 3:
        for i, controller in enumerate(detected_controllers[-1]):
            print(f"   [{i}] {controller.name} - State: {controller.state}")

    print(f"   Log messages: {log_messages[-1] if len(log_messages) > 3 else 'None'}")

    print("\n=== Test Summary ===")
    print(f"Total scans performed: {len(detected_controllers)}")
    print(f"Total log messages: {len(log_messages)}")

    # Verify filtering is working
    if len(detected_controllers) >= 4:
        scan1_count = len(detected_controllers[0])  # First scan: 1 controller
        scan2_count = len(detected_controllers[1])  # Second scan: 1 controller
        scan3_count = len(detected_controllers[2])  # Third scan: 0 controllers (disconnected)
        scan4_count = len(detected_controllers[3])  # Fourth scan: 1 controller (reconnected)

        print(f"Scan results: {scan1_count} -> {scan2_count} -> {scan3_count} -> {scan4_count}")

        if scan1_count == 1 and scan2_count == 1 and scan3_count == 0 and scan4_count == 1:
            print("✅ Controller filtering is working correctly!")
        else:
            print("❌ Controller filtering may have issues")

    print("Test completed.")

if __name__ == "__main__":
    simulate_controller_scanning()