#!/usr/bin/env python3
"""Debug rescan behavior - test multiple scans to identify disappearing controllers."""

import sys
import time
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, '../src')

from input_link.gui.application import InputLinkApplication
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState

def debug_rescan_behavior():
    """Debug what happens during multiple scans."""
    print("=== DEBUGGING RESCAN BEHAVIOR ===")

    # Create GUI application
    gui_app = InputLinkApplication(sys.argv)

    # Get components
    sender_window = gui_app.sender_window
    async_worker = gui_app.async_worker

    # Navigate to sender window
    gui_app.stacked_widget.setCurrentWidget(sender_window)
    gui_app.processEvents()

    print(f"Setup complete - navigated to sender window")

    # Create test controller
    test_controller = DetectedController(
        pygame_id=0,
        device_id=1,
        name="Test Xbox Controller",
        guid="030000005e040000ea020000000000000",
        num_axes=6,
        num_buttons=14,
        num_hats=1,
        state=ControllerConnectionState.CONNECTED,
        assigned_number=1
    )

    # Mock the controller manager to return test controller first time
    mock_manager = Mock()

    # Track call count
    scan_count = [0]

    def mock_scan_controllers():
        scan_count[0] += 1
        print(f"  Mock scan_controllers() called - call #{scan_count[0]}")

        if scan_count[0] == 1:
            # First scan: return controller
            return [test_controller]
        else:
            # Subsequent scans: might return empty (simulating the user's issue)
            # Let's test different scenarios
            return [test_controller]  # Always return controller for now

    def mock_get_connected():
        connected_count = mock_manager.get_connected_controllers.call_count + 1
        print(f"  Mock get_connected_controllers() called - call #{connected_count}")
        return [test_controller]  # Always return controller

    mock_manager.scan_controllers.side_effect = mock_scan_controllers
    mock_manager.get_connected_controllers.side_effect = mock_get_connected
    async_worker.controller_manager = mock_manager

    # Hook into update_controllers to track calls
    original_update = sender_window.update_controllers
    update_calls = []

    def debug_update(controllers):
        call_num = len(update_calls) + 1
        print(f"\\n  >>> update_controllers() call #{call_num}")
        print(f"      Received {len(controllers)} controllers")
        for i, ctrl in enumerate(controllers):
            print(f"        [{i}] {ctrl.name}")

        print(f"      Before: {len(sender_window.controller_cards)} cards")
        result = original_update(controllers)
        print(f"      After: {len(sender_window.controller_cards)} cards")

        if sender_window.controller_cards:
            for i, card in enumerate(sender_window.controller_cards):
                print(f"        Card[{i}]: Visible={card.isVisible()}, Size={card.size()}")
        else:
            print("        No cards!")

        update_calls.append(controllers)
        return result

    sender_window.update_controllers = debug_update

    print(f"\\n=== PERFORMING MULTIPLE SCANS ===")

    # Scan 1: First scan
    print(f"\\n--- SCAN #1 (First scan) ---")
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.2)

    # Scan 2: Immediate rescan
    print(f"\\n--- SCAN #2 (Immediate rescan) ---")
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.2)

    # Scan 3: After delay
    print(f"\\n--- SCAN #3 (After delay) ---")
    time.sleep(1)
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.2)

    # Test different mock scenarios
    print(f"\\n=== TESTING EMPTY RESULTS SCENARIO ===")

    # Change mock to return empty on subsequent calls
    def mock_scan_empty():
        scan_count[0] += 1
        print(f"  Mock scan_controllers() called - call #{scan_count[0]}")

        if scan_count[0] <= 3:
            return [test_controller]  # Previous calls already made
        else:
            print("    >>> Returning EMPTY results (simulating user issue)")
            return []  # Empty results

    def mock_get_connected_empty():
        connected_count = mock_manager.get_connected_controllers.call_count + 1
        print(f"  Mock get_connected_controllers() called - call #{connected_count}")

        if connected_count <= 3:
            return [test_controller]
        else:
            print("    >>> Returning EMPTY connected controllers")
            return []

    mock_manager.scan_controllers.side_effect = mock_scan_empty
    mock_manager.get_connected_controllers.side_effect = mock_get_connected_empty

    # Scan 4: With empty results
    print(f"\\n--- SCAN #4 (Empty results test) ---")
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.2)

    # Scan 5: Another empty scan
    print(f"\\n--- SCAN #5 (Another empty scan) ---")
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.2)

    print(f"\\n=== FINAL RESULTS ===")
    print(f"Total update_controllers calls: {len(update_calls)}")
    print(f"Total scan_controllers calls: {scan_count[0]}")
    print(f"Final UI state:")
    print(f"  Cards count: {len(sender_window.controller_cards)}")
    print(f"  Count label: '{sender_window.controller_count_label.text()}'")
    print(f"  Button text: '{sender_window.scan_btn.text()}'")

    if sender_window.controller_cards:
        print(f"  Cards visibility:")
        for i, card in enumerate(sender_window.controller_cards):
            print(f"    [{i}] Visible: {card.isVisible()}, Size: {card.size()}")

    print(f"\\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_rescan_behavior()