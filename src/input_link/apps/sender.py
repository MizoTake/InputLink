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
        input_preview_callback: Optional[Callable[[str, dict, dict], None]] = None,
        verbose: bool = False,
    ):
        """Initialize sender application.

        Args:
            config_path: Path to configuration file
            log_callback: Callback for log messages (level, message)
            status_callback: Callback for status changes
            input_preview_callback: Callback for input preview (controller_id, button_states, axis_values)
            verbose: Enable verbose (DEBUG) logging
        """
        self.config_path = config_path or Path.home() / ".input-link" / "config.json"
        self.config: Optional[ConfigModel] = None
        self.controller_manager: Optional[ControllerManager] = None
        self.input_engine: Optional[InputCaptureEngine] = None
        self.websocket_client: Optional[WebSocketClient] = None
        self.running = False
        self._status_callback = status_callback
        self._input_preview_callback = input_preview_callback
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

    def set_controller_input_method(self, controller_id: str, input_method: str) -> bool:
        """Set the input method for a controller (xinput or dinput)."""
        if not self.controller_manager:
            return False
        from input_link.models import InputMethod
        # Convert string to InputMethod enum
        method_enum = InputMethod.XINPUT if input_method.lower() == "xinput" else InputMethod.DINPUT
        ok = self.controller_manager.set_input_method(controller_id, method_enum)
        if ok:
            self.logger.info(f"Controller {controller_id} input method set to {input_method.upper()}")
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
        if self.websocket_client:
            await self.websocket_client.stop()
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
        # If config already provided (e.g., from GUI), skip loading from file
        if self.config is not None:
            self.logger.info("Using provided configuration (skipping file load)")
            return

        # Create config directory if needed
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or create config
        self.config = ConfigModel.load_from_file(self.config_path)
        self.logger.info(f"Configuration loaded from {self.config_path}")

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

        # Apply explicit controller configurations from config if provided
        mappings = getattr(self.config.sender_config, "controllers", {})
        if mappings:
            for cid, ccfg in mappings.items():
                if getattr(ccfg, "enabled", True):
                    # Assign desired number; will unassign previous owner if needed
                    self.controller_manager.assign_controller_number(cid, ccfg.assigned_number)

                    # Apply input method if specified
                    if hasattr(ccfg, "input_method"):
                        self.controller_manager.set_input_method(cid, ccfg.input_method)
                        self.logger.info(f"  - Applied input_method {ccfg.input_method.value} to {cid}")
                else:
                    # Disabled: ensure no assignment remains
                    for c in controllers:
                        if c.identifier == cid:
                            if c.assigned_number:
                                c.assigned_number = None
                            break

        for controller in controllers:
            self.logger.info(f"  - {controller.name} (Number: {controller.assigned_number})")

        # Start input capture
        self.input_engine.start_capture()

        self.logger.info("Services started")

    async def _main_loop(self) -> None:
        """Main application loop."""
        self.logger.info("Sender running - Press Ctrl+C to stop in CUI mode.")

        scan_interval = 30.0  # Scan for new controllers every 30 seconds
        last_scan_time = asyncio.get_event_loop().time()

        try:
            while self.running:
                current_time = asyncio.get_event_loop().time()

                # Periodically scan for new/disconnected controllers
                if current_time - last_scan_time >= scan_interval:
                    previous_count = len(self.controller_manager.get_connected_controllers())
                    self.controller_manager.scan_controllers()
                    current_count = len(self.controller_manager.get_connected_controllers())

                    # Only log if controller count changed
                    if current_count != previous_count:
                        self.logger.info(f"Controller count changed: {previous_count} -> {current_count}")

                    last_scan_time = current_time

                # Sleep to prevent busy waiting
                await asyncio.sleep(5.0)

        except asyncio.CancelledError:
            self.logger.info("Main loop cancelled")

    async def _on_controller_input(self, input_data) -> None:
        """Handle controller input data."""
        if self.websocket_client and self.websocket_client.connected:
            await self.websocket_client.send_controller_input(input_data)

        # Update GUI preview if callback is set
        if self._input_preview_callback:
            # Extract button and axis data from input_data
            button_states = {
                "a": input_data.buttons.a,
                "b": input_data.buttons.b,
                "x": input_data.buttons.x,
                "y": input_data.buttons.y,
                "lb": input_data.buttons.lb,
                "rb": input_data.buttons.rb,
                "back": input_data.buttons.back,
                "start": input_data.buttons.start,
                "ls": input_data.buttons.ls,
                "rs": input_data.buttons.rs,
                "dpad_up": input_data.buttons.dpad_up,
                "dpad_down": input_data.buttons.dpad_down,
                "dpad_left": input_data.buttons.dpad_left,
                "dpad_right": input_data.buttons.dpad_right,
            }
            axis_values = {
                "left_x": input_data.axes.left_stick_x,
                "left_y": input_data.axes.left_stick_y,
                "right_x": input_data.axes.right_stick_x,
                "right_y": input_data.axes.right_stick_y,
                "left_trigger": input_data.axes.left_trigger,
                "right_trigger": input_data.axes.right_trigger,
            }
            self._input_preview_callback(input_data.controller_id, button_states, axis_values)

    async def _cleanup(self) -> None:
        """Cleanup application resources."""
        self.logger.info("Cleaning up sender resources...")

        self.running = False

        # Cleanup order is important:
        # 1. Stop input capture (prevents new data generation)
        # 2. Send disconnect message to receiver (triggers gamepad cleanup)
        # 3. Stop WebSocket client (flushes pending messages and disconnects)
        # 4. Cleanup controller manager (releases pygame resources)

        # 1. Stop input capture first
        if self.input_engine:
            self.input_engine.stop_capture()
            self.input_engine = None

        # 2. Send disconnect message to receiver before closing connection
        if self.websocket_client and self.websocket_client.connected:
            from input_link.network import NetworkMessage
            disconnect_msg = NetworkMessage.create_controller_disconnect_message()
            await self.websocket_client.send_message(disconnect_msg)
            # Give a brief moment for the message to be sent
            await asyncio.sleep(0.1)
            self.logger.info("Sent disconnect message to receiver")

        # 3. Stop WebSocket client
        if self.websocket_client:
            await self.websocket_client.stop()
            self.websocket_client = None

        # 4. Cleanup controller manager last
        if self.controller_manager:
            self.controller_manager.cleanup()
            self.controller_manager = None

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
        from input_link.core import ControllerManager
        cm = ControllerManager()
        cm.initialize()
        controllers = cm.scan_controllers()
        print(f"Detected {len(controllers)} controller(s):")
        for c in controllers:
            print(f"- {c.name} | identifier={c.identifier} | pygame_id={c.pygame_id}")
        return
    # Create sender app with verbose logging
    app = SenderApp(config_path=config, verbose=verbose)

    # Apply CLI overrides by merging with existing config file (if any)
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
        key, num_str = m.split(":", 1)
        num = int(num_str)
        if num < 1 or num > 8:
            raise ValueError("number out of range 1-8")
        base_cfg.sender_config.controllers[key] = ControllerConfig(
            assigned_number=num,
            enabled=True,
        )

    app.config = base_cfg

    # Run application
    asyncio.run(app.start())


if __name__ == "__main__":
    main()
