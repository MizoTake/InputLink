#!/usr/bin/env python3
"""Test ReceiverWindow scroll functionality with many controllers."""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from input_link.gui.receiver_window import ReceiverWindow

def test_scroll_with_many_controllers():
    """Test ReceiverWindow scroll functionality with many controllers."""
    print("Testing ReceiverWindow scroll functionality...")
    
    app = QApplication([])
    window = ReceiverWindow()
    window.show()
    
    test_results = []
    
    print("=== TESTING SCROLL AREA FUNCTIONALITY ===")
    
    # Test 1: Initial state
    print("1. Testing initial state...")
    initial_cards = len(window.virtual_controller_cards)
    print(f"Initial controller cards: {initial_cards}")
    
    if initial_cards == 4:
        test_results.append("[PASS] Initial 4 controller cards created")
    else:
        test_results.append(f"[FAIL] Expected 4 initial cards, got {initial_cards}")
    
    # Test 2: Check scroll area exists
    print("2. Testing scroll area presence...")
    if hasattr(window, 'controllers_scroll'):
        test_results.append("[PASS] Scroll area created successfully")
        scroll_max_height = window.controllers_scroll.maximumHeight()
        print(f"Scroll area max height: {scroll_max_height}px")
        if scroll_max_height == 300:
            test_results.append("[PASS] Scroll area height limit set correctly")
        else:
            test_results.append(f"[FAIL] Expected max height 300px, got {scroll_max_height}px")
    else:
        test_results.append("[FAIL] Scroll area not found")
    
    # Test 3: Add controllers dynamically to test scrolling
    print("3. Testing dynamic controller addition...")
    
    controller_test_counts = [6, 8, 12, 16, 20]
    
    for count in controller_test_counts:
        print(f"Testing with {count} controllers...")
        
        # Simulate adding controllers by calling update_virtual_controller
        for i in range(1, count + 1):
            window.update_virtual_controller(i, True, f"Client-192.168.1.{100+i}")
        
        current_cards = len(window.virtual_controller_cards)
        if current_cards == count:
            test_results.append(f"[PASS] Successfully created {count} controller cards")
        else:
            test_results.append(f"[FAIL] Expected {count} cards, got {current_cards}")
        
        # Check if scroll area is still functional
        if hasattr(window, 'controllers_scroll'):
            scroll_widget = window.controllers_scroll.widget()
            if scroll_widget:
                widget_height = scroll_widget.sizeHint().height()
                print(f"Scroll content height with {count} controllers: {widget_height}px")
                
                if widget_height > 300:  # More than scroll area max height
                    test_results.append(f"[PASS] Scroll needed for {count} controllers (content: {widget_height}px)")
                else:
                    test_results.append(f"[INFO] No scroll needed for {count} controllers (content: {widget_height}px)")
    
    # Test 4: Settings adjustment
    print("4. Testing max controllers setting interaction...")
    
    # Test setting max controllers to 0 (no limit)
    original_setting = window.max_controllers_spin.value()
    print(f"Original max controllers setting: {original_setting}")
    
    window.max_controllers_spin.setValue(0)
    new_setting = window.max_controllers_spin.value()
    
    if new_setting == 0:
        test_results.append("[PASS] Can set max controllers to 0 (no limit)")
    else:
        test_results.append(f"[FAIL] Failed to set max controllers to 0, got {new_setting}")
    
    # Test 5: UI responsiveness with many controllers
    print("5. Testing UI responsiveness...")
    
    # Try to interact with the last controller card
    if len(window.virtual_controller_cards) >= 20:
        last_card = window.virtual_controller_cards[19]  # 20th controller
        card_visible = last_card.isVisible()
        
        if card_visible:
            test_results.append("[PASS] Controller cards remain visible with many controllers")
        else:
            test_results.append("[FAIL] Controller cards not visible with many controllers")
            
        # Check card properties
        card_height = last_card.height()
        if card_height > 0:
            test_results.append(f"[PASS] Controller cards maintain proper height ({card_height}px)")
        else:
            test_results.append("[FAIL] Controller cards have invalid height")
    
    # Test 6: Scroll bar visibility
    print("6. Testing scroll bar visibility...")
    
    if hasattr(window, 'controllers_scroll'):
        v_scrollbar = window.controllers_scroll.verticalScrollBar()
        if v_scrollbar:
            scrollbar_visible = v_scrollbar.isVisible()
            scrollbar_max = v_scrollbar.maximum()
            
            print(f"Vertical scrollbar visible: {scrollbar_visible}")
            print(f"Scrollbar maximum value: {scrollbar_max}")
            
            if scrollbar_visible and scrollbar_max > 0:
                test_results.append("[PASS] Scroll bar visible and functional when needed")
            elif not scrollbar_visible and scrollbar_max == 0:
                test_results.append("[INFO] Scroll bar hidden when not needed")
            else:
                test_results.append(f"[WARN] Scroll bar state inconsistent (visible: {scrollbar_visible}, max: {scrollbar_max})")
    
    # Print results
    print(f"\n=== SCROLL FUNCTIONALITY TEST RESULTS ===")
    print(f"Total tests: {len(test_results)}")
    
    passed = len([r for r in test_results if r.startswith("[PASS]")])
    failed = len([r for r in test_results if r.startswith("[FAIL]")])
    info = len([r for r in test_results if r.startswith("[INFO]")])
    warn = len([r for r in test_results if r.startswith("[WARN]")])
    
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Info: {info}")
    print(f"Warnings: {warn}")
    
    if failed == 0:
        print(f"[SUCCESS] All critical tests passed!")
    else:
        print(f"[ISSUES] {failed} tests failed")
    
    print(f"\nDetailed results:")
    for result in test_results:
        print(result)
    
    # Auto-close
    def close_window():
        print("\nClosing scroll test window...")
        window.close()
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(close_window)
    timer.start(5000)  # 5 seconds to see the UI
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_scroll_with_many_controllers())