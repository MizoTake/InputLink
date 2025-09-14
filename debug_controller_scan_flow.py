#!/usr/bin/env python3
"""Debug complete controller scanning signal flow in GUI."""

import sys
import time
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add src to path
sys.path.insert(0, 'src')

from input_link.gui.application import InputLinkApplication
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState

def debug_scan_signal_flow():
    """Debug complete controller scan signal flow."""
    print("=== DEBUGGING COMPLETE SCAN SIGNAL FLOW ===")

    # Ensure clean Qt environment
    app = QApplication.instance()
    if app is not None:
        app.quit()
        app = None

    app = QApplication(sys.argv)

    # Create GUI application
    gui_app = InputLinkApplication([])

    # Get references to components
    sender_window = gui_app.sender_window
    async_worker = gui_app.async_worker
    main_window = gui_app.main_window
    stack_widget = gui_app.stack_widget

    print(f"Components:")
    print(f"  GUI App: {gui_app}")
    print(f"  Main Window: {main_window}")
    print(f"  Stack Widget: {stack_widget}")
    print(f"  Sender Window: {sender_window}")
    print(f"  Async Worker: {async_worker}")
    print(f"  Controller Manager: {getattr(async_worker, 'controller_manager', 'None')}")

    # Create test controllers
    test_controllers = [
        DetectedController(
            pygame_id=0,
            device_id=1,
            name="Test Xbox Controller 1",
            guid="030000005e040000ea020000000000000",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        ),
        DetectedController(
            pygame_id=1,
            device_id=2,
            name="Test PS4 Controller",
            guid="030000004c050000cc090000000000000",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=2
        )
    ]

    print(f"\\nTest Controllers Created:")
    for i, controller in enumerate(test_controllers):
        print(f"  [{i}] {controller.name} - {controller.state} - {controller.identifier}")

    # Mock controller manager to return test controllers
    mock_manager = Mock()
    mock_manager.initialize.return_value = None
    mock_manager.scan_controllers.return_value = test_controllers
    mock_manager.get_connected_controllers.return_value = test_controllers
    async_worker.controller_manager = mock_manager

    print(f"Controller manager mocked")

    # Hook into all signal handlers to trace the flow
    print(f"\\n=== HOOKING INTO SIGNAL HANDLERS ===")

    # Hook 1: SenderWindow scan button click
    original_scan = sender_window._scan_controllers
    scan_click_count = [0]

    def debug_scan_click():
        scan_click_count[0] += 1
        print(f"\\n>>> [STEP 1] SenderWindow._scan_controllers() CALLED (click #{scan_click_count[0]})")
        print(f"    Scan button state before: '{sender_window.scan_btn.text()}' - Enabled: {sender_window.scan_btn.isEnabled()}")
        result = original_scan()
        print(f"    Signal emitted: scan_controllers_requested")
        return result

    sender_window._scan_controllers = debug_scan_click

    # Hook 2: AsyncWorker scan handler
    original_async_scan = async_worker.scan_controllers
    async_scan_count = [0]

    def debug_async_scan():
        async_scan_count[0] += 1
        print(f"\\n>>> [STEP 2] AsyncWorker.scan_controllers() CALLED (#{async_scan_count[0]})")
        print(f"    About to call controller_manager.scan_controllers()")
        result = original_async_scan()
        print(f"    AsyncWorker scan complete, signal should be emitted")
        return result

    async_worker.scan_controllers = debug_async_scan

    # Hook 3: InputLinkApplication controller detection handler
    original_controller_handler = gui_app._on_controllers_detected
    handler_call_count = [0]

    def debug_controller_handler(controllers):
        handler_call_count[0] += 1
        print(f"\\n>>> [STEP 3] InputLinkApplication._on_controllers_detected() CALLED (#{handler_call_count[0]})")
        print(f"    Received {len(controllers)} controllers")
        for i, controller in enumerate(controllers):
            print(f"      [{i}] {controller.name} - {controller.state}")
        result = original_controller_handler(controllers)
        print(f"    About to call sender_window.update_controllers() with {len(controllers)} controllers")
        return result

    gui_app._on_controllers_detected = debug_controller_handler

    # Hook 4: SenderWindow update controllers
    original_update = sender_window.update_controllers
    update_call_count = [0]

    def debug_update_controllers(controllers):
        update_call_count[0] += 1
        print(f"\\n>>> [STEP 4] SenderWindow.update_controllers() CALLED (#{update_call_count[0]})")
        print(f"    Received {len(controllers)} controllers")
        print(f"    Before update - Existing cards: {len(sender_window.controller_cards)}")
        print(f"    Scroll area visible: {sender_window.controller_scroll_area.isVisible()}")
        result = original_update(controllers)
        print(f"    After update - Cards: {len(sender_window.controller_cards)}")
        print(f"    Scan button: '{sender_window.scan_btn.text()}' - Enabled: {sender_window.scan_btn.isEnabled()}")
        print(f"    Count label: '{sender_window.controller_count_label.text()}'")

        # Check if cards were actually added to the scroll area
        if hasattr(sender_window.controller_scroll_area, '_cards'):
            scroll_cards = getattr(sender_window.controller_scroll_area, '_cards', [])
            print(f"    Scroll area cards: {len(scroll_cards)}")
        return result

    sender_window.update_controllers = debug_update_controllers

    print(f"All signal handlers hooked")

    # Navigate to sender window
    print(f"\\n=== NAVIGATING TO SENDER WINDOW ===")
    stack_widget.setCurrentWidget(sender_window)
    app.processEvents()
    time.sleep(0.1)

    current_widget = stack_widget.currentWidget()
    print(f"Current widget: {current_widget}")
    print(f"Is sender window: {current_widget is sender_window}")
    print(f"Sender window visible: {sender_window.isVisible()}")

    # Trigger scan
    print(f"\\n=== TRIGGERING CONTROLLER SCAN ===")
    print(f"Initial state:")
    print(f"  Scan button: '{sender_window.scan_btn.text()}' - Enabled: {sender_window.scan_btn.isEnabled()}")
    print(f"  Controller cards: {len(sender_window.controller_cards)}")
    print(f"  Count label: '{sender_window.controller_count_label.text()}'")

    # Click scan button
    print(f"\\nClicking scan button...")
    sender_window.scan_btn.click()

    # Process events to allow signal propagation
    print(f"Processing events...")
    app.processEvents()
    time.sleep(0.5)  # Allow time for async operations

    # Check final state
    print(f"\\n=== FINAL STATE ===")
    print(f"Call counts:")
    print(f"  Scan button clicks: {scan_click_count[0]}")
    print(f"  AsyncWorker scans: {async_scan_count[0]}")
    print(f"  Controller handlers: {handler_call_count[0]}")
    print(f"  Update calls: {update_call_count[0]}")

    print(f"\\nUI state:")
    print(f"  Scan button: '{sender_window.scan_btn.text()}' - Enabled: {sender_window.scan_btn.isEnabled()}")
    print(f"  Controller cards: {len(sender_window.controller_cards)}")
    print(f"  Count label: '{sender_window.controller_count_label.text()}'")

    # Check card details
    if sender_window.controller_cards:
        print(f"\\nController card details:")
        for i, card in enumerate(sender_window.controller_cards):
            print(f"  [{i}] {type(card)} - Visible: {card.isVisible()} - Parent: {card.parent()}")
    else:
        print("\\nNo controller cards found!")

    # Check scroll area
    if hasattr(sender_window.controller_scroll_area, 'show_empty_message'):
        is_showing_empty = not sender_window.controller_scroll_area.isVisible() if hasattr(sender_window.controller_scroll_area, '_empty_label') else False
        print(f"\\nScroll area empty message showing: {is_showing_empty}")

    # Clean up
    gui_app.close()
    app.quit()
    print(f"\\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_scan_signal_flow()