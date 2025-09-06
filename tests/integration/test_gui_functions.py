#!/usr/bin/env python3
"""Test specific GUI functionality."""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from input_link.gui.main_window import MainWindow

def test_main_window_functionality():
    """Test MainWindow specific functionality."""
    print("Starting MainWindow functionality test...")
    
    app = QApplication([])
    window = MainWindow()
    
    # Test 1: Signal connections
    signals_triggered = []
    
    def on_start_sender():
        signals_triggered.append("start_sender")
        print("START_SENDER signal triggered")
        
    def on_start_receiver():
        signals_triggered.append("start_receiver")
        print("START_RECEIVER signal triggered")
        
    def on_stop_services():
        signals_triggered.append("stop_services")
        print("STOP_SERVICES signal triggered")
    
    window.start_sender.connect(on_start_sender)
    window.start_receiver.connect(on_start_receiver)
    window.stop_services.connect(on_stop_services)
    
    # Test 2: Button clicks
    print("Testing button functionality...")
    window.start_sender_btn.click()
    window.start_receiver_btn.click()
    window.stop_btn.click()
    
    # Test 3: Status updates
    print("Testing status updates...")
    window.update_sender_status("Connected", "#34C759")
    print("Sender status updated")
    
    window.update_receiver_status("Listening on 8765", "#34C759") 
    print("Receiver status updated")
    
    # Test 4: Log messages
    print("Testing log functionality...")
    window.add_log_message("Application started")
    window.add_log_message("Controller detected: Xbox Controller")
    window.add_log_message("WebSocket connection established")
    print("Log messages added")
    
    # Test 5: Settings dialog
    print("Testing settings dialog...")
    # We'll override the _show_settings to avoid the actual dialog
    original_show_settings = window._show_settings
    settings_called = False
    
    def mock_show_settings():
        nonlocal settings_called
        settings_called = True
        print("Settings dialog called")
    
    window._show_settings = mock_show_settings
    window.config_btn.click()
    
    # Verify results
    print("\n=== TEST RESULTS ===")
    print(f"Signals triggered: {signals_triggered}")
    print(f"Expected signals: ['start_sender', 'start_receiver', 'stop_services']")
    print(f"All signals working: {len(signals_triggered) == 3}")
    print(f"Settings dialog called: {settings_called}")
    
    # Show window briefly
    window.show()
    print("MainWindow displayed successfully")
    
    # Auto-close
    def close_window():
        print("Closing test window...")
        window.close()
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(close_window)
    timer.start(2000)  # 2 seconds
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_main_window_functionality())