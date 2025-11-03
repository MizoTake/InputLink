"""Test script to verify QTimer thread fix for preview polling.

This script simulates the fix to ensure QTimer operations happen in the correct thread.
"""

import sys
from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot, QCoreApplication
from PySide6.QtWidgets import QApplication


class WorkerThread(QThread):
    """Simulates AsyncWorker thread."""

    # Signals for cross-thread communication
    start_timer_requested = Signal()
    stop_timer_requested = Signal()

    def __init__(self):
        super().__init__()
        self._timer = None

    def request_start_timer(self):
        """Request timer start from main thread (NEW APPROACH)."""
        print(f"[Worker Thread {self.currentThread()}] Emitting start_timer_requested signal")
        self.start_timer_requested.emit()

    def request_stop_timer(self):
        """Request timer stop from main thread (NEW APPROACH)."""
        print(f"[Worker Thread {self.currentThread()}] Emitting stop_timer_requested signal")
        self.stop_timer_requested.emit()


class MainWindow(QObject):
    """Simulates main GUI application."""

    def __init__(self):
        super().__init__()
        self.worker = WorkerThread()
        self.timer = None

        # Connect signals to main thread slots
        self.worker.start_timer_requested.connect(self._on_start_timer_requested)
        self.worker.stop_timer_requested.connect(self._on_stop_timer_requested)

        self.worker.start()

    @Slot()
    def _on_start_timer_requested(self):
        """Handle timer start in main thread."""
        print(f"[Main Thread {QThread.currentThread()}] Starting timer in main thread")

        if self.timer:
            self.timer.stop()

        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.start(100)  # 100ms interval

        print(f"[Main Thread] Timer created successfully")

    @Slot()
    def _on_stop_timer_requested(self):
        """Handle timer stop in main thread."""
        print(f"[Main Thread {QThread.currentThread()}] Stopping timer in main thread")

        if self.timer:
            self.timer.stop()
            print(f"[Main Thread] Timer stopped successfully")
        else:
            print(f"[Main Thread] No timer to stop")

    @Slot()
    def _on_timer_tick(self):
        """Handle timer tick."""
        print(f"[Main Thread] Timer tick - preview polling would happen here")

    def test_workflow(self):
        """Test the complete workflow."""
        print("\n=== Testing Timer Thread Fix ===\n")

        # Simulate sender stop -> start preview
        print("1. Simulating Sender Stop (start preview polling)...")
        self.worker.request_start_timer()

        # Let timer run for a bit
        QTimer.singleShot(500, self._test_stop_timer)

    def _test_stop_timer(self):
        """Test stopping the timer."""
        print("\n2. Simulating Sender Start (stop preview polling)...")
        self.worker.request_stop_timer()

        # Quit after verification
        QTimer.singleShot(200, self._finish_test)

    def _finish_test(self):
        """Finish the test."""
        print("\n=== Test Complete - No Qt errors should appear above ===\n")
        QCoreApplication.quit()


if __name__ == "__main__":
    print("Testing QTimer thread fix for preview polling...")
    print("Expected: All timer operations happen in main thread")
    print("Expected: No 'QObject::killTimer' or thread warnings\n")

    app = QApplication(sys.argv)
    window = MainWindow()

    # Start test after event loop begins
    QTimer.singleShot(100, window.test_workflow)

    sys.exit(app.exec())
