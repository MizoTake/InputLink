"""Sender application for capturing and forwarding controller inputs."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Callable, Optional

import click

from input_link.core import ControllerManager, InputCaptureEngine
from input_link.core.logging_system import setup_application_logging, LogLevel
from input_link.models import ConfigModel, ReceiverConfig, SenderConfig
from input_link.network import WebSocketClient


class SenderApp:
    """Sender application for Input Link."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        log_callback: Optional[Callable[[str, str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        verbose: bool = False,
    ):
        """Initialize sender application.
        
        Args:
            config_path: Path to configuration file
            log_callback: Callback for log messages (level, message)
            status_callback: Callback for status changes
            verbose: Enable verbose (DEBUG) logging
        """
        self.config_path = config_path or Path.home() / ".input-link" / "config.json"
        self.config: Optional[ConfigModel] = None
        self.controller_manager: Optional[ControllerManager] = None
        self.input_engine: Optional[InputCaptureEngine] = None
        self.websocket_client: Optional[WebSocketClient] = None
        self.running = False
        self._status_callback = status_callback
        self._main_task: Optional[asyncio.Task] = None
        
        # Initialize logging
        self.logger = setup_application_logging(
            app_name="sender",
            config=None,  # Will be set after config loads
            verbose=verbose,
            log_callback=log_callback,
        )

    async def start(self) -> None:
        """Start the sender application."""
        try:
            self.logger.info("Starting sender application...")
            # Load configuration
            await self._load_config()

            # Update logger with loaded config
            self.logger.config = self.config

            # Initialize components
            await self._initialize_components()

            # Start services
            await self._start_services()

            self.running = True
            self.logger.info("Sender application started successfully")

            # Run main loop
            self._main_task = asyncio.create_task(self._main_loop())
            await self._main_task

        except asyncio.CancelledError:
            self.logger.info("Sender application task was cancelled.")
        except Exception as e:
            self.logger.error(f"Failed to start sender application: {e}")
            # In GUI mode, don't exit, just report error
            if not hasattr(self, 'logger') or self.logger.log_callback is None:
                sys.exit(1)
        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """Stop the sender application."""
        self.logger.info("Stop requested for sender application.")
        self.running = False
        if self._main_task:
            self._main_task.cancel()
        # Cleanup is called in the finally block of start()

    async def _load_config(self) -> None:
        """Load application configuration."""
        try:
            # Create config directory if needed
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Load or create config
            self.config = ConfigModel.load_from_file(self.config_path)
            self.logger.info(f"Configuration loaded from {self.config_path}")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    async def _initialize_components(self) -> None:
        """Initialize application components."""
        # Initialize controller manager
        self.controller_manager = ControllerManager(auto_assign_numbers=True)
        self.controller_manager.initialize()

        # Initialize input capture engine
        self.input_engine = InputCaptureEngine(
            self.controller_manager,
            input_callback=self._on_controller_input,
        )

        # Initialize WebSocket client
        self.websocket_client = WebSocketClient(
            host=self.config.sender_config.receiver_host,
            port=self.config.sender_config.receiver_port,
            reconnect_interval=self.config.sender_config.retry_interval,
            max_reconnect_attempts=self.config.sender_config.max_retry_attempts,
            status_callback=self._status_callback,
        )

        self.logger.info("Components initialized")

    async def _start_services(self) -> None:
        """Start application services."""
        # Start WebSocket client
        await self.websocket_client.start()

        # Scan for controllers
        controllers = self.controller_manager.scan_controllers()
        self.logger.info(f"Found {len(controllers)} controller(s)")

        for controller in controllers:
            self.logger.info(f"  - {controller.name} (Number: {controller.assigned_number})")

        # Start input capture
        self.input_engine.start_capture()

        self.logger.info("Services started")

    async def _main_loop(self) -> None:
        """Main application loop."""
        self.logger.info("Sender running - Press Ctrl+C to stop in CUI mode.")

        try:
            while self.running:
                # Periodically scan for new controllers
                # This might be too noisy for GUI logs
                # self.controller_manager.scan_controllers()

                # Sleep to prevent busy waiting
                await asyncio.sleep(5.0)

        except asyncio.CancelledError:
            self.logger.info("Main loop cancelled")

    async def _on_controller_input(self, input_data) -> None:
        """Handle controller input data."""
        if self.websocket_client and self.websocket_client.connected:
            await self.websocket_client.send_controller_input(input_data)

    async def _cleanup(self) -> None:
        """Cleanup application resources."""
        self.logger.info("Cleaning up sender resources...")

        self.running = False

        # Stop input capture
        if self.input_engine:
            self.input_engine.stop_capture()

        # Stop WebSocket client
        if self.websocket_client:
            await self.websocket_client.stop()

        # Cleanup controller manager
        if self.controller_manager:
            self.controller_manager.cleanup()

        self.logger.info("Sender cleanup complete")


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=False, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Receiver host address",
)
@click.option(
    "--port",
    default=8765,
    type=int,
    help="Receiver port",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(config: Optional[Path], host: str, port: int, verbose: bool) -> None:
    """Input Link Sender - Capture and forward controller inputs."""
    # Create sender app with verbose logging
    app = SenderApp(config_path=config, verbose=verbose)

    # Override config if command line options provided
    if config is None and (host != "127.0.0.1" or port != 8765):
        # Create temporary config with command line values
        from input_link.models import ReceiverConfig, SenderConfig
        app.config = ConfigModel(
            sender_config=SenderConfig(receiver_host=host, receiver_port=port),
            receiver_config=ReceiverConfig(),
        )

    # Run application
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        app.logger.info("Application stopped by user")
    except Exception as e:
        app.logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
