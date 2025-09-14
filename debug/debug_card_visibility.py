#!/usr/bin/env python3
"""Debug controller card visibility issue."""

import sys

# Add src to path
sys.path.insert(0, '../src')

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState
from input_link.gui.enhanced_widgets import EnhancedControllerCard, ModernCardScrollArea

def debug_card_visibility():
    """Debug card visibility in isolation."""
    print("=== DEBUGGING CARD VISIBILITY ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

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

    print(f"Test controller: {test_controller.name}")

    # Test 1: Create card in isolation
    print(f"\\n=== TEST 1: Card in isolation ===")
    test_card = EnhancedControllerCard(test_controller)
    print(f"Card created: {test_card}")
    print(f"Card visible: {test_card.isVisible()}")
    print(f"Card size: {test_card.size()}")

    # Explicitly show the card
    test_card.show()
    print(f"After show() - Card visible: {test_card.isVisible()}")

    # Test 2: Card in scroll area
    print(f"\\n=== TEST 2: Card in scroll area ===")
    scroll_area = ModernCardScrollArea()
    print(f"Scroll area created: {scroll_area}")
    print(f"Scroll area visible: {scroll_area.isVisible()}")

    # Add card to scroll area
    scroll_area.add_card(test_card)
    print(f"Card added to scroll area")
    print(f"Card visible: {test_card.isVisible()}")
    print(f"Card parent: {test_card.parent()}")

    # Test 3: Card in proper widget hierarchy
    print(f"\\n=== TEST 3: Full widget hierarchy ===")

    # Create main widget
    main_widget = QWidget()
    main_layout = QVBoxLayout()

    # Create new scroll area and card
    scroll_area2 = ModernCardScrollArea()
    test_card2 = EnhancedControllerCard(test_controller)

    print(f"Before adding to hierarchy:")
    print(f"  Card2 visible: {test_card2.isVisible()}")
    print(f"  Scroll2 visible: {scroll_area2.isVisible()}")
    print(f"  Main visible: {main_widget.isVisible()}")

    # Build hierarchy
    main_layout.addWidget(scroll_area2)
    main_widget.setLayout(main_layout)

    # Add card to scroll area
    scroll_area2.add_card(test_card2)

    print(f"After building hierarchy:")
    print(f"  Card2 visible: {test_card2.isVisible()}")
    print(f"  Scroll2 visible: {scroll_area2.isVisible()}")
    print(f"  Main visible: {main_widget.isVisible()}")

    # Show the main widget
    main_widget.show()

    print(f"After showing main widget:")
    print(f"  Card2 visible: {test_card2.isVisible()}")
    print(f"  Scroll2 visible: {scroll_area2.isVisible()}")
    print(f"  Main visible: {main_widget.isVisible()}")

    # Process events
    app.processEvents()

    print(f"After processEvents():")
    print(f"  Card2 visible: {test_card2.isVisible()}")
    print(f"  Scroll2 visible: {scroll_area2.isVisible()}")
    print(f"  Main visible: {main_widget.isVisible()}")

    # Test 4: Check internal structure
    print(f"\\n=== TEST 4: Internal structure ===")
    cards_widget = scroll_area2.cards_widget
    cards_layout = scroll_area2.cards_layout

    print(f"Cards widget: {cards_widget}")
    print(f"Cards widget visible: {cards_widget.isVisible()}")
    print(f"Cards layout count: {cards_layout.count()}")

    for i in range(cards_layout.count()):
        item = cards_layout.itemAt(i)
        if item and item.widget():
            widget = item.widget()
            print(f"  [{i}] Widget: {widget}")
            print(f"       Visible: {widget.isVisible()}")
            print(f"       Size: {widget.size()}")

    # Test 5: Force visibility
    print(f"\\n=== TEST 5: Force visibility ===")
    test_card2.setVisible(True)
    test_card2.show()
    cards_widget.setVisible(True)
    cards_widget.show()
    scroll_area2.setVisible(True)
    scroll_area2.show()

    app.processEvents()

    print(f"After forcing visibility:")
    print(f"  Card2 visible: {test_card2.isVisible()}")
    print(f"  Cards widget visible: {cards_widget.isVisible()}")
    print(f"  Scroll2 visible: {scroll_area2.isVisible()}")
    print(f"  Main visible: {main_widget.isVisible()}")

    print(f"\\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_card_visibility()