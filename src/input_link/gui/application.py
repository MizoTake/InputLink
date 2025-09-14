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

    # Map sender status to display text and colors (kept identical)
    STATUS_MAP = {
        "connecting": ("Connecting...", "#FF9500"),
        "connected": ("Connected", "#34C759"),
        "disconnected": ("Disconnected", "#8E8E93"),
        "reconnecting": ("Reconnecting...", "#FF9500"),
        "failed": ("Connection Failed", "#FF3B30"),
        "stopped": ("Stopped", "#8E8E93"),
    }

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
        # Runtime settings captured from UI
        self.sender_settings: Dict = {
            "host": "127.0.0.1",
            "port": 8765,
            "polling_rate": 60,
            "controllers": {},  # controller_id -> {enabled: bool, number: int}
        }
        self.receiver_settings: Dict = {
            "host": "0.0.0.0",
            "port": 8765,
            "max_controllers": 4,
            "auto_create": True,
        }

    def run(self):
        """Run the async event loop in this thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()

    async def _async_stop(self):
        """Async shutdown: stop apps then the loop."""
        if self.sender_app and self.sender_app.running:
            await self.sender_app.stop()
        if self.receiver_app and self.receiver_app.running:
            await self.receiver_app.stop()
        if self.loop:
            self.loop.stop()

    def stop(self):
        """Stop the worker thread with proper cleanup."""
        self._stop_requested = True

        # Schedule async stop sequence on the worker loop
        if self.loop and not self.loop.is_closed():
            fut = asyncio.run_coroutine_threadsafe(self._async_stop(), self.loop)
            fut.result(timeout=5)

        # Cleanup worker thread
        self.quit()
        self.wait(5000)  # Wait up to 5 seconds
        if self.isRunning():
            print("Force terminating worker thread")
            self.terminate()

    def _sender_log_callback(self, level: str, message: str):
        self.log_message.emit(f"[Sender] {message}")

    def _sender_status_callback(self, status: str):
        display_status, color = self.STATUS_MAP.get(status, ("Unknown", "#8E8E93"))
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
        print(f"\n=== AsyncWorker.scan_controllers() DEBUG START ===")

        if not self.controller_manager:
            self.controller_manager = ControllerManager()
            print("Created new ControllerManager")

        # Ensure pygame joystick subsystem is initialized
        self.controller_manager.initialize()
        print("Controller manager initialized")

        # Scan for controllers and get only connected ones
        all_controllers = self.controller_manager.scan_controllers()
        connected_controllers = self.controller_manager.get_connected_controllers()

        print(f"Scan results: {len(all_controllers)} total, {len(connected_controllers)} connected")

        # Debug log details
        print("All controllers:")
        for i, controller in enumerate(all_controllers):
            print(f"  [{i}] {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        print("Connected controllers:")
        for i, controller in enumerate(connected_controllers):
            print(f"  [{i}] {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        self.logger.info(f"Scan results: {len(all_controllers)} total, {len(connected_controllers)} connected")

        # Debug log details
        for controller in all_controllers:
            self.logger.info(f"  Controller: {controller.name} - State: {controller.state} - ID: {controller.identifier}")

        print(f"About to emit controller_detected signal with {len(connected_controllers)} controllers")
        self.controller_detected.emit(connected_controllers)
        print("controller_detected signal emitted")

        self.log_message.emit(f"Found {len(connected_controllers)} connected controllers")
        print("log_message signal emitted")
        print(f"=== AsyncWorker.scan_controllers() DEBUG END ===\n")

    @Slot()
    def start_sender(self):
        """Start sender application."""
        if self.sender_app and self.sender_app.running:
            self.logger.warning("Sender is already running.")
            self.log_message.emit("Sender is already running.")
            return
        # Build config from current UI settings
        from input_link.models import ConfigModel, SenderConfig, ReceiverConfig, ControllerConfig
        controllers_cfg = {}
        for cid, entry in self.sender_settings.get("controllers", {}).items():
            if not entry.get("enabled", False):
                continue
            controllers_cfg[cid] = ControllerConfig(
                assigned_number=entry.get("number", 1),
                enabled=True,
            )
        cfg = ConfigModel(
            sender_config=SenderConfig(
                receiver_host=self.sender_settings.get("host", "127.0.0.1"),
                receiver_port=int(self.sender_settings.get("port", 8765)),
                polling_rate=int(self.sender_settings.get("polling_rate", 60)),
                controllers=controllers_cfg,
            ),
            receiver_config=ReceiverConfig(),
        )

        self.sender_app = SenderApp(
            log_callback=self._sender_log_callback,
            status_callback=self._sender_status_callback,
            verbose=False,
        )
        # Inject config prepared from UI
        self.sender_app.config = cfg
        self._schedule(self.sender_app.start())

    @Slot()
    def stop_sender(self):
        """Request to stop the sender application."""
        if not self.sender_app or not self.sender_app.running:
            self.logger.warning("Sender is not running.")
            self.log_message.emit("Sender is not running.")
            return

        if self.loop and self.sender_app:
            self._schedule(self.sender_app.stop())

    @Slot()
    def start_receiver(self):
        """Start receiver application."""
        if self.receiver_app and self.receiver_app.running:
            self.logger.warning("Receiver is already running.")
            self.log_message.emit("Receiver is already running.")
            return
        # Build config from current UI settings
        from input_link.models import ConfigModel, SenderConfig, ReceiverConfig
        cfg = ConfigModel(
            sender_config=SenderConfig(receiver_host="127.0.0.1"),
            receiver_config=ReceiverConfig(
                listen_host=self.receiver_settings.get("host", "0.0.0.0"),
                listen_port=int(self.receiver_settings.get("port", 8765)),
                max_controllers=int(self.receiver_settings.get("max_controllers", 4)),
                auto_create_virtual=bool(self.receiver_settings.get("auto_create", True)),
            ),
        )

        self.receiver_app = ReceiverApp(
            log_callback=self._receiver_log_callback,
            status_callback=self._receiver_status_callback,
            verbose=False,
        )
        # Inject config prepared from UI
        self.receiver_app.config = cfg
        self._schedule(self.receiver_app.start())

    @Slot(dict)
    def on_sender_settings_changed(self, payload: Dict):
        t = payload.get("type")
        if t == "sender_network":
            host = payload.get("host")
            port = payload.get("port")
            rate = payload.get("polling_rate")
            if isinstance(host, str):
                self.sender_settings["host"] = host
            if isinstance(port, int):
                self.sender_settings["port"] = port
            if isinstance(rate, int):
                self.sender_settings["polling_rate"] = rate
            # Live-update network settings if sender is running
            try:
                if self.sender_app and self.sender_app.running and self.loop:
                    self._schedule(
                        self.sender_app.update_network_settings(
                            self.sender_settings["host"],
                            int(self.sender_settings["port"]),
                        )
                    )
            except Exception:
                pass
        elif t == "controller_number":
            cid = payload.get("controller_id")
            num = payload.get("number")
            if cid:
                entry = self.sender_settings["controllers"].setdefault(cid, {"enabled": True, "number": 1})
                if isinstance(num, int):
                    entry["number"] = num
                # Live-apply number change if sender is running
                try:
                    if self.sender_app and self.sender_app.running:
                        self.sender_app.set_controller_number(cid, int(entry["number"]))
                except Exception:
                    pass

    @Slot(str, bool)
    def on_sender_controller_enabled(self, controller_id: str, enabled: bool):
        entry = self.sender_settings["controllers"].setdefault(controller_id, {"enabled": False, "number": 1})
        entry["enabled"] = bool(enabled)
        # Live-apply enable/disable
        try:
            if self.sender_app and self.sender_app.running:
                num = int(entry.get("number", 1))
                self.sender_app.set_controller_enabled(controller_id, bool(enabled), number=num)
        except Exception:
            pass

    @Slot(dict)
    def on_receiver_settings_changed(self, payload: Dict):
        host = payload.get("host")
        port = payload.get("port")
        maxc = payload.get("max_controllers")
        auto = payload.get("auto_create")
        if isinstance(host, str):
            self.receiver_settings["host"] = host
        if isinstance(port, int):
            self.receiver_settings["port"] = port
        if isinstance(maxc, int):
            self.receiver_settings["max_controllers"] = maxc
        if isinstance(auto, bool):
            self.receiver_settings["auto_create"] = auto

    @Slot()
    def stop_receiver(self):
        """Request to stop the receiver application."""
        if not self.receiver_app or not self.receiver_app.running:
            self.logger.warning("Receiver is not running.")
            self.log_message.emit("Receiver is not running.")
            return

        if self.loop and self.receiver_app:
            self._schedule(self.receiver_app.stop())

    def _schedule(self, coro):
        """Schedule a coroutine on the worker loop, handling errors uniformly."""
        if not (self.loop and not self.loop.is_closed()):
            return None
        try:
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        except Exception as e:
            # Keep existing behavior: print errors to stdout
            print(f"Error scheduling coroutine: {e}")
            return None


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
        # Cache last known non-empty controller list to avoid clearing UI on transient empty scans
        self._last_controllers = []

        # Ensure graceful shutdown on app quit
        self.aboutToQuit.connect(self._on_about_to_quit)

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
            self.stacked_widget.resize(600, 750)  # Set default size
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

    def _connect_sender_window_signals(self):
        """Connect sender window signals."""
        print(f"SenderWindow check: {self.sender_window is not None}")
        print(f"AsyncWorker check: {self.async_worker is not None}")
        print(f"start_capture check: {hasattr(self.sender_window, 'start_capture') if self.sender_window else False}")
        print(f"back_btn check: {hasattr(self.sender_window, 'back_btn') if self.sender_window else False}")
        print(f"scan_btn check: {hasattr(self.sender_window, 'scan_btn') if self.sender_window else False}")
        if self.sender_window and self.async_worker:
            # Connect available signals
            self._connect_signal(self.sender_window, 'start_capture', self.async_worker.start_sender, "Connected start_capture signal")
            self._connect_signal(self.sender_window, 'stop_capture', self._stop_sender, "Connected stop_capture signal")
            if hasattr(self.sender_window, 'back_btn'):
                self.sender_window.back_btn.clicked.connect(self._show_main_window)
                print("Connected back_btn signal")
            # High-level request + settings and toggles (avoid double-scanning)
            self._connect_signal(self.sender_window, 'scan_controllers_requested', self.async_worker.scan_controllers, "Connected scan_controllers_requested signal")
            self._connect_signal(self.sender_window, 'settings_changed', self.async_worker.on_sender_settings_changed, "Connected sender settings_changed signal")
            self._connect_signal(self.sender_window, 'controller_enabled', self.async_worker.on_sender_controller_enabled, "Connected sender controller_enabled signal")
            print("SenderWindow signals connected successfully")
        else:
            print("Warning: SenderWindow or AsyncWorker not available")

    def _connect_receiver_window_signals(self):
        """Connect receiver window signals."""
        print(f"ReceiverWindow check: {self.receiver_window is not None}")
        print(f"start_server check: {hasattr(self.receiver_window, 'start_server') if self.receiver_window else False}")
        print(f"stop_server check: {hasattr(self.receiver_window, 'stop_server') if self.receiver_window else False}")
        print(f"back_btn check: {hasattr(self.receiver_window, 'back_btn') if self.receiver_window else False}")
        if self.receiver_window and self.async_worker:
            # Connect available signals
            self._connect_signal(self.receiver_window, 'start_server', self.async_worker.start_receiver, "Connected start_server signal")
            self._connect_signal(self.receiver_window, 'stop_server', self._stop_receiver, "Connected stop_server signal")
            if hasattr(self.receiver_window, 'back_btn'):
                self.receiver_window.back_btn.clicked.connect(self._show_main_window)
                print("Connected back_btn signal")
            self._connect_signal(self.receiver_window, 'settings_changed', self.async_worker.on_receiver_settings_changed, "Connected receiver settings_changed signal")
            print("ReceiverWindow signals connected successfully")
        else:
            print("Warning: ReceiverWindow or AsyncWorker not available")

    def _connect_signal(self, source, signal_name: str, slot, success_message: str):
        """Connect a signal by name to a slot if present, printing a debug line.
        Preserves behavior/messages while reducing repetition.
        """
        if hasattr(source, signal_name):
            getattr(source, signal_name).connect(slot)
            print(success_message)

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
        self._stop_sender()
        self._stop_receiver()
        self.main_window.add_log_message("All services stopped")

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
        print(f"\n=== InputLinkApplication._on_controllers_detected() DEBUG ===")
        print(f"Received signal with {len(controllers)} controllers")
        for i, controller in enumerate(controllers):
            print(f"  [{i}] {controller.name} - {controller.state} - {controller.identifier}")

        print("About to call sender_window.update_controllers()")
        # Always update UI with current scan results
        self.sender_window.update_controllers(controllers)
        print("sender_window.update_controllers() completed")

        self._last_controllers = controllers
        print(f"_last_controllers updated: {len(self._last_controllers)} controllers")

        if not controllers:
            self.main_window.add_log_message("No controllers found")
            print("Added 'No controllers found' log message")

        print(f"=== _on_controllers_detected() DEBUG END ===\n")

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

    def _on_about_to_quit(self):
        """Ensure background threads and loops stop before app exit."""
        # Stop async worker first
        if hasattr(self, 'async_worker') and self.async_worker:
            print("Stopping async worker (aboutToQuit)...")
            self.async_worker.stop()
            self.async_worker.wait(3000)

        # Close stacked widget if it exists
        if hasattr(self, 'stacked_widget') and self.stacked_widget:
            self.stacked_widget.close()

        # Close individual windows
        for window_name in ['main_window', 'sender_window', 'receiver_window']:
            if hasattr(self, window_name):
                window = getattr(self, window_name)
                if window and not window.isHidden():
                    window.close()


def run_gui_application():
    """Run the GUI application."""
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


if __name__ == "__main__":
    sys.exit(run_gui_application())
