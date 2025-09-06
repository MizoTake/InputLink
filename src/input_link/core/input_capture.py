"""Input capture engine for real-time controller input polling."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from queue import Empty, Queue
from typing import Callable, Dict, Optional

import pygame

from input_link.core.controller_manager import ControllerManager, DetectedController
from input_link.models import ButtonState, ControllerInputData, ControllerState

logger = logging.getLogger(__name__)


@dataclass
class InputCaptureConfig:
    """Configuration for input capture engine."""

    polling_rate: int = 60  # Hz
    dead_zone: float = 0.1  # Axis dead zone
    enable_button_repeat: bool = False
    max_queue_size: int = 1000


class InputCaptureEngine:
    """Real-time controller input capture engine."""

    def __init__(
        self,
        controller_manager: ControllerManager,
        config: Optional[InputCaptureConfig] = None,
        input_callback: Optional[Callable[[ControllerInputData], None]] = None,
    ):
        """Initialize input capture engine.
        
        Args:
            controller_manager: Controller manager instance
            config: Capture configuration
            input_callback: Optional callback for input events
        """
        self._controller_manager = controller_manager
        self._config = config or InputCaptureConfig()
        self._input_callback = input_callback

        self._running = False
        self._capture_thread: Optional[threading.Thread] = None
        self._input_queue: Queue[ControllerInputData] = Queue(maxsize=self._config.max_queue_size)

        self._pygame_joysticks: Dict[int, pygame.joystick.Joystick] = {}
        self._previous_states: Dict[str, ControllerInputData] = {}

    def start_capture(self) -> None:
        """Start input capture in background thread."""
        if self._running:
            logger.warning("Input capture is already running")
            return

        self._running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            name="InputCaptureThread",
            daemon=True,
        )
        self._capture_thread.start()
        logger.info(f"Input capture started at {self._config.polling_rate} Hz")

    def stop_capture(self) -> None:
        """Stop input capture."""
        if not self._running:
            return

        self._running = False

        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=1.0)

        # Cleanup pygame joysticks
        for joystick in self._pygame_joysticks.values():
            if joystick.get_init():
                joystick.quit()
        self._pygame_joysticks.clear()

        logger.info("Input capture stopped")

    def get_input_data(self, timeout: float = 0.1) -> Optional[ControllerInputData]:
        """Get next input data from queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Next input data or None if timeout
        """
        try:
            return self._input_queue.get(timeout=timeout)
        except Empty:
            return None

    def get_current_state(self, controller_id: str) -> Optional[ControllerInputData]:
        """Get current state of a specific controller.
        
        Args:
            controller_id: Controller identifier
            
        Returns:
            Current controller state or None
        """
        return self._previous_states.get(controller_id)

    def _capture_loop(self) -> None:
        """Main capture loop running in background thread."""
        poll_interval = 1.0 / self._config.polling_rate

        while self._running:
            start_time = time.perf_counter()

            try:
                # Update pygame event queue to handle device changes
                pygame.event.pump()

                # Process all connected controllers
                connected_controllers = self._controller_manager.get_connected_controllers()

                for controller in connected_controllers:
                    if controller.assigned_number is None:
                        continue  # Skip unassigned controllers

                    input_data = self._capture_controller_input(controller)
                    if input_data:
                        # Check if state changed or button repeat is enabled
                        previous_state = self._previous_states.get(controller.identifier)

                        if (self._config.enable_button_repeat or
                            previous_state is None or
                            self._state_changed(previous_state, input_data)):

                            # Store current state
                            self._previous_states[controller.identifier] = input_data

                            # Queue input data
                            try:
                                self._input_queue.put_nowait(input_data)
                            except:
                                # Queue full, remove oldest item and add new one
                                try:
                                    self._input_queue.get_nowait()
                                    self._input_queue.put_nowait(input_data)
                                except Empty:
                                    pass

                            # Call callback if provided
                            if self._input_callback:
                                try:
                                    self._input_callback(input_data)
                                except Exception as e:
                                    logger.error(f"Error in input callback: {e}")

                # Maintain polling rate
                elapsed = time.perf_counter() - start_time
                sleep_time = max(0, poll_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)  # Brief pause on error

    def _capture_controller_input(self, controller: DetectedController) -> Optional[ControllerInputData]:
        """Capture input from a specific controller.
        
        Args:
            controller: Controller to capture from
            
        Returns:
            Controller input data or None on error
        """
        try:
            # Get or create pygame joystick
            joystick = self._get_pygame_joystick(controller)
            if not joystick:
                return None

            # Capture button states
            buttons = self._capture_button_state(joystick)

            # Capture axis states
            axes = self._capture_axis_state(joystick)

            # Create input data
            input_data = ControllerInputData(
                controller_number=controller.assigned_number,
                controller_id=controller.identifier,
                input_method=controller.preferred_input_method,
                buttons=buttons,
                axes=axes,
                timestamp=datetime.now(timezone.utc).timestamp(),
            )

            return input_data

        except Exception as e:
            logger.error(f"Error capturing input from {controller.name}: {e}")
            return None

    def _get_pygame_joystick(self, controller: DetectedController) -> Optional[pygame.joystick.Joystick]:
        """Get or create pygame joystick instance.
        
        Args:
            controller: Controller to get joystick for
            
        Returns:
            Pygame joystick instance or None
        """
        pygame_id = controller.pygame_id

        if pygame_id not in self._pygame_joysticks:
            try:
                joystick = pygame.joystick.Joystick(pygame_id)
                joystick.init()
                self._pygame_joysticks[pygame_id] = joystick
                logger.debug(f"Initialized pygame joystick for {controller.name}")
            except pygame.error as e:
                logger.error(f"Failed to initialize joystick {pygame_id}: {e}")
                return None

        return self._pygame_joysticks.get(pygame_id)

    def _capture_button_state(self, joystick: pygame.joystick.Joystick) -> ButtonState:
        """Capture button state from pygame joystick.
        
        Args:
            joystick: Pygame joystick instance
            
        Returns:
            Button state
        """
        buttons = ButtonState()

        try:
            num_buttons = joystick.get_numbuttons()

            # Standard Xbox controller button mapping
            if num_buttons >= 10:
                buttons.a = bool(joystick.get_button(0))
                buttons.b = bool(joystick.get_button(1))
                buttons.x = bool(joystick.get_button(2))
                buttons.y = bool(joystick.get_button(3))
                buttons.lb = bool(joystick.get_button(4))
                buttons.rb = bool(joystick.get_button(5))
                buttons.back = bool(joystick.get_button(6))
                buttons.start = bool(joystick.get_button(7))
                buttons.ls = bool(joystick.get_button(8))
                buttons.rs = bool(joystick.get_button(9))

            # D-pad from hat
            if joystick.get_numhats() > 0:
                hat = joystick.get_hat(0)
                buttons.dpad_left = hat[0] < 0
                buttons.dpad_right = hat[0] > 0
                buttons.dpad_up = hat[1] > 0
                buttons.dpad_down = hat[1] < 0

        except pygame.error as e:
            logger.error(f"Error reading button state: {e}")

        return buttons

    def _capture_axis_state(self, joystick: pygame.joystick.Joystick) -> ControllerState:
        """Capture axis state from pygame joystick.
        
        Args:
            joystick: Pygame joystick instance
            
        Returns:
            Controller axis state
        """
        axes = ControllerState()

        try:
            num_axes = joystick.get_numaxes()

            # Standard Xbox controller axis mapping
            if num_axes >= 2:
                # Left stick
                raw_x = joystick.get_axis(0)
                raw_y = joystick.get_axis(1)
                axes.left_stick_x = self._apply_dead_zone(raw_x)
                axes.left_stick_y = -self._apply_dead_zone(raw_y)  # Invert Y axis

            if num_axes >= 4:
                # Right stick
                raw_x = joystick.get_axis(2) if num_axes > 3 else joystick.get_axis(3)
                raw_y = joystick.get_axis(3) if num_axes > 4 else 0
                axes.right_stick_x = self._apply_dead_zone(raw_x)
                axes.right_stick_y = -self._apply_dead_zone(raw_y)  # Invert Y axis

            if num_axes >= 6:
                # Triggers (convert from [-1, 1] to [0, 1])
                raw_lt = joystick.get_axis(4)
                raw_rt = joystick.get_axis(5)
                axes.left_trigger = max(0.0, (raw_lt + 1.0) / 2.0)
                axes.right_trigger = max(0.0, (raw_rt + 1.0) / 2.0)

        except pygame.error as e:
            logger.error(f"Error reading axis state: {e}")

        return axes

    def _apply_dead_zone(self, value: float) -> float:
        """Apply dead zone to axis value.
        
        Args:
            value: Raw axis value
            
        Returns:
            Processed axis value
        """
        if abs(value) < self._config.dead_zone:
            return 0.0

        # Scale beyond dead zone to maintain full range
        sign = 1.0 if value >= 0 else -1.0
        scaled = (abs(value) - self._config.dead_zone) / (1.0 - self._config.dead_zone)
        return sign * min(1.0, scaled)

    def _state_changed(self, previous: ControllerInputData, current: ControllerInputData) -> bool:
        """Check if controller state has changed significantly.
        
        Args:
            previous: Previous state
            current: Current state
            
        Returns:
            True if state changed
        """
        # Check button changes
        prev_buttons = previous.buttons
        curr_buttons = current.buttons

        if (prev_buttons.a != curr_buttons.a or
            prev_buttons.b != curr_buttons.b or
            prev_buttons.x != curr_buttons.x or
            prev_buttons.y != curr_buttons.y or
            prev_buttons.lb != curr_buttons.lb or
            prev_buttons.rb != curr_buttons.rb or
            prev_buttons.back != curr_buttons.back or
            prev_buttons.start != curr_buttons.start or
            prev_buttons.ls != curr_buttons.ls or
            prev_buttons.rs != curr_buttons.rs or
            prev_buttons.dpad_up != curr_buttons.dpad_up or
            prev_buttons.dpad_down != curr_buttons.dpad_down or
            prev_buttons.dpad_left != curr_buttons.dpad_left or
            prev_buttons.dpad_right != curr_buttons.dpad_right):
            return True

        # Check axis changes (with small threshold to avoid noise)
        threshold = 0.01
        prev_axes = previous.axes
        curr_axes = current.axes

        if (abs(prev_axes.left_stick_x - curr_axes.left_stick_x) > threshold or
            abs(prev_axes.left_stick_y - curr_axes.left_stick_y) > threshold or
            abs(prev_axes.right_stick_x - curr_axes.right_stick_x) > threshold or
            abs(prev_axes.right_stick_y - curr_axes.right_stick_y) > threshold or
            abs(prev_axes.left_trigger - curr_axes.left_trigger) > threshold or
            abs(prev_axes.right_trigger - curr_axes.right_trigger) > threshold):
            return True

        return False

    def __del__(self):
        """Ensure cleanup on destruction."""
        self.stop_capture()
