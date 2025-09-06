#!/usr/bin/env python3
"""Test BackToMain button functionality."""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from input_link.gui.application import InputLinkApplication

def test_back_to_main_buttons():
    """Test BackToMain button functionality."""
    print("Testing BackToMain button functionality...")
    
    app = InputLinkApplication([])
    
    # Simulate navigation flow
    navigation_log = []
    
    # Override show methods to log navigation
    original_show_main = app._show_main_window
    original_show_sender = app._show_sender_window  
    original_show_receiver = app._show_receiver_window
    
    def log_show_main():
        navigation_log.append("show_main_window")
        print("Navigation: Showing Main Window")
        original_show_main()
        
    def log_show_sender():
        navigation_log.append("show_sender_window")
        print("Navigation: Showing Sender Window")
        original_show_sender()
        
    def log_show_receiver():
        navigation_log.append("show_receiver_window")
        print("Navigation: Showing Receiver Window")
        original_show_receiver()
    
    app._show_main_window = log_show_main
    app._show_sender_window = log_show_sender
    app._show_receiver_window = log_show_receiver
    
    # Test navigation sequence
    print("\n=== Testing Navigation Sequence ===")
    
    # 1. Start at main window (already there)
    print("1. Starting at Main Window")
    current_widget = app.stacked_widget.currentWidget()
    print(f"Current widget: {type(current_widget).__name__}")
    
    # 2. Navigate to Sender Window (simulate button click)
    print("2. Navigating to Sender Window...")
    app.main_window.start_sender.emit()
    current_widget = app.stacked_widget.currentWidget()
    print(f"Current widget after sender signal: {type(current_widget).__name__}")
    
    # 3. Test Sender Back button
    print("3. Testing Sender Back button...")
    app.sender_window.back_btn.click()
    current_widget = app.stacked_widget.currentWidget()
    print(f"Current widget after sender back: {type(current_widget).__name__}")
    
    # 4. Navigate to Receiver Window (simulate button click)
    print("4. Navigating to Receiver Window...")
    app.main_window.start_receiver.emit()
    current_widget = app.stacked_widget.currentWidget()
    print(f"Current widget after receiver signal: {type(current_widget).__name__}")
    
    # 5. Test Receiver Back button
    print("5. Testing Receiver Back button...")
    app.receiver_window.back_btn.click()
    current_widget = app.stacked_widget.currentWidget()
    print(f"Current widget after receiver back: {type(current_widget).__name__}")
    
    # Show results
    print(f"\n=== Navigation Log ===")
    for i, action in enumerate(navigation_log, 1):
        print(f"{i}. {action}")
    
    print(f"\n=== Test Results ===")
    expected_sequence = [
        "show_sender_window",  # Main -> Sender
        "show_main_window",    # Sender -> Main (back button)
        "show_receiver_window", # Main -> Receiver
        "show_main_window"     # Receiver -> Main (back button)
    ]
    
    print(f"Expected: {expected_sequence}")
    print(f"Actual:   {navigation_log}")
    print(f"BackToMain buttons working: {navigation_log == expected_sequence}")
    
    # Auto-close
    def close_app():
        print("\nClosing test application...")
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(close_app)
    timer.start(2000)  # 2 seconds
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_back_to_main_buttons())