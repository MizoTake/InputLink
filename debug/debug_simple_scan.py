#!/usr/bin/env python3
"""Simple debug script to test controller scanning with mock data."""

import sys
import time
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, '../src')

from input_link.gui.application import InputLinkApplication
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState

def main():
    """Main debug function."""
    print("=== SIMPLE CONTROLLER SCAN DEBUG ===")

    # Create the GUI application (this creates the QApplication)
    gui_app = InputLinkApplication(sys.argv)

    # Get references
    sender_window = gui_app.sender_window
    async_worker = gui_app.async_worker

    print(f"GUI App created successfully")
    print(f"Sender Window: {sender_window}")
    print(f"Async Worker: {async_worker}")

    # Create test controllers
    test_controllers = [
        DetectedController(
            pygame_id=0,
            device_id=1,
            name="DEBUG Xbox Controller",
            guid="030000005e040000ea020000000000000",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )
    ]

    print(f"Test controller: {test_controllers[0].name}")

    # Mock the controller manager
    mock_manager = Mock()
    mock_manager.scan_controllers.return_value = test_controllers
    mock_manager.get_connected_controllers.return_value = test_controllers
    async_worker.controller_manager = mock_manager

    # Hook into update_controllers to see what happens
    original_update = sender_window.update_controllers
    update_calls = []

    def debug_update(controllers):
        print(f"\\n=== update_controllers() CALLED ===")
        print(f"Received {len(controllers)} controllers:")
        for i, ctrl in enumerate(controllers):
            print(f"  [{i}] {ctrl.name} - {ctrl.state}")

        print(f"Before update:")
        print(f"  Cards: {len(sender_window.controller_cards)}")
        print(f"  Count label: '{sender_window.controller_count_label.text()}'")

        result = original_update(controllers)
        update_calls.append(controllers)

        print(f"After update:")
        print(f"  Cards: {len(sender_window.controller_cards)}")
        print(f"  Count label: '{sender_window.controller_count_label.text()}'")
        print(f"  Scan button: '{sender_window.scan_btn.text()}'")
        return result

    sender_window.update_controllers = debug_update

    # Show sender window
    print(f"\\nNavigating to sender window...")
    gui_app.stacked_widget.setCurrentWidget(sender_window)

    # Test direct update first
    print(f"\\n=== TEST 1: Direct update_controllers() ===")
    sender_window.update_controllers(test_controllers)

    # Process events
    gui_app.processEvents()

    # Test scan button click
    print(f"\\n=== TEST 2: Scan button click ===")
    sender_window.scan_btn.click()

    # Process events and wait
    gui_app.processEvents()
    time.sleep(0.5)

    # Test async worker scan directly
    print(f"\\n=== TEST 3: Async worker scan ===")
    async_worker.scan_controllers()

    # Process events and wait
    gui_app.processEvents()
    time.sleep(0.5)

    print(f"\\n=== RESULTS ===")
    print(f"Update calls: {len(update_calls)}")
    print(f"Final UI state:")
    print(f"  Cards: {len(sender_window.controller_cards)}")
    print(f"  Count: '{sender_window.controller_count_label.text()}'")
    print(f"  Button: '{sender_window.scan_btn.text()}'")

    if sender_window.controller_cards:
        print(f"Cards details:")
        for i, card in enumerate(sender_window.controller_cards):
            print(f"  [{i}] Type: {type(card)}")
            print(f"       Visible: {card.isVisible()}")
            print(f"       Size: {card.size()}")
    else:
        print("No cards found!")

    print(f"\\nDebug complete - check above output for issues")

if __name__ == "__main__":
    main()