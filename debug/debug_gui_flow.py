#!/usr/bin/env python3
"""Debug GUI controller display flow in detail."""

import sys
import time
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add src to path
sys.path.insert(0, '../src')

from input_link.gui.application import InputLinkApplication
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState

def debug_gui_controller_flow():
    """Debug the complete GUI controller display flow."""
    print("=== Debugging GUI Controller Display Flow ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create the actual GUI application
    gui_app = InputLinkApplication([])

    # Access the components
    sender_window = gui_app.sender_window
    async_worker = gui_app.async_worker

    print(f"GUI App created: {gui_app}")
    print(f"Sender Window: {sender_window}")
    print(f"Async Worker: {async_worker}")
    print(f"Controller Manager: {getattr(async_worker, 'controller_manager', 'None')}")

    # Create test controller
    test_controller = DetectedController(
        pygame_id=0,
        device_id=1,
        name="DEBUG Xbox Controller",
        guid="030003f05e0400008e02000000007200",
        num_axes=6,
        num_buttons=14,
        num_hats=1,
        state=ControllerConnectionState.CONNECTED,
        assigned_number=1
    )

    print(f"\nTest Controller: {test_controller.name}")
    print(f"Controller ID: {test_controller.identifier}")

    # Patch the controller manager to return our test controller
    mock_manager = Mock()
    mock_manager.initialize.return_value = None
    mock_manager.scan_controllers.return_value = [test_controller]
    mock_manager.get_connected_controllers.return_value = [test_controller]
    async_worker.controller_manager = mock_manager

    print(f"Mock manager set: {mock_manager}")

    # Hook into SenderWindow.update_controllers to track calls
    original_update_controllers = sender_window.update_controllers

    def debug_update_controllers(controllers):
        print(f"\n=== SenderWindow.update_controllers() CALLED ===")
        print(f"Controllers received: {len(controllers)}")
        for i, controller in enumerate(controllers):
            print(f"  [{i}] {controller.name} - {controller.state} - {controller.identifier}")

        print(f"Before update - Current cards: {len(sender_window.controller_cards)}")

        # Call the original method
        result = original_update_controllers(controllers)

        print(f"After update - Controller cards: {len(sender_window.controller_cards)}")
        print(f"Scan button text: '{sender_window.scan_btn.text()}'")
        print(f"Scan button enabled: {sender_window.scan_btn.isEnabled()}")
        print(f"Controller count label: '{sender_window.controller_count_label.text()}'")

        # Check scroll area
        print(f"Scroll area widget count: {getattr(sender_window.controller_scroll_area, '_card_count', 'unknown')}")

        return result

    sender_window.update_controllers = debug_update_controllers

    # Hook into AsyncWorker controller detection
    detected_controllers_log = []

    def log_controller_detected(controllers):
        print(f"\n=== controller_detected SIGNAL EMITTED ===")
        print(f"Signal payload: {len(controllers)} controllers")
        for i, controller in enumerate(controllers):
            print(f"  [{i}] {controller.name} - {controller.state}")
        detected_controllers_log.append(controllers)

    async_worker.controller_detected.connect(log_controller_detected)

    print(f"\n=== Starting Debug Test ===")

    # Test 1: Direct update_controllers call
    print(f"\n1. Testing direct update_controllers() call...")
    sender_window.update_controllers([test_controller])

    # Process events
    app.processEvents()
    time.sleep(0.1)

    # Test 2: AsyncWorker scan_controllers
    print(f"\n2. Testing AsyncWorker.scan_controllers()...")
    async_worker.scan_controllers()

    # Process events
    app.processEvents()
    time.sleep(0.1)

    # Test 3: SenderWindow scan request
    print(f"\n3. Testing SenderWindow scan button signal...")
    sender_window.scan_controllers_requested.emit()

    # Process events
    app.processEvents()
    time.sleep(0.1)

    print(f"\n=== Final State ===")
    print(f"Total controller_detected signals: {len(detected_controllers_log)}")
    print(f"Final controller cards count: {len(sender_window.controller_cards)}")
    print(f"Sender window visible: {sender_window.isVisible()}")

    # Check if cards were actually created
    if sender_window.controller_cards:
        for i, card in enumerate(sender_window.controller_cards):
            print(f"Card [{i}]: {type(card)} - Visible: {card.isVisible()}")

    # Clean up
    gui_app.close()
    print(f"\nDebug complete.")

if __name__ == "__main__":
    debug_gui_controller_flow()