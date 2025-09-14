#!/usr/bin/env python3
"""Test the controller state persistence fix."""

import sys
import time

# Add src to path
sys.path.insert(0, '../src')

from input_link.core import ControllerManager
from input_link.core.controller_manager import ControllerConnectionState

def test_controller_persistence_fix():
    """Test that controllers maintain state across multiple scans."""
    print("=== TESTING CONTROLLER PERSISTENCE FIX ===")

    manager = ControllerManager(auto_assign_numbers=True)

    try:
        print("1. Initializing controller manager...")
        manager.initialize()

        # Perform first scan
        print(f"\\n2. First scan...")
        first_scan = manager.scan_controllers()
        connected_first = manager.get_connected_controllers()

        print(f"   Total controllers: {len(first_scan)}")
        print(f"   Connected controllers: {len(connected_first)}")

        for i, controller in enumerate(connected_first):
            print(f"   [{i}] {controller.name}")
            print(f"       State: {controller.state}")
            print(f"       Assigned Number: {controller.assigned_number}")
            print(f"       ID: {controller.identifier}")

        if not connected_first:
            print("   No controllers found - test cannot continue")
            return

        # Record initial state
        initial_controller = connected_first[0]
        initial_name = initial_controller.name
        initial_assigned_number = initial_controller.assigned_number
        initial_id = initial_controller.identifier

        print(f"\\n3. Recorded initial state:")
        print(f"   Name: {initial_name}")
        print(f"   Assigned Number: {initial_assigned_number}")
        print(f"   ID: {initial_id}")

        # Perform multiple rescans to test persistence
        for scan_num in range(2, 6):
            print(f"\\n{scan_num}. Rescan #{scan_num - 1}...")
            time.sleep(0.5)  # Small delay between scans

            rescan_result = manager.scan_controllers()
            connected_rescan = manager.get_connected_controllers()

            print(f"   Total controllers: {len(rescan_result)}")
            print(f"   Connected controllers: {len(connected_rescan)}")

            # Check if our original controller is still there
            found_original = False
            for controller in connected_rescan:
                if controller.identifier == initial_id:
                    found_original = True
                    print(f"   ✅ Original controller found:")
                    print(f"       Name: {controller.name}")
                    print(f"       State: {controller.state}")
                    print(f"       Assigned Number: {controller.assigned_number}")

                    # Verify persistence
                    if controller.assigned_number == initial_assigned_number:
                        print(f"   ✅ Assigned number preserved: {controller.assigned_number}")
                    else:
                        print(f"   ❌ Assigned number changed: {initial_assigned_number} -> {controller.assigned_number}")

                    if controller.state == ControllerConnectionState.CONNECTED:
                        print(f"   ✅ State is CONNECTED")
                    else:
                        print(f"   ❌ State is not CONNECTED: {controller.state}")
                    break

            if not found_original:
                print(f"   ❌ Original controller lost!")
                print(f"   Available controllers:")
                for i, controller in enumerate(connected_rescan):
                    print(f"     [{i}] {controller.name} - {controller.identifier}")

        print(f"\\n=== FINAL VERIFICATION ===")
        final_scan = manager.scan_controllers()
        final_connected = manager.get_connected_controllers()

        print(f"Final results:")
        print(f"  Total controllers: {len(final_scan)}")
        print(f"  Connected controllers: {len(final_connected)}")

        # Show all controller states
        print(f"\\nAll controller states:")
        for pygame_id, controller in manager._controllers.items():
            print(f"  pygame_id[{pygame_id}]: {controller.name}")
            print(f"    State: {controller.state}")
            print(f"    Assigned: {controller.assigned_number}")
            print(f"    ID: {controller.identifier}")

        print(f"\\nTest complete - check results above")

    finally:
        manager.cleanup()

if __name__ == "__main__":
    test_controller_persistence_fix()