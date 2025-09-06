"""Receiver application for simulating controller inputs."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Callable, Dict, Optional

import click

from input_link.core.logging_system import setup_application_logging, LogLevel
from input_link.models import ConfigModel, ControllerInputData
from input_link.network import WebSocketServer
from input_link.virtual import VirtualControllerManager


class ReceiverApp:
    """Receiver application for Input Link."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        log_callback: Optional[Callable[[str, str], None]] = None,
        status_callback: Optional[Callable[[str, Dict], None]] = None,
        verbose: bool = False,
    ):
        """Initialize receiver application.
        
        Args:
            config_path: Path to configuration file
            log_callback: Callback for log messages (level, message)
            status_callback: Callback for status changes (status, data)
            verbose: Enable verbose (DEBUG) logging
        """
        self.config_path = config_path or Path.home() / ".input-link" / "config.json"
        self.config: Optional[ConfigModel] = None
        self.websocket_server: Optional[WebSocketServer] = None
        self.virtual_controller_manager: Optional[VirtualControllerManager] = None
        self.running = False
        self._status_callback = status_callback
        self._main_task: Optional[asyncio.Task] = None
        
        # Initialize logging
        self.logger = setup_application_logging(
            app_name="receiver",
            config=None,  # Will be set after config loads
            verbose=verbose,
            log_callback=log_callback,
        )

    async def start(self) -> None:
        """Start the receiver application."""
        try:
            self.logger.info("Starting receiver application...")
            # Load configuration
            await self._load_config()

            # Update logger with loaded config
            self.logger.config = self.config

            # Initialize components
            await self._initialize_components()

            # Start services
            await self._start_services()

            self.running = True
            self.logger.info("Receiver application started successfully")

            # Run main loop
            self._main_task = asyncio.create_task(self._main_loop())
            await self._main_task

        except asyncio.CancelledError:
            self.logger.info("Receiver application task was cancelled.")
        except Exception as e:
            self.logger.error(f"Failed to start receiver application: {e}")
            if not hasattr(self, 'logger') or self.logger.log_callback is None:
                sys.exit(1)
        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """Stop the receiver application."""
        self.logger.info("Stop requested for receiver application.")
        self.running = False
        if self._main_task:
            self._main_task.cancel()

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
        # Initialize virtual controller manager
        max_controllers = self.config.receiver_config.max_controllers
        self.virtual_controller_manager = VirtualControllerManager(
            max_controllers=max_controllers if max_controllers > 0 else None,
            auto_create=self.config.receiver_config.auto_create_virtual,
            creation_callback=self._on_controller_created,
            destruction_callback=self._on_controller_destroyed,
        )

        # Initialize WebSocket server
        self.websocket_server = WebSocketServer(
            host="0.0.0.0",  # Listen on all interfaces
            port=self.config.receiver_config.listen_port,
            input_callback=self._on_controller_input,
            status_callback=self._status_callback,
        )

        self.logger.info("Components initialized")

    async def _start_services(self) -> None:
        """Start application services."""
        # Start virtual controller manager
        await self.virtual_controller_manager.start()

        # Start WebSocket server
        await self.websocket_server.start()

        self.logger.info(
            f"Server listening on port {self.config.receiver_config.listen_port}"
        )

    async def _main_loop(self) -> None:
        """Main application loop."""
        self.logger.info("Receiver running - Press Ctrl+C to stop in CUI mode.")

        try:
            while self.running:
                # Display status periodically
                await asyncio.sleep(30.0)

                if not self.running: break

                client_count = self.websocket_server.client_count
                controller_count = self.virtual_controller_manager.active_controller_count

                self.logger.info(
                    f"Status: {client_count} client(s), "
                    f"{controller_count} virtual controller(s)"
                )

        except asyncio.CancelledError:
            self.logger.info("Main loop cancelled")

    def _on_controller_input(self, input_data: ControllerInputData) -> None:
        """Handle received controller input data.
        
        Args:
            input_data: Controller input data from sender
        """
        # Forward to virtual controller manager
        asyncio.create_task(
            self.virtual_controller_manager.update_controller_state(input_data),
        )

    def _on_controller_created(self, controller_number: int) -> None:
        """Handle virtual controller creation.
        
        Args:
            controller_number: Controller number that was created
        """
        self.logger.info(f"Virtual controller {controller_number} created")

    def _on_controller_destroyed(self, controller_number: int) -> None:
        """Handle virtual controller destruction.
        
        Args:
            controller_number: Controller number that was destroyed
        """
        self.logger.info(f"Virtual controller {controller_number} destroyed")

    async def _cleanup(self) -> None:
        """Cleanup application resources."""
        self.logger.info("Cleaning up receiver resources...")

        self.running = False

        # Stop WebSocket server
        if self.websocket_server:
            await self.websocket_server.stop()

        # Stop virtual controller manager
        if self.virtual_controller_manager:
            await self.virtual_controller_manager.stop()

        self.logger.info("Receiver cleanup complete")


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=False, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--port",
    default=8765,
    type=int,
    help="Server port to listen on",
)
@click.option(
    "--max-controllers",
    default=4,
    type=int,
    help="Maximum number of virtual controllers",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    config: Optional[Path],
    port: int,
    max_controllers: int,
    verbose: bool,
) -> None:
    """Input Link Receiver - Simulate controller inputs from network."""
    # Create receiver app with verbose logging
    app = ReceiverApp(config_path=config, verbose=verbose)

    # Override config if command line options provided
    if config is None and (port != 8765 or max_controllers != 4):
        # Create temporary config with command line values
        from input_link.models import ReceiverConfig, SenderConfig
        app.config = ConfigModel(
            sender_config=SenderConfig(receiver_host="127.0.0.1"),
            receiver_config=ReceiverConfig(
                listen_port=port,
                max_controllers=max_controllers,
            ),
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
