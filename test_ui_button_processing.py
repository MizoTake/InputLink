#!/usr/bin/env python3
"""Comprehensive UI button processing test."""

import sys
import os
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from input_link.gui.application import InputLinkApplication

def test_ui_button_processing():
    """Test all UI button processing functionality."""
    print("Starting comprehensive UI button processing test...")
    
    app = InputLinkApplication([])
    
    # Mock the async worker to avoid actual service operations
    original_start_sender = app.async_worker.start_sender
    original_stop_sender = app.async_worker.stop_sender
    original_start_receiver = app.async_worker.start_receiver
    original_stop_receiver = app.async_worker.stop_receiver
    original_scan_controllers = app.async_worker.scan_controllers
    
    # Track button interactions
    button_interactions = []
    
    # Mock async worker methods
    def mock_start_sender():
        button_interactions.append("start_sender_called")
        print("Mock: Start Sender called")
    
    def mock_stop_sender():
        button_interactions.append("stop_sender_called") 
        print("Mock: Stop Sender called")
    
    def mock_start_receiver():
        button_interactions.append("start_receiver_called")
        print("Mock: Start Receiver called")
    
    def mock_stop_receiver():
        button_interactions.append("stop_receiver_called")
        print("Mock: Stop Receiver called")
        
    def mock_scan_controllers():
        button_interactions.append("scan_controllers_called")
        print("Mock: Scan Controllers called")
        # Simulate controller detection
        from input_link.core.controller_manager import DetectedController
        mock_controllers = [
            DetectedController(
                joystick_id=0,
                name="Test Xbox Controller",
                guid="test-guid-1",
                assigned_number=1,
                preferred_input_method="XINPUT"
            ),
            DetectedController(
                joystick_id=1, 
                name="Test PS4 Controller",
                guid="test-guid-2",
                assigned_number=2,
                preferred_input_method="DINPUT"
            )
        ]
        app.async_worker.controller_detected.emit(mock_controllers)
    
    app.async_worker.start_sender = mock_start_sender
    app.async_worker.stop_sender = mock_stop_sender
    app.async_worker.start_receiver = mock_start_receiver
    app.async_worker.stop_receiver = mock_stop_receiver
    app.async_worker.scan_controllers = mock_scan_controllers
    
    # Test sequence
    test_results = []
    
    print("\n=== TESTING MAIN WINDOW BUTTONS ===")
    
    # 1. Test Main Window - Start Sender button
    print("1. Testing Main Window Start Sender button...")
    app.main_window.start_sender_btn.click()
    current_window = app.stacked_widget.currentWidget()
    if current_window == app.sender_window:
        test_results.append("[PASS] Main->Sender navigation works")
        print("[PASS] Navigation to Sender window successful")
    else:
        test_results.append("[FAIL] Main->Sender navigation failed")
        print("[FAIL] Navigation to Sender window failed")
    
    # 2. Test Main Window - Start Receiver button
    print("2. Testing Main Window Start Receiver button...")
    app._show_main_window()  # Go back to main
    app.main_window.start_receiver_btn.click()
    current_window = app.stacked_widget.currentWidget()
    if current_window == app.receiver_window:
        test_results.append("[PASS] Main->Receiver navigation works")
        print("[PASS] Navigation to Receiver window successful")
    else:
        test_results.append("[FAIL] Main->Receiver navigation failed")
        print("[FAIL] Navigation to Receiver window failed")
    
    print("\n=== TESTING SENDER WINDOW BUTTONS ===")
    app.stacked_widget.setCurrentWidget(app.sender_window)
    
    # 3. Test Sender Window - Scan button
    print("3. Testing Sender Window Scan button...")
    initial_interactions = len(button_interactions)
    app.sender_window.scan_btn.click()
    if "scan_controllers_called" in button_interactions[initial_interactions:]:
        test_results.append("[PASS] Sender scan button works")
        print("[PASS] Scan controllers functionality triggered")
    else:
        test_results.append("[FAIL] Sender scan button failed")
        print("[FAIL] Scan controllers functionality not triggered")
    
    # 4. Test Sender Window - Start/Stop Capture toggle
    print("4. Testing Sender Window Start Capture button...")
    initial_text = app.sender_window.start_btn.text()
    print(f"Initial button text: {initial_text}")
    
    # First click - should start capture
    initial_interactions = len(button_interactions)
    app.sender_window.start_btn.click()
    after_start_text = app.sender_window.start_btn.text()
    if "start_capture" in button_interactions[initial_interactions:] or after_start_text != initial_text:
        test_results.append("[PASS] Sender start capture works")
        print(f"[PASS] Start capture triggered - button text: {after_start_text}")
    else:
        test_results.append("[FAIL] Sender start capture failed")
        print("[FAIL] Start capture not triggered")
    
    # Second click - should stop capture
    initial_interactions = len(button_interactions)
    app.sender_window.start_btn.click()
    after_stop_text = app.sender_window.start_btn.text()
    if "stop_capture" in button_interactions[initial_interactions:] or after_stop_text != after_start_text:
        test_results.append("[PASS] Sender stop capture works")
        print(f"[PASS] Stop capture triggered - button text: {after_stop_text}")
    else:
        test_results.append("[FAIL] Sender stop capture failed") 
        print("[FAIL] Stop capture not triggered")
    
    # 5. Test Sender Window - Back button
    print("5. Testing Sender Window Back button...")
    app.sender_window.back_btn.click()
    current_window = app.stacked_widget.currentWidget()
    if current_window == app.main_window:
        test_results.append("[PASS] Sender back navigation works")
        print("[PASS] Back to Main window successful")
    else:
        test_results.append("[FAIL] Sender back navigation failed")
        print("[FAIL] Back to Main window failed")
    
    print("\n=== TESTING RECEIVER WINDOW BUTTONS ===")
    app.stacked_widget.setCurrentWidget(app.receiver_window)
    
    # 6. Test Receiver Window - Start/Stop Server toggle
    print("6. Testing Receiver Window Start Server button...")
    initial_text = app.receiver_window.start_btn.text()
    print(f"Initial button text: {initial_text}")
    
    # First click - should start server
    initial_interactions = len(button_interactions)
    app.receiver_window.start_btn.click()
    after_start_text = app.receiver_window.start_btn.text()
    if "start_server" in button_interactions[initial_interactions:] or after_start_text != initial_text:
        test_results.append("[PASS] Receiver start server works")
        print(f"[PASS] Start server triggered - button text: {after_start_text}")
    else:
        test_results.append("[FAIL] Receiver start server failed")
        print("[FAIL] Start server not triggered")
    
    # Second click - should stop server
    initial_interactions = len(button_interactions)
    app.receiver_window.start_btn.click()
    after_stop_text = app.receiver_window.start_btn.text()
    if "stop_server" in button_interactions[initial_interactions:] or after_stop_text != after_start_text:
        test_results.append("[PASS] Receiver stop server works")
        print(f"[PASS] Stop server triggered - button text: {after_stop_text}")
    else:
        test_results.append("[FAIL] Receiver stop server failed")
        print("[FAIL] Stop server not triggered")
    
    # 7. Test Receiver Window - Settings changes
    print("7. Testing Receiver Window Settings...")
    original_port = app.receiver_window.port_spin.value()
    original_max_controllers = app.receiver_window.max_controllers_spin.value()
    original_auto_create = app.receiver_window.auto_create_checkbox.isChecked()
    
    # Change settings
    app.receiver_window.port_spin.setValue(9999)
    app.receiver_window.max_controllers_spin.setValue(6)
    app.receiver_window.auto_create_checkbox.setChecked(not original_auto_create)
    
    new_port = app.receiver_window.port_spin.value()
    new_max_controllers = app.receiver_window.max_controllers_spin.value()
    new_auto_create = app.receiver_window.auto_create_checkbox.isChecked()
    
    if (new_port == 9999 and new_max_controllers == 6 and new_auto_create != original_auto_create):
        test_results.append("[PASS] Receiver settings modification works")
        print("[PASS] Settings can be modified successfully")
    else:
        test_results.append("[FAIL] Receiver settings modification failed")
        print("[FAIL] Settings modification failed")
    
    # 8. Test Receiver Window - Back button
    print("8. Testing Receiver Window Back button...")
    app.receiver_window.back_btn.click()
    current_window = app.stacked_widget.currentWidget()
    if current_window == app.main_window:
        test_results.append("[PASS] Receiver back navigation works")
        print("[PASS] Back to Main window successful")
    else:
        test_results.append("[FAIL] Receiver back navigation failed")
        print("[FAIL] Back to Main window failed")
    
    # 9. Test UI Layout and Overlapping
    print("\n=== TESTING UI LAYOUT AND SIZING ===")
    
    # Check window sizes
    main_size = app.main_window.size()
    sender_size = app.sender_window.size()
    receiver_size = app.receiver_window.size()
    stack_size = app.stacked_widget.size()
    
    print(f"Main Window size: {main_size.width()} x {main_size.height()}")
    print(f"Sender Window size: {sender_size.width()} x {sender_size.height()}")
    print(f"Receiver Window size: {receiver_size.width()} x {receiver_size.height()}")
    print(f"Stacked Widget size: {stack_size.width()} x {stack_size.height()}")
    
    # Check if windows fit properly in stack
    layout_issues = []
    if sender_size.width() > stack_size.width() or sender_size.height() > stack_size.height():
        layout_issues.append("Sender window too large for container")
    if receiver_size.width() > stack_size.width() or receiver_size.height() > stack_size.height():
        layout_issues.append("Receiver window too large for container")
    
    if layout_issues:
        test_results.extend([f"[FAIL] {issue}" for issue in layout_issues])
        for issue in layout_issues:
            print(f"[FAIL] Layout issue: {issue}")
    else:
        test_results.append("[PASS] UI layout sizing appropriate")
        print("[PASS] All windows fit properly in container")
    
    # Print final results
    print(f"\n=== FINAL TEST RESULTS ===")
    print(f"Button interactions captured: {button_interactions}")
    print(f"Total tests: {len(test_results)}")
    
    passed = len([r for r in test_results if r.startswith("[PASS]")])
    failed = len([r for r in test_results if r.startswith("[FAIL]")])
    
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/len(test_results)*100:.1f}%")
    
    for result in test_results:
        print(result)
    
    # Auto-close
    def close_app():
        print("\nClosing UI test application...")
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(close_app)
    timer.start(3000)  # 3 seconds
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_ui_button_processing())