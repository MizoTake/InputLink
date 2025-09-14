#!/usr/bin/env python3
"""Trigger GUI scan via automation to test signal flow."""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer

# Add src to path
sys.path.insert(0, '../src')

def trigger_scan_in_gui():
    """Connect to existing GUI and trigger scan."""
    print("=== Connecting to existing GUI instance ===")

    app = QApplication.instance()
    if app is None:
        print("No QApplication instance found - GUI must be running")
        return

    print(f"Found QApplication: {app}")

    # Find all top-level windows
    windows = app.topLevelWindows()
    print(f"Found {len(windows)} top-level windows")

    for window in windows:
        print(f"Window: {window} - Visible: {window.isVisible()}")

    # Find all widgets
    widgets = app.allWidgets()
    sender_windows = [w for w in widgets if w.__class__.__name__ == 'SenderWindow']

    print(f"Found {len(sender_windows)} SenderWindow instances")

    if sender_windows:
        sender_window = sender_windows[0]
        print(f"SenderWindow: {sender_window}")

        # Check if we can access the scan button
        if hasattr(sender_window, 'scan_btn'):
            scan_btn = sender_window.scan_btn
            print(f"Scan button found: {scan_btn}")
            print(f"Scan button text: '{scan_btn.text()}'")
            print(f"Scan button enabled: {scan_btn.isEnabled()}")
            print(f"Scan button visible: {scan_btn.isVisible()}")

            # Navigate to sender window first if it's in a stacked widget
            parent_widgets = app.allWidgets()
            stacked_widgets = [w for w in parent_widgets if w.__class__.__name__ == 'QStackedWidget']

            if stacked_widgets:
                stack = stacked_widgets[0]
                print(f"Found stack widget: {stack}")

                # Find sender window index
                for i in range(stack.count()):
                    widget = stack.widget(i)
                    if widget.__class__.__name__ == 'SenderWindow':
                        print(f"Setting current widget to SenderWindow at index {i}")
                        stack.setCurrentIndex(i)
                        app.processEvents()
                        time.sleep(0.1)
                        break

            # Now click the scan button
            print("\n=== TRIGGERING SCAN BUTTON CLICK ===")
            scan_btn.click()
            app.processEvents()

            print("Scan button clicked - check main GUI output for debug traces")

        else:
            print("No scan_btn attribute found")

    else:
        print("No SenderWindow found")

if __name__ == "__main__":
    trigger_scan_in_gui()