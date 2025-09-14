#!/usr/bin/env python3
"""Debug controller scanning behavior."""

import sys
import time
from src.input_link.core import ControllerManager

def debug_controller_scanning():
    """Debug controller scanning behavior step by step."""
    print("=== Debug Controller Scanning ===")

    manager = ControllerManager()

    try:
        print("1. Initializing controller manager...")
        manager.initialize()
        print("   Initialized successfully")

        print("\n2. First scan...")
        controllers_first = manager.scan_controllers()
        print(f"   scan_controllers() returned: {len(controllers_first)} controllers")

        for i, controller in enumerate(controllers_first):
            print(f"   [{i}] {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        connected_first = manager.get_connected_controllers()
        print(f"   get_connected_controllers() returned: {len(connected_first)} controllers")

        for i, controller in enumerate(connected_first):
            print(f"   [{i}] {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        print("\n3. Waiting 2 seconds...")
        time.sleep(2)

        print("4. Second scan (rescan)...")
        controllers_second = manager.scan_controllers()
        print(f"   scan_controllers() returned: {len(controllers_second)} controllers")

        for i, controller in enumerate(controllers_second):
            print(f"   [{i}] {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        connected_second = manager.get_connected_controllers()
        print(f"   get_connected_controllers() returned: {len(connected_second)} controllers")

        for i, controller in enumerate(connected_second):
            print(f"   [{i}] {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        print("\n5. Third scan (rescan again)...")
        controllers_third = manager.scan_controllers()
        print(f"   scan_controllers() returned: {len(controllers_third)} controllers")

        for i, controller in enumerate(controllers_third):
            print(f"   [{i}] {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        connected_third = manager.get_connected_controllers()
        print(f"   get_connected_controllers() returned: {len(connected_third)} controllers")

        for i, controller in enumerate(connected_third):
            print(f"   [{i}] {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        print("\n=== Internal state inspection ===")
        print(f"Internal _controllers dict size: {len(manager._controllers)}")
        print(f"Assigned numbers: {manager._assigned_numbers}")

        for pygame_id, controller in manager._controllers.items():
            print(f"  pygame_id={pygame_id}: {controller.name} - {controller.state} - {controller.identifier}")

    finally:
        manager.cleanup()
        print("\nCleanup complete")

if __name__ == "__main__":
    debug_controller_scanning()