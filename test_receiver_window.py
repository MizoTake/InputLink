#!/usr/bin/env python3
"""Test ReceiverWindow functionality."""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from input_link.gui.receiver_window import ReceiverWindow

def test_receiver_window_functionality():
    """Test ReceiverWindow specific functionality."""
    print("Starting ReceiverWindow functionality test...")
    
    app = QApplication([])
    window = ReceiverWindow()
    
    # Test 1: Signal connections
    signals_triggered = []
    
    def on_start_server():
        signals_triggered.append("start_server")
        print("START_SERVER signal triggered")
        
    def on_stop_server():
        signals_triggered.append("stop_server")
        print("STOP_SERVER signal triggered")
    
    window.start_server.connect(on_start_server)
    window.stop_server.connect(on_stop_server)
    
    # Test 2: Button functionality
    print("Testing button functionality...")
    
    # Test server toggle
    print("Testing server toggle...")
    initial_text = window.start_btn.text()
    print(f"Initial button text: {initial_text}")
    
    window.start_btn.click()  # Should start server
    after_start_text = window.start_btn.text()
    print(f"After start click: {after_start_text}")
    
    window.start_btn.click()  # Should stop server
    after_stop_text = window.start_btn.text()
    print(f"After stop click: {after_stop_text}")
    
    # Test 3: Settings functionality
    print("Testing settings...")
    window.port_spin.setValue(9876)
    window.max_controllers_spin.setValue(8)
    window.auto_create_checkbox.setChecked(True)
    
    print(f"Port setting: {window.port_spin.value()}")
    print(f"Max controllers setting: {window.max_controllers_spin.value()}")
    print(f"Auto create setting: {window.auto_create_checkbox.isChecked()}")
    
    # Test 4: Status updates
    print("Testing status updates...")
    window.update_server_status("Listening on 0.0.0.0:9876", "#34C759")
    window.update_connection_count(2)
    print("Server status and connection count updated")
    
    # Test 5: Virtual controller updates
    print("Testing virtual controller updates...")
    window.update_virtual_controller(1, True, "Client-192.168.1.100")
    window.update_virtual_controller(2, True, "Client-192.168.1.101")
    window.update_virtual_controller(3, False)
    print("Virtual controller status updated")
    
    # Test 6: Activity log
    print("Testing activity log...")
    window.add_log_message("Test server started")
    window.add_log_message("Client connected: 192.168.1.100")
    window.add_log_message("Virtual controller 1 activated")
    window.add_log_message("Input data received from controller 1")
    print("Activity log messages added")
    
    # Test 7: Controller count update (internal method)
    print("Testing controller count updates...")
    initial_card_count = len(window.virtual_controller_cards)
    print(f"Initial virtual controller cards: {initial_card_count}")
    
    # This would normally be called internally when settings change
    # window._update_controller_count(6)
    # For now, we'll just check the current count
    print(f"Current virtual controller cards: {len(window.virtual_controller_cards)}")
    
    # Show window briefly
    window.show()
    print("ReceiverWindow displayed successfully")
    
    # Verify results
    print("\n=== RECEIVER WINDOW TEST RESULTS ===")
    print(f"Signals triggered: {signals_triggered}")
    print(f"Expected: start_server, stop_server signals")
    print(f"Server toggle working: {'start_server' in signals_triggered and 'stop_server' in signals_triggered}")
    print(f"Button text changes: {initial_text} -> {after_start_text} -> {after_stop_text}")
    
    # Auto-close
    def close_window():
        print("Closing receiver test window...")
        window.close()
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(close_window)
    timer.start(3000)  # 3 seconds for receiver (more content to show)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_receiver_window_functionality())