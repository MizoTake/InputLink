#!/usr/bin/env python3
"""Debug main window visibility hierarchy."""

import sys
import time
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, '../src')

from input_link.gui.application import InputLinkApplication
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState

def debug_window_hierarchy():
    """Debug the complete window visibility hierarchy."""
    print("=== DEBUGGING WINDOW VISIBILITY HIERARCHY ===")

    # Create GUI application
    gui_app = InputLinkApplication(sys.argv)

    # Get components
    main_window = gui_app.main_window
    stack_widget = gui_app.stacked_widget
    sender_window = gui_app.sender_window
    scroll_area = sender_window.controller_scroll_area

    print(f"Components created:")
    print(f"  Main Window: {main_window}")
    print(f"  Stack Widget: {stack_widget}")
    print(f"  Sender Window: {sender_window}")
    print(f"  Scroll Area: {scroll_area}")

    # Check initial visibility
    print(f"\\nInitial visibility:")
    print(f"  Main Window visible: {main_window.isVisible()}")
    print(f"  Stack Widget visible: {stack_widget.isVisible()}")
    print(f"  Sender Window visible: {sender_window.isVisible()}")
    print(f"  Scroll Area visible: {scroll_area.isVisible()}")
    print(f"  Current widget: {stack_widget.currentWidget()}")

    # Navigate to sender window (this is what happens when user clicks "Sender")
    print(f"\\n=== NAVIGATING TO SENDER WINDOW ===")
    stack_widget.setCurrentWidget(sender_window)
    gui_app.processEvents()

    print(f"After navigation:")
    print(f"  Current widget: {stack_widget.currentWidget()}")
    print(f"  Current widget is sender: {stack_widget.currentWidget() is sender_window}")
    print(f"  Sender Window visible: {sender_window.isVisible()}")
    print(f"  Scroll Area visible: {scroll_area.isVisible()}")

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

    # Mock the async worker
    mock_manager = Mock()
    mock_manager.scan_controllers.return_value = [test_controller]
    mock_manager.get_connected_controllers.return_value = [test_controller]
    gui_app.async_worker.controller_manager = mock_manager

    print(f"\\n=== ADDING CONTROLLER CARD ===")
    print(f"Before adding card:")
    print(f"  Sender visible: {sender_window.isVisible()}")
    print(f"  Scroll visible: {scroll_area.isVisible()}")
    print(f"  Cards widget visible: {scroll_area.cards_widget.isVisible()}")

    # Add controller directly
    sender_window.update_controllers([test_controller])
    gui_app.processEvents()

    print(f"After adding card:")
    print(f"  Sender visible: {sender_window.isVisible()}")
    print(f"  Scroll visible: {scroll_area.isVisible()}")
    print(f"  Cards widget visible: {scroll_area.cards_widget.isVisible()}")
    print(f"  Controller cards: {len(sender_window.controller_cards)}")

    if sender_window.controller_cards:
        card = sender_window.controller_cards[0]
        print(f"  Card visible: {card.isVisible()}")
        print(f"  Card parent: {card.parent()}")
        print(f"  Card size: {card.size()}")

        # Check parent hierarchy
        parent = card.parent()
        level = 0
        while parent and level < 10:
            print(f"    Parent[{level}]: {parent} - Visible: {parent.isVisible()}")
            parent = parent.parent()
            level += 1

    print(f"\\n=== FORCE VISIBILITY TEST ===")

    # Show main window if not visible
    if not main_window.isVisible():
        print("Showing main window...")
        main_window.show()
        gui_app.processEvents()

    # Force show sender window
    if not sender_window.isVisible():
        print("Force showing sender window...")
        sender_window.show()
        gui_app.processEvents()

    print(f"After forcing visibility:")
    print(f"  Main Window visible: {main_window.isVisible()}")
    print(f"  Sender Window visible: {sender_window.isVisible()}")
    print(f"  Scroll Area visible: {scroll_area.isVisible()}")

    if sender_window.controller_cards:
        card = sender_window.controller_cards[0]
        print(f"  Card visible: {card.isVisible()}")

    print(f"\\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_window_hierarchy()