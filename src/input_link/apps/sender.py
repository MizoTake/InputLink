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

    # Runtime updates
    def set_controller_number(self, controller_id: str, number: int) -> bool:
        if not self.controller_manager:
            return False
        ok = self.controller_manager.assign_controller_number(controller_id, number)
        if ok:
            self.logger.info(f"Controller {controller_id} set to Player {number}")
        return ok

    def set_controller_enabled(self, controller_id: str, enabled: bool, number: Optional[int] = None) -> bool:
        if not self.controller_manager:
            return False
        if enabled:
            if number is None:
                number = self.controller_manager._get_next_available_number()  # best effort
                if number is None:
                    self.logger.error("No available controller numbers to assign")
                    return False
            return self.set_controller_number(controller_id, number)
        else:
            ok = self.controller_manager.unassign_controller(controller_id)
            if ok:
                self.logger.info(f"Controller {controller_id} disabled")
            return ok

    async def update_network_settings(self, host: str, port: int) -> None:
        """Update receiver host/port and reconnect WebSocket client if needed."""
        if not self.config:
            return
        need_restart = (
            host != self.config.sender_config.receiver_host or
            port != self.config.sender_config.receiver_port
        )
        if not need_restart:
            return
        self.logger.info(f"Updating network settings to {host}:{port}")
        self.config.sender_config.receiver_host = host
        self.config.sender_config.receiver_port = port
        try:
            if self.websocket_client:
                await self.websocket_client.stop()
        except Exception:
            pass
        # Recreate client with new settings
        self.websocket_client = WebSocketClient(
            host=self.config.sender_config.receiver_host,
            port=self.config.sender_config.receiver_port,
            reconnect_interval=self.config.sender_config.retry_interval,
            max_reconnect_attempts=self.config.sender_config.max_retry_attempts,
            status_callback=self._status_callback,
        )
        await self.websocket_client.start()

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
            # If config already provided (e.g., from GUI), skip loading from file
            if self.config is not None:
                self.logger.info("Using provided configuration (skipping file load)")
                return

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
        # If explicit controller mappings are provided in config, prefer manual assignment
        has_explicit_mappings = bool(
            getattr(self.config, "sender_config", None)
            and getattr(self.config.sender_config, "controllers", None)
        )
        self.controller_manager = ControllerManager(auto_assign_numbers=not has_explicit_mappings)
        self.controller_manager.initialize()

        # Initialize input capture engine
        loop = asyncio.get_running_loop()
        from input_link.core.input_capture import InputCaptureConfig
        capture_config = InputCaptureConfig(
            polling_rate=self.config.sender_config.polling_rate,
        )
        self.input_engine = InputCaptureEngine(
            self.controller_manager,
            config=capture_config,
            input_callback=self._on_controller_input,
            event_loop=loop,
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

        # Apply explicit controller number assignments from config if provided
        try:
            mappings = getattr(self.config.sender_config, "controllers", {})
            if mappings:
                for cid, ccfg in mappings.items():
                    try:
                        if getattr(ccfg, "enabled", True):
                            # Assign desired number; will unassign previous owner if needed
                            self.controller_manager.assign_controller_number(cid, ccfg.assigned_number)
                        else:
                            # Disabled: ensure no assignment remains
                            # Find controller and clear assignment
                            for c in controllers:
                                if c.identifier == cid:
                                    if c.assigned_number:
                                        # Reassign to None by removing from internal set
                                        c.assigned_number = None
                                    break
                    except Exception as e:
                        self.logger.error(f"Failed to apply mapping for {cid}: {e}")
        except Exception as e:
            self.logger.error(f"Error applying controller mappings: {e}")

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
    "--controller-map",
    multiple=True,
    help=(
        "Controller number mapping in the form '<identifier>:<number>'. "
        "Repeatable. Identifier should match a controller identifier (guid_deviceId)."
    ),
)
@click.option(
    "--list-controllers",
    is_flag=True,
    help="List detected controllers and exit",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    config: Optional[Path],
    host: str,
    port: int,
    controller_map: tuple[str, ...],
    list_controllers: bool,
    verbose: bool,
) -> None:
    """Input Link Sender - Capture and forward controller inputs."""
    if list_controllers:
        try:
            from input_link.core import ControllerManager
            cm = ControllerManager()
            cm.initialize()
            controllers = cm.scan_controllers()
            print(f"Detected {len(controllers)} controller(s):")
            for c in controllers:
                print(f"- {c.name} | identifier={c.identifier} | pygame_id={c.pygame_id}")
            return
        except Exception as e:
            print(f"Failed to list controllers: {e}")
            return
    # Create sender app with verbose logging
    app = SenderApp(config_path=config, verbose=verbose)

    # Apply CLI overrides by merging with existing config file (if any)
    try:
        from input_link.models import ControllerConfig, SenderConfig, ReceiverConfig

        cfg_path = config or (Path.home() / ".input-link" / "config.json")
        base_cfg = ConfigModel.load_from_file(cfg_path)

        # Network overrides
        if host and host != base_cfg.sender_config.receiver_host:
            base_cfg.sender_config.receiver_host = host
        if port and port != base_cfg.sender_config.receiver_port:
            base_cfg.sender_config.receiver_port = port

        # Controller mapping overrides
        for m in controller_map:
            try:
                key, num_str = m.split(":", 1)
                num = int(num_str)
                if num < 1 or num > 8:
                    raise ValueError("number out of range 1-8")
                base_cfg.sender_config.controllers[key] = ControllerConfig(
                    assigned_number=num,
                    enabled=True,
                )
            except Exception as e:
                print(f"Ignoring invalid --controller-map '{m}': {e}")

        app.config = base_cfg
    except Exception as e:
        # If anything goes wrong, fall back to minimal inline config
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
