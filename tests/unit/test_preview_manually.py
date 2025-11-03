"""Manual test script to verify preview polling works after sender stop."""

import asyncio
import pygame
from input_link.apps.sender import SenderApp
from input_link.core import ControllerManager
from input_link.models import ConfigModel, SenderConfig, ReceiverConfig


async def test_preview_after_stop():
    """Test that controller_manager is accessible in status callback."""

    print("\n" + "="*60)
    print("MANUAL TEST: Preview Polling After Sender Stop")
    print("="*60 + "\n")

    # Track what happens
    callback_results = []

    def status_callback(status: str):
        print(f"\n>>> Status callback called: {status}")
        if status == "stopped":
            # Try to access controller manager
            if test_app.controller_manager is not None:
                controllers = test_app.controller_manager.get_connected_controllers()
                callback_results.append({
                    "status": status,
                    "controller_manager_available": True,
                    "controllers_count": len(controllers)
                })
                print(f">>> Controller manager IS available: {len(controllers)} controllers")
            else:
                callback_results.append({
                    "status": status,
                    "controller_manager_available": False,
                    "controllers_count": 0
                })
                print(f">>> Controller manager is NOT available")

    # Create config
    config = ConfigModel(
        sender_config=SenderConfig(
            receiver_host="127.0.0.1",
            receiver_port=9999,  # Non-existent port to avoid actual connection
        ),
        receiver_config=ReceiverConfig(
            listen_port=9999,  # Match sender port
        ),
    )

    # Create sender app in GUI mode
    test_app = SenderApp(
        status_callback=status_callback,
        cleanup_controller_manager=False,
    )
    test_app.config = config

    print("Step 1: Initializing components...")
    await test_app._initialize_components()
    print(f"  [OK] Controller manager created: {test_app.controller_manager is not None}")

    print("\nStep 2: Scanning for controllers...")
    controllers = test_app.controller_manager.scan_controllers()
    print(f"  [OK] Found {len(controllers)} controllers")
    for c in controllers:
        print(f"    - {c.name} (ID: {c.identifier})")

    print("\nStep 3: Calling _cleanup() to simulate stop...")
    await test_app._cleanup()

    print("\nStep 4: Checking results...")
    if len(callback_results) > 0:
        result = callback_results[0]
        print(f"  Status: {result['status']}")
        print(f"  Controller manager available: {result['controller_manager_available']}")
        print(f"  Controllers count: {result['controllers_count']}")

        if result['controller_manager_available'] and result['controllers_count'] > 0:
            print("\n[PASS] TEST PASSED: Controller manager is accessible in status callback")
            return True
        else:
            print("\n[FAIL] TEST FAILED: Controller manager is NOT accessible in status callback")
            return False
    else:
        print("\n[FAIL] TEST FAILED: Status callback was not called")
        return False


if __name__ == "__main__":
    # Initialize pygame for the test
    pygame.init()
    pygame.joystick.init()

    try:
        result = asyncio.run(test_preview_after_stop())
        exit(0 if result else 1)
    finally:
        pygame.joystick.quit()
        pygame.quit()
