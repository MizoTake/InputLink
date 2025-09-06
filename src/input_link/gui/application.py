"""GUI Application entry point for Input Link."""

from __future__ import annotations

import asyncio
import sys
from typing import Dict, Optional

from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QStackedWidget

from input_link.apps.receiver import ReceiverApp
from input_link.apps.sender import SenderApp
from input_link.core import ControllerManager
from input_link.core.logging_system import setup_application_logging
from input_link.gui.main_window import MainWindow
from input_link.gui.receiver_window import ReceiverWindow
from input_link.gui.sender_window import SenderWindow


class AsyncWorker(QThread):
    """Worker thread for async operations."""

    # Signals
    controller_detected = Signal(list)  # List[DetectedController]
    sender_status_changed = Signal(str, str)  # status, color
    receiver_status_changed = Signal(str, str) # status, color
    log_message = Signal(str)

    def __init__(self):
        super().__init__()
        self.sender_app: Optional[SenderApp] = None
        self.receiver_app: Optional[ReceiverApp] = None
        self.controller_manager: Optional[ControllerManager] = None
        self._stop_requested = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Initialize GUI logging
        self.logger = setup_application_logging(
            app_name="gui",
            config=None,
            verbose=False,
            log_callback=None,
        )

    def run(self):
        """Run the async event loop in this thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_forever()
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def stop(self):
        """Stop the worker thread with proper cleanup."""
        self._stop_requested = True
        
        # Stop applications gracefully
        try:
            if self.sender_app:
                self.stop_sender()
        except Exception as e:
            print(f"Error stopping sender app: {e}")
        
        try:
            if self.receiver_app:
                self.stop_receiver()
        except Exception as e:
            print(f"Error stopping receiver app: {e}")

        # Stop event loop
        try:
            if self.loop and not self.loop.is_closed():
                self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception as e:
            print(f"Error stopping event loop: {e}")
        
        # Cleanup worker thread
        try:
            self.quit()
            self.wait(5000)  # Wait up to 5 seconds
            if self.isRunning():
                print("Force terminating worker thread")
                self.terminate()
        except Exception as e:
            print(f"Error during worker cleanup: {e}")

    def _sender_log_callback(self, level: str, message: str):
        self.log_message.emit(f"[Sender] {message}")

    def _sender_status_callback(self, status: str):
        STATUS_MAP = {
            "connecting": ("Connecting...", "#FF9500"),
            "connected": ("Connected", "#34C759"),
            "disconnected": ("Disconnected", "#8E8E93"),
            "reconnecting": ("Reconnecting...", "#FF9500"),
            "failed": ("Connection Failed", "#FF3B30"),
            "stopped": ("Stopped", "#8E8E93"),
        }
        display_status, color = STATUS_MAP.get(status, ("Unknown", "#8E8E93"))
        self.sender_status_changed.emit(display_status, color)

    def _receiver_log_callback(self, level: str, message: str):
        self.log_message.emit(f"[Receiver] {message}")

    def _receiver_status_callback(self, status: str, data: Dict):
        if status == "listening":
            address = data.get("address", "N/A")
            self.receiver_status_changed.emit(f"Listening on {address}", "#34C759")
        elif status == "stopped":
            self.receiver_status_changed.emit("Stopped", "#8E8E93")
        elif status == "error":
            self.receiver_status_changed.emit("Error", "#FF3B30")
        elif status == "client_connected":
            self.log_message.emit(f"Client connected: {data.get('client_id')}")
        elif status == "client_disconnected":
            self.log_message.emit(f"Client disconnected: {data.get('client_id')}")

    @Slot()
    def scan_controllers(self):
        """Scan for controllers."""
        if not self.controller_manager:
            self.controller_manager = ControllerManager()

        try:
            controllers = self.controller_manager.scan_controllers()
            self.controller_detected.emit(controllers)
            self.logger.info(f"Found {len(controllers)} controllers")
            self.log_message.emit(f"Found {len(controllers)} controllers")
        except Exception as e:
            self.logger.error(f"Controller scan error: {e}")
            self.log_message.emit(f"Controller scan error: {e}")
            self.controller_detected.emit([])

    @Slot()
    def start_sender(self):
        """Start sender application."""
        if self.sender_app and self.sender_app.running:
            self.logger.warning("Sender is already running.")
            self.log_message.emit("Sender is already running.")
            return

        self.sender_app = SenderApp(
            log_callback=self._sender_log_callback,
            status_callback=self._sender_status_callback,
            verbose=False,
        )
        asyncio.run_coroutine_threadsafe(self.sender_app.start(), self.loop)

    @Slot()
    def stop_sender(self):
        """Request to stop the sender application."""
        if not self.sender_app or not self.sender_app.running:
            self.logger.warning("Sender is not running.")
            self.log_message.emit("Sender is not running.")
            return

        if self.loop and self.sender_app:
            asyncio.run_coroutine_threadsafe(self.sender_app.stop(), self.loop)

    @Slot()
    def start_receiver(self):
        """Start receiver application."""
        if self.receiver_app and self.receiver_app.running:
            self.logger.warning("Receiver is already running.")
            self.log_message.emit("Receiver is already running.")
            return

        self.receiver_app = ReceiverApp(
            log_callback=self._receiver_log_callback,
            status_callback=self._receiver_status_callback,
            verbose=False,
        )
        asyncio.run_coroutine_threadsafe(self.receiver_app.start(), self.loop)

    @Slot()
    def stop_receiver(self):
        """Request to stop the receiver application."""
        if not self.receiver_app or not self.receiver_app.running:
            self.logger.warning("Receiver is not running.")
            self.log_message.emit("Receiver is not running.")
            return

        if self.loop and self.receiver_app:
            asyncio.run_coroutine_threadsafe(self.receiver_app.stop(), self.loop)


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
        try:
            print("Setting up UI components...")
            
            # Create stacked widget to manage different windows
            self.stacked_widget = QStackedWidget()
            print("Created QStackedWidget")

            # Create windows
            print("Creating MainWindow...")
            self.main_window = MainWindow()
            print(f"MainWindow created: {self.main_window}")
            
            print("Creating SenderWindow...")
            self.sender_window = SenderWindow()
            print(f"SenderWindow created: {self.sender_window}")
            
            print("Creating ReceiverWindow...")
            self.receiver_window = ReceiverWindow()
            print(f"ReceiverWindow created: {self.receiver_window}")

            # Add windows to stack
            self.stacked_widget.addWidget(self.main_window)
            self.stacked_widget.addWidget(self.sender_window)
            self.stacked_widget.addWidget(self.receiver_window)
            print("Added windows to stack widget")

            # Note: Signal connections are now done after worker setup

            # Show stacked widget with main window
            print("Showing main window...")
            self.stacked_widget.setWindowTitle("Input Link")
            self.stacked_widget.resize(480, 650)  # Set minimum size
            self.stacked_widget.setCurrentWidget(self.main_window)
            self.stacked_widget.show()
            self.stacked_widget.raise_()
            self.stacked_widget.activateWindow()
            
            # Force window to center and bring to front
            screen = QApplication.primaryScreen().geometry()
            window_size = self.stacked_widget.size()
            self.stacked_widget.move(
                (screen.width() - window_size.width()) // 2,
                (screen.height() - window_size.height()) // 2
            )
            
            print(f"Stacked widget geometry: {self.stacked_widget.geometry()}")
            print(f"Stacked widget visible: {self.stacked_widget.isVisible()}")
            print(f"Main window visible: {self.main_window.isVisible()}")
            print("GUI is now running. Press Ctrl+C to close.")
            print("UI setup complete")
            
        except Exception as e:
            print(f"Error during UI setup: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _setup_worker(self):
        """Setup the async worker thread."""
        self.async_worker = AsyncWorker()

        # Connect worker signals
        self.async_worker.controller_detected.connect(self._on_controllers_detected)
        self.async_worker.sender_status_changed.connect(self._on_sender_status_changed)
        self.async_worker.receiver_status_changed.connect(self._on_receiver_status_changed)
        self.async_worker.log_message.connect(self._on_log_message)

        # Start worker
        self.async_worker.start()
        
        # Now connect window signals (after worker is created)
        print("Connecting window signals...")
        self._connect_main_window_signals()
        self._connect_sender_window_signals()
        self._connect_receiver_window_signals()

    def _connect_main_window_signals(self):
        """Connect main window signals."""
        try:
            if self.main_window is None:
                print("Error: MainWindow is None")
                return
                
            if not hasattr(self.main_window, 'start_sender'):
                print("Error: MainWindow missing start_sender signal")
                return
                
            self.main_window.start_sender.connect(self._show_sender_window)
            self.main_window.start_receiver.connect(self._show_receiver_window)
            self.main_window.stop_services.connect(self._stop_all_services)
            print("MainWindow signals connected successfully")
        except Exception as e:
            print(f"Error connecting main window signals: {e}")
            import traceback
            traceback.print_exc()

    def _connect_sender_window_signals(self):
        """Connect sender window signals."""
        try:
            print(f"SenderWindow check: {self.sender_window is not None}")
            print(f"AsyncWorker check: {self.async_worker is not None}")
            print(f"start_capture check: {hasattr(self.sender_window, 'start_capture') if self.sender_window else False}")
            print(f"back_btn check: {hasattr(self.sender_window, 'back_btn') if self.sender_window else False}")
            print(f"scan_btn check: {hasattr(self.sender_window, 'scan_btn') if self.sender_window else False}")
            
            if self.sender_window and self.async_worker:
                # Connect available signals
                if hasattr(self.sender_window, 'start_capture'):
                    self.sender_window.start_capture.connect(self.async_worker.start_sender)
                    print("Connected start_capture signal")
                if hasattr(self.sender_window, 'stop_capture'):
                    self.sender_window.stop_capture.connect(self._stop_sender)
                    print("Connected stop_capture signal")
                if hasattr(self.sender_window, 'back_btn'):
                    self.sender_window.back_btn.clicked.connect(self._show_main_window)
                    print("Connected back_btn signal")
                if hasattr(self.sender_window, 'scan_btn'):
                    self.sender_window.scan_btn.clicked.connect(self.async_worker.scan_controllers)
                    print("Connected scan_btn signal")
                print("SenderWindow signals connected successfully")
            else:
                print("Warning: SenderWindow or AsyncWorker not available")
        except Exception as e:
            print(f"Error connecting sender window signals: {e}")
            import traceback
            traceback.print_exc()

    def _connect_receiver_window_signals(self):
        """Connect receiver window signals."""
        try:
            print(f"ReceiverWindow check: {self.receiver_window is not None}")
            print(f"start_server check: {hasattr(self.receiver_window, 'start_server') if self.receiver_window else False}")
            print(f"stop_server check: {hasattr(self.receiver_window, 'stop_server') if self.receiver_window else False}")
            print(f"back_btn check: {hasattr(self.receiver_window, 'back_btn') if self.receiver_window else False}")
            
            if self.receiver_window and self.async_worker:
                # Connect available signals
                if hasattr(self.receiver_window, 'start_server'):
                    self.receiver_window.start_server.connect(self.async_worker.start_receiver)
                    print("Connected start_server signal")
                if hasattr(self.receiver_window, 'stop_server'):
                    self.receiver_window.stop_server.connect(self._stop_receiver)
                    print("Connected stop_server signal")
                if hasattr(self.receiver_window, 'back_btn'):
                    self.receiver_window.back_btn.clicked.connect(self._show_main_window)
                    print("Connected back_btn signal")
                print("ReceiverWindow signals connected successfully")
            else:
                print("Warning: ReceiverWindow or AsyncWorker not available")
        except Exception as e:
            print(f"Error connecting receiver window signals: {e}")
            import traceback
            traceback.print_exc()

    @Slot()
    def _show_main_window(self):
        """Show the main window."""
        self.stacked_widget.setCurrentWidget(self.main_window)

    @Slot()
    def _show_sender_window(self):
        """Show the sender window."""
        self.stacked_widget.setCurrentWidget(self.sender_window)

    @Slot()
    def _show_receiver_window(self):
        """Show the receiver window."""
        self.stacked_widget.setCurrentWidget(self.receiver_window)

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
        if self.async_worker:
            self.async_worker.stop_sender()

    @Slot()
    def _stop_receiver(self):
        """Stop receiver service."""
        if self.async_worker:
            self.async_worker.stop_receiver()

    @Slot(list)
    def _on_controllers_detected(self, controllers):
        """Handle controller detection results."""
        self.sender_window.update_controllers(controllers)

    @Slot(str, str)
    def _on_sender_status_changed(self, status, color):
        """Handle sender status changes."""
        self.main_window.update_sender_status(status, color)
        self.sender_window.update_connection_status(status, color)

    @Slot(str, str)
    def _on_receiver_status_changed(self, status, color):
        """Handle receiver status changes."""
        self.main_window.update_receiver_status(status, color)
        self.receiver_window.update_server_status(status, color)

    @Slot(str)
    def _on_log_message(self, message):
        """Handle log messages."""
        self.main_window.add_log_message(message)
        self.receiver_window.add_log_message(message)

    def closeEvent(self, event):
        """Handle application close event with proper cleanup."""
        try:
            print("Application close requested...")
            
            # Stop async worker first
            if hasattr(self, 'async_worker') and self.async_worker:
                print("Stopping async worker...")
                try:
                    self.async_worker.stop()
                    # Give worker time to cleanup
                    self.async_worker.wait(3000)  # Wait up to 3 seconds
                except Exception as e:
                    print(f"Error stopping async worker: {e}")
            
            # Close stacked widget if it exists
            if hasattr(self, 'stacked_widget') and self.stacked_widget:
                print("Closing stacked widget...")
                try:
                    self.stacked_widget.close()
                except Exception as e:
                    print(f"Error closing stacked widget: {e}")
            
            # Close individual windows
            for window_name in ['main_window', 'sender_window', 'receiver_window']:
                if hasattr(self, window_name):
                    window = getattr(self, window_name)
                    if window and not window.isHidden():
                        try:
                            window.close()
                        except Exception as e:
                            print(f"Error closing {window_name}: {e}")
            
            print("Application cleanup complete")
            event.accept()
        except Exception as e:
            print(f"Error during application close: {e}")
            import traceback
            traceback.print_exc()
            event.accept()  # Force close even on error


def run_gui_application():
    """Run the GUI application."""
    logger = None
    try:
        # Initialize early logging
        logger = setup_application_logging(
            app_name="gui_main",
            config=None,
            verbose=False,
            log_callback=None,
        )
        
        logger.info("Starting Input Link GUI application...")
        app = InputLinkApplication(sys.argv)
        logger.info("Application initialized successfully")
        
        return app.exec()
    except ImportError as e:
        error_msg = f"Import error - missing dependencies: {e}"
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg)
        print("Please install GUI dependencies: pip install PySide6")
        return 1
    except KeyboardInterrupt:
        interrupt_msg = "Application interrupted by user"
        if logger:
            logger.info(interrupt_msg)
        else:
            print(f"\\n{interrupt_msg}")
        return 0
    except Exception as e:
        error_msg = f"Application error: {e}"
        if logger:
            logger.error(error_msg)
            logger.exception("Full traceback:")
        else:
            print(error_msg)
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_gui_application())
