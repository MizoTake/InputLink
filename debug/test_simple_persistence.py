#!/usr/bin/env python3
"""Simple test for controller persistence without Unicode."""

import sys
import time

# Add src to path
sys.path.insert(0, '../src')

from input_link.core import ControllerManager
from input_link.core.controller_manager import ControllerConnectionState

def test_simple_persistence():
    """Simple test for controller persistence."""
    print("=== SIMPLE CONTROLLER PERSISTENCE TEST ===")

    manager = ControllerManager(auto_assign_numbers=True)

    try:
        manager.initialize()

        # First scan
        print("\\n1. First scan...")
        first_result = manager.get_connected_controllers()
        print(f"   Connected: {len(first_result)}")

        if first_result:
            controller = first_result[0]
            print(f"   Name: {controller.name}")
            print(f"   Assigned: {controller.assigned_number}")
            print(f"   State: {controller.state}")

            # Multiple rescans
            for i in range(2, 6):
                print(f"\\n{i}. Rescan #{i-1}...")
                time.sleep(0.2)

                rescan_result = manager.get_connected_controllers()
                print(f"   Connected: {len(rescan_result)}")

                if rescan_result:
                    controller = rescan_result[0]
                    print(f"   Name: {controller.name}")
                    print(f"   Assigned: {controller.assigned_number}")
                    print(f"   State: {controller.state}")

                    if controller.assigned_number == first_result[0].assigned_number:
                        print("   SUCCESS: Assigned number preserved")
                    else:
                        print("   FAIL: Assigned number changed")
                else:
                    print("   FAIL: No controllers found")

            print(f"\\n=== FINAL STATE ===")
            final_result = manager.get_connected_controllers()
            print(f"Final connected controllers: {len(final_result)}")

            if final_result:
                print("SUCCESS: Controllers persisted through multiple scans")
            else:
                print("FAIL: Controllers disappeared")

        else:
            print("No controllers found - cannot test persistence")

    finally:
        manager.cleanup()

if __name__ == "__main__":
    test_simple_persistence()