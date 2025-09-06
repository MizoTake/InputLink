#!/usr/bin/env python3
"""Test GUI interactions and functionality."""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from input_link.gui.main_window import MainWindow

def test_main_window_signals():
    """Test MainWindow signal connections."""
    print("Creating QApplication...")
    app = QApplication([])
    
    print("Creating MainWindow...")
    window = MainWindow()
    
    # Test signal connections
    def on_start_sender():
        print("✅ Start Sender signal triggered!")
        
    def on_start_receiver():
        print("✅ Start Receiver signal triggered!")
        
    def on_stop_services():
        print("✅ Stop Services signal triggered!")
    
    # Connect test slots
    window.start_sender.connect(on_start_sender)
    window.start_receiver.connect(on_start_receiver)
    window.stop_services.connect(on_stop_services)
    
    print("Testing signal connections...")
    
    # Test status updates
    print("Testing status updates...")
    window.update_sender_status("Connected", "#34C759")
    window.update_receiver_status("Listening", "#34C759")
    
    # Test log messages
    print("Testing log messages...")
    window.add_log_message("Test log message 1")
    window.add_log_message("Test log message 2")
    
    # Test button clicks programmatically
    print("Testing button clicks...")
    window.start_sender_btn.click()  # Should trigger on_start_sender
    window.start_receiver_btn.click()  # Should trigger on_start_receiver  
    window.stop_btn.click()  # Should trigger on_stop_services
    
    # Show window for visual confirmation
    window.show()
    
    # Auto-close after 3 seconds for automated testing
    def close_window():
        print("Auto-closing window...")
        window.close()
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(close_window)
    timer.start(3000)  # 3 seconds
    
    print("MainWindow displayed for 3 seconds...")
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_main_window_signals())