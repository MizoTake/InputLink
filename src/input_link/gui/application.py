"""GUI Application entry point for Input Link."""

import sys
import asyncio
import threading
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox, QStackedWidget
from PySide6.QtCore import QObject, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QIcon, QFont

from .main_window import MainWindow
from .sender_window import SenderWindow
from .receiver_window import ReceiverWindow
from ..apps.sender import SenderApp
from ..apps.receiver import ReceiverApp
from ..core import ControllerManager
from ..core.controller_manager import DetectedController
from ..models import ConfigModel


class AsyncWorker(QThread):
    """Worker thread for async operations."""
    
    # Signals
    controller_detected = Signal(list)  # List[DetectedController]
    connection_status_changed = Signal(str, str)  # status, color
    log_message = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.sender_app: Optional[SenderApp] = None
        self.receiver_app: Optional[ReceiverApp] = None
        self.controller_manager: Optional[ControllerManager] = None
        self._stop_requested = False
        
    def run(self):
        """Run the async event loop in this thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._async_main())
        except Exception as e:
            self.log_message.emit(f"Error in async worker: {e}")
        finally:
            self.loop.close()
            
    async def _async_main(self):
        """Main async function."""
        while not self._stop_requested:
            await asyncio.sleep(0.1)
            
    def stop(self):
        """Stop the worker thread."""
        self._stop_requested = True
        if hasattr(self, 'loop'):
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.quit()
        self.wait()
        
    @Slot()
    def scan_controllers(self):
        """Scan for controllers."""
        if not self.controller_manager:
            self.controller_manager = ControllerManager()
            
        try:
            controllers = self.controller_manager.scan_controllers()
            self.controller_detected.emit(controllers)
            self.log_message.emit(f"Found {len(controllers)} controllers")
        except Exception as e:
            self.log_message.emit(f"Controller scan error: {e}")
            self.controller_detected.emit([])
            
    @Slot()
    def start_sender(self):
        """Start sender application."""
        try:
            # This would be implemented to start the actual sender
            self.connection_status_changed.emit("Connecting...", "#FF9500")
            self.log_message.emit("Starting sender...")
            
            # Simulate connection process
            QTimer.singleShot(2000, lambda: self.connection_status_changed.emit("Connected", "#34C759"))
            QTimer.singleShot(2000, lambda: self.log_message.emit("Sender connected successfully"))
        except Exception as e:
            self.log_message.emit(f"Failed to start sender: {e}")
            self.connection_status_changed.emit("Connection Failed", "#FF3B30")
            
    @Slot()
    def start_receiver(self):
        """Start receiver application."""
        try:
            # This would be implemented to start the actual receiver
            self.connection_status_changed.emit("Starting...", "#FF9500")
            self.log_message.emit("Starting receiver server...")
            
            # Simulate server start
            QTimer.singleShot(1500, lambda: self.connection_status_changed.emit("Listening", "#34C759"))
            QTimer.singleShot(1500, lambda: self.log_message.emit("Server started on port 8765"))
        except Exception as e:
            self.log_message.emit(f"Failed to start receiver: {e}")
            self.connection_status_changed.emit("Failed", "#FF3B30")


class InputLinkApplication(QApplication):
    """Main GUI application for Input Link."""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Application setup
        self.setApplicationName("Input Link")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Input Link Team")
        
        # Set application font
        font = QFont()
        font.setFamily("-apple-system")
        font.setPointSize(12)
        self.setFont(font)
        
        # Initialize components
        self.main_window: Optional[MainWindow] = None
        self.sender_window: Optional[SenderWindow] = None
        self.receiver_window: Optional[ReceiverWindow] = None
        self.stacked_widget: Optional[QStackedWidget] = None
        self.async_worker: Optional[AsyncWorker] = None
        
        self._setup_ui()
        self._setup_worker()
        
    def _setup_ui(self):
        """Setup the main UI components."""
        # Create stacked widget to manage different windows
        self.stacked_widget = QStackedWidget()
        
        # Create windows
        self.main_window = MainWindow()
        self.sender_window = SenderWindow()
        self.receiver_window = ReceiverWindow()
        
        # Add windows to stack
        self.stacked_widget.addWidget(self.main_window)
        self.stacked_widget.addWidget(self.sender_window)
        self.stacked_widget.addWidget(self.receiver_window)
        
        # Connect signals
        self._connect_main_window_signals()
        self._connect_sender_window_signals()
        self._connect_receiver_window_signals()
        
        # Show main window
        self.main_window.show()
        
    def _setup_worker(self):
        """Setup the async worker thread."""
        self.async_worker = AsyncWorker()
        
        # Connect worker signals
        self.async_worker.controller_detected.connect(self._on_controllers_detected)
        self.async_worker.connection_status_changed.connect(self._on_connection_status_changed)
        self.async_worker.log_message.connect(self._on_log_message)
        
        # Start worker
        self.async_worker.start()
        
    def _connect_main_window_signals(self):
        """Connect main window signals."""
        if self.main_window:
            self.main_window.start_sender.connect(self._show_sender_window)
            self.main_window.start_receiver.connect(self._show_receiver_window)
            self.main_window.stop_services.connect(self._stop_all_services)
        
    def _connect_sender_window_signals(self):
        """Connect sender window signals."""
        if self.sender_window and self.async_worker:
            self.sender_window.start_capture.connect(self.async_worker.start_sender)
            self.sender_window.stop_capture.connect(self._stop_sender)
            self.sender_window.back_btn.clicked.connect(self._show_main_window)
            self.sender_window.scan_btn.clicked.connect(self.async_worker.scan_controllers)
        
    def _connect_receiver_window_signals(self):
        """Connect receiver window signals."""
        if self.receiver_window and self.async_worker:
            self.receiver_window.start_server.connect(self.async_worker.start_receiver)
            self.receiver_window.stop_server.connect(self._stop_receiver)
            self.receiver_window.back_btn.clicked.connect(self._show_main_window)
        
    @Slot()
    def _show_main_window(self):
        """Show the main window."""
        self.sender_window.hide()
        self.receiver_window.hide()
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
    @Slot()
    def _show_sender_window(self):
        """Show the sender window."""
        self.main_window.hide()
        self.receiver_window.hide()
        self.sender_window.show()
        self.sender_window.raise_()
        self.sender_window.activateWindow()
        
    @Slot()
    def _show_receiver_window(self):
        """Show the receiver window."""
        self.main_window.hide()
        self.sender_window.hide()
        self.receiver_window.show()
        self.receiver_window.raise_()
        self.receiver_window.activateWindow()
        
    @Slot()
    def _stop_all_services(self):
        """Stop all running services."""
        try:
            self._stop_sender()
            self._stop_receiver()
            self.main_window.add_log_message("All services stopped")
        except Exception as e:
            self.main_window.add_log_message(f"Error stopping services: {e}")
            
    @Slot()
    def _stop_sender(self):
        """Stop sender service."""
        # Implement actual sender stopping logic here
        self.main_window.update_sender_status("Stopped", "#8E8E93")
        self.sender_window.update_connection_status("Disconnected", "#8E8E93")
        
    @Slot()
    def _stop_receiver(self):
        """Stop receiver service."""
        # Implement actual receiver stopping logic here
        self.main_window.update_receiver_status("Stopped", "#8E8E93")
        self.receiver_window.update_server_status("Stopped", "#8E8E93")
        
    @Slot(list)
    def _on_controllers_detected(self, controllers):
        """Handle controller detection results."""
        self.sender_window.update_controllers(controllers)
        
    @Slot(str, str)
    def _on_connection_status_changed(self, status, color):
        """Handle connection status changes."""
        self.main_window.update_sender_status(status, color)
        self.sender_window.update_connection_status(status, color)
        
        if "Server" in status or "Listening" in status:
            self.main_window.update_receiver_status(status, color)
            self.receiver_window.update_server_status(status, color)
            
    @Slot(str)
    def _on_log_message(self, message):
        """Handle log messages."""
        self.main_window.add_log_message(message)
        self.receiver_window.add_log_message(message)
        
    def closeEvent(self, event):
        """Handle application close event."""
        if self.async_worker:
            self.async_worker.stop()
        event.accept()


def run_gui_application():
    """Run the GUI application."""
    app = InputLinkApplication(sys.argv)
    
    try:
        return app.exec()
    except KeyboardInterrupt:
        print("\\nApplication interrupted by user")
        return 0
    except Exception as e:
        print(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_gui_application())