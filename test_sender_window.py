#!/usr/bin/env python3
"""Test SenderWindow functionality."""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from input_link.gui.sender_window import SenderWindow
from input_link.core.controller_manager import DetectedController
from input_link.models.controller import InputMethod

def test_sender_window_functionality():
    """Test SenderWindow specific functionality."""
    print("Starting SenderWindow functionality test...")
    
    app = QApplication([])
    window = SenderWindow()
    
    # Test 1: Signal connections
    signals_triggered = []
    
    def on_start_capture():
        signals_triggered.append("start_capture")
        print("START_CAPTURE signal triggered")
        
    def on_stop_capture():
        signals_triggered.append("stop_capture")
        print("STOP_CAPTURE signal triggered")
        
    def on_controller_enabled(controller_id, enabled):
        signals_triggered.append(f"controller_enabled_{controller_id}_{enabled}")
        print(f"CONTROLLER_ENABLED signal: {controller_id} = {enabled}")
    
    window.start_capture.connect(on_start_capture)
    window.stop_capture.connect(on_stop_capture)
    window.controller_enabled.connect(on_controller_enabled)
    
    # Test 2: Button functionality
    print("Testing button functionality...")
    
    # Test scan button
    window.scan_btn.click()
    print("Scan button clicked")
    
    # Test capture toggle
    print("Testing capture toggle...")
    initial_text = window.start_btn.text()
    print(f"Initial button text: {initial_text}")
    
    window.start_btn.click()  # Should start capture
    after_start_text = window.start_btn.text()
    print(f"After start click: {after_start_text}")
    
    window.start_btn.click()  # Should stop capture
    after_stop_text = window.start_btn.text()
    print(f"After stop click: {after_stop_text}")
    
    # Test 3: Settings functionality
    print("Testing settings...")
    window.host_combo.setCurrentText("192.168.1.50")
    window.port_spin.setValue(9000)
    window.rate_spin.setValue(90)
    
    print(f"Host setting: {window.host_combo.currentText()}")
    print(f"Port setting: {window.port_spin.value()}")
    print(f"Rate setting: {window.rate_spin.value()}")
    
    # Test 4: Controller list updates
    print("Testing controller updates...")
    
    # Create mock controllers
    mock_controllers = [
        DetectedController(
            pygame_id=0,
            device_id=0,
            name="Xbox Controller",
            guid="12345",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            assigned_number=1,
            preferred_input_method=InputMethod.XINPUT
        ),
        DetectedController(
            pygame_id=1,
            device_id=1,
            name="PS4 Controller", 
            guid="67890",
            num_axes=6,
            num_buttons=16,
            num_hats=1,
            assigned_number=2,
            preferred_input_method=InputMethod.DINPUT
        )
    ]
    
    # Test with controllers
    window.update_controllers(mock_controllers)
    print(f"Controller count after update: {len(window.controller_cards)}")
    print(f"Controller count label: {window.controller_count_label.text()}")
    
    # Test without controllers
    window.update_controllers([])
    print(f"Controller count after clearing: {len(window.controller_cards)}")
    print(f"No controllers label visible: {window.no_controllers_label.isVisible()}")
    
    # Test 5: Connection status update
    print("Testing connection status...")
    window.update_connection_status("Connected to 192.168.1.50:8765", "#34C759")
    print("Connection status updated")
    
    # Show window briefly
    window.show()
    print("SenderWindow displayed successfully")
    
    # Verify results
    print("\n=== SENDER WINDOW TEST RESULTS ===")
    print(f"Signals triggered: {signals_triggered}")
    print(f"Expected: start_capture, stop_capture signals")
    print(f"Capture toggle working: {'start_capture' in signals_triggered and 'stop_capture' in signals_triggered}")
    print(f"Button text changes: {initial_text} -> {after_start_text} -> {after_stop_text}")
    
    # Auto-close
    def close_window():
        print("Closing sender test window...")
        window.close()
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(close_window)
    timer.start(2000)  # 2 seconds
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_sender_window_functionality())