#!/usr/bin/env python3
"""Test real controller scanning functionality."""

import sys
import time

# Add src to path
sys.path.insert(0, '../src')

from input_link.core import ControllerManager

def test_real_controller_scanning():
    """Test real controller scanning multiple times."""
    print("=== Real Controller Scanning Test ===")

    manager = ControllerManager()

    try:
        print("1. Initializing controller manager...")
        manager.initialize()

        # Perform multiple scans to test consistency
        for i in range(1, 4):
            print(f"\n{i}. Scan #{i}...")

            # Full scan
            all_controllers = manager.scan_controllers()
            connected_controllers = manager.get_connected_controllers()

            print(f"   Total controllers: {len(all_controllers)}")
            print(f"   Connected controllers: {len(connected_controllers)}")

            # Show details
            for j, controller in enumerate(all_controllers):
                status = "CONNECTED" if controller.state.name == "CONNECTED" else "DISCONNECTED"
                print(f"   [{j}] {controller.name} - {status} - {controller.identifier}")

            # Show only connected
            print(f"   Connected only:")
            for j, controller in enumerate(connected_controllers):
                print(f"   [{j}] {controller.name} - {controller.identifier}")

            if i < 3:
                print("   Waiting 2 seconds before next scan...")
                time.sleep(2)

        print(f"\n=== Internal State Inspection ===")
        print(f"Manager._controllers size: {len(manager._controllers)}")
        print(f"Assigned numbers: {manager._assigned_numbers}")

        # Test the key behavior: scan vs get_connected
        print(f"\n=== Key Behavior Verification ===")
        all_result = manager.scan_controllers()
        connected_result = manager.get_connected_controllers()

        print(f"scan_controllers() returns: {len(all_result)} controllers")
        print(f"get_connected_controllers() returns: {len(connected_result)} controllers")

        if len(connected_result) <= len(all_result):
            print("✓ Filtering is working correctly (connected <= total)")
        else:
            print("✗ Filtering issue detected (connected > total)")

        # Test that connected controllers are actually connected
        all_connected = all(c.state.name == "CONNECTED" for c in connected_result)
        print(f"All returned controllers are connected: {all_connected}")

    finally:
        manager.cleanup()
        print("\n=== Cleanup Complete ===")

if __name__ == "__main__":
    test_real_controller_scanning()