#!/usr/bin/env python3
"""Test the GUI rescan fix - simulate user scenario."""

import sys
import time
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, '../src')

from input_link.gui.application import InputLinkApplication
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState

def test_gui_rescan_fix():
    """Test that GUI shows controllers consistently across multiple scans."""
    print("=== TESTING GUI RESCAN FIX ===")

    # Create GUI application
    gui_app = InputLinkApplication(sys.argv)
    sender_window = gui_app.sender_window
    async_worker = gui_app.async_worker

    # Navigate to sender window
    gui_app.stacked_widget.setCurrentWidget(sender_window)
    gui_app.processEvents()

    print("GUI setup complete")

    # Create test controllers
    test_controllers = [
        DetectedController(
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
    ]

    # Set up mock that properly uses the real ControllerManager logic
    real_manager = async_worker.controller_manager
    real_manager.initialize()

    # Add our test controller to the real manager's internal state
    real_manager._controllers = {0: test_controllers[0]}
    real_manager._assigned_numbers = {1}

    print(f"Mock setup complete - {len(test_controllers)} test controllers")

    # Hook into update_controllers to track calls
    update_results = []
    original_update = sender_window.update_controllers

    def track_update(controllers):
        call_num = len(update_results) + 1
        print(f"\\n>>> UPDATE #{call_num}: Received {len(controllers)} controllers")

        for i, ctrl in enumerate(controllers):
            print(f"    [{i}] {ctrl.name} - State: {ctrl.state} - Assigned: {ctrl.assigned_number}")

        result = original_update(controllers)
        update_results.append(controllers)

        print(f"    Cards after update: {len(sender_window.controller_cards)}")
        print(f"    Count label: '{sender_window.controller_count_label.text()}'")

        return result

    sender_window.update_controllers = track_update

    print(f"\\n=== PERFORMING USER SCENARIO: MULTIPLE SCANS ===")

    # Scan 1: Initial scan (should show controllers)
    print(f"\\n--- SCAN #1: Initial scan ---")
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.3)

    # Scan 2: Immediate rescan (user's problem: controllers disappear here)
    print(f"\\n--- SCAN #2: Immediate rescan (user issue point) ---")
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.3)

    # Scan 3: Another rescan
    print(f"\\n--- SCAN #3: Another rescan ---")
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.3)

    # Scan 4: Final rescan
    print(f"\\n--- SCAN #4: Final rescan ---")
    sender_window.scan_btn.click()
    gui_app.processEvents()
    time.sleep(0.3)

    print(f"\\n=== RESULTS ===")
    print(f"Total update calls: {len(update_results)}")

    success = True
    for i, controllers in enumerate(update_results):
        scan_num = i + 1
        if controllers:
            print(f"Scan #{scan_num}: SUCCESS - {len(controllers)} controllers shown")
        else:
            print(f"Scan #{scan_num}: FAIL - Controllers disappeared!")
            success = False

    print(f"\\nFinal UI state:")
    print(f"  Cards: {len(sender_window.controller_cards)}")
    print(f"  Count: '{sender_window.controller_count_label.text()}'")
    print(f"  Button: '{sender_window.scan_btn.text()}'")

    if success and len(sender_window.controller_cards) > 0:
        print(f"\\n🎉 SUCCESS: Fix works - controllers persist across rescans!")
    else:
        print(f"\\n❌ FAIL: Issue still exists - controllers disappearing")

    gui_app.close()

if __name__ == "__main__":
    test_gui_rescan_fix()