"""Windows virtual controller implementation using vgamepad."""

from __future__ import annotations

import logging
import vgamepad as vg
from typing import Optional

from input_link.models import ButtonState, ControllerInputData, ControllerState
from input_link.virtual.base import VirtualController

logger = logging.getLogger(__name__)


class WindowsVirtualController(VirtualController):
    """Windows virtual controller using vgamepad/ViGEm."""

    def __init__(self, controller_number: int, controller_type: str = "xbox360"):
        """Initialize Windows virtual controller.
        
        Args:
            controller_number: Controller number (>=1)
            controller_type: Controller type ('xbox360' or 'ds4')
        """
        super().__init__(controller_number)
        self.controller_type = controller_type
        self._gamepad = None
        self._last_state: Optional[ControllerInputData] = None

    async def connect(self) -> bool:
        """Connect virtual controller using vgamepad.
        
        Returns:
            True if connected successfully, False otherwise
        """
        if self._connected:
            logger.warning(f"Controller {self.controller_number} is already connected")
            return True

        try:
            import vgamepad as vg

            # Create gamepad based on type
            if self.controller_type == "xbox360":
                self._gamepad = vg.VX360Gamepad()
            elif self.controller_type == "ds4":
                self._gamepad = vg.VDS4Gamepad()
            else:
                logger.error(f"Unsupported controller type: {self.controller_type}")
                return False

            self._connected = True
            logger.info(f"Windows virtual controller {self.controller_number} connected ({self.controller_type})")

            # Reset to neutral state
            self.reset_state()

            return True

        except ImportError:
            logger.error("vgamepad not available - install with: pip install vgamepad")
            return False
        except Exception as e:
            logger.error(f"Failed to connect Windows virtual controller: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect virtual controller."""
        if not self._connected:
            return

        try:
            if self._gamepad:
                # Reset to neutral state before disconnecting
                self.reset_state()

                # Note: vgamepad gamepads auto-disconnect when object is destroyed
                self._gamepad = None

            self._connected = False
            logger.info(f"Windows virtual controller {self.controller_number} disconnected")

        except Exception as e:
            logger.error(f"Error disconnecting Windows virtual controller: {e}")

    async def update_state(self, input_data: ControllerInputData) -> bool:
        """Update controller state with input data.
        
        Args:
            input_data: Controller input data
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self._connected or not self._gamepad:
            logger.warning("Cannot update state - controller not connected")
            return False

        try:
            # Update button states
            self._update_buttons(input_data.buttons)

            # Update axis states
            self._update_axes(input_data.axes)

            # Send update to system
            self._gamepad.update()

            # Store last state
            self._last_state = input_data

            return True

        except Exception as e:
            logger.error(f"Failed to update controller state: {e}")
            return False

    def reset_state(self) -> None:
        """Reset controller to neutral state."""
        if not self._connected or not self._gamepad:
            return

        try:
            import vgamepad as vg

            # Reset all buttons
            if self.controller_type == "xbox360":
                buttons = [
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
                ]

                for button in buttons:
                    self._gamepad.release_button(button)

                # Reset sticks
                self._gamepad.left_joystick(x_value=0, y_value=0)
                self._gamepad.right_joystick(x_value=0, y_value=0)

                # Reset triggers
                self._gamepad.left_trigger(value=0)
                self._gamepad.right_trigger(value=0)

            # Send update
            self._gamepad.update()
            logger.debug(f"Controller {self.controller_number} reset to neutral state")

        except Exception as e:
            logger.error(f"Failed to reset controller state: {e}")

    def _update_buttons(self, buttons: ButtonState) -> None:
        """Update button states.
        
        Args:
            buttons: Button state
        """
        import vgamepad as vg

        if self.controller_type != "xbox360":
            return  # Only Xbox360 mapping implemented for now

        # Button mapping for Xbox360
        button_mapping = {
            "a": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "b": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "x": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "lb": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "rb": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            "start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "ls": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            "rs": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            "dpad_up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            "dpad_down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            "dpad_left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            "dpad_right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        }

        # Get previous button state
        prev_buttons = self._last_state.buttons if self._last_state else ButtonState()

        # Update each button
        for button_name, vg_button in button_mapping.items():
            current_pressed = getattr(buttons, button_name)
            previous_pressed = getattr(prev_buttons, button_name)

            # Only update if state changed
            if current_pressed != previous_pressed:
                if current_pressed:
                    self._gamepad.press_button(vg_button)
                else:
                    self._gamepad.release_button(vg_button)

    def _update_axes(self, axes: ControllerState) -> None:
        """Update axis states.
        
        Args:
            axes: Controller axis state
        """
        if self.controller_type != "xbox360":
            return  # Only Xbox360 mapping implemented for now

        # Convert from [-1, 1] to vgamepad's expected ranges

        # Left stick (range: -32768 to 32767)
        left_x = int(axes.left_stick_x * 32767)
        left_y = int(axes.left_stick_y * 32767)
        self._gamepad.left_joystick(x_value=left_x, y_value=left_y)

        # Right stick (range: -32768 to 32767)
        right_x = int(axes.right_stick_x * 32767)
        right_y = int(axes.right_stick_y * 32767)
        self._gamepad.right_joystick(x_value=right_x, y_value=right_y)

        # Triggers (range: 0 to 255)
        left_trigger = int(axes.left_trigger * 255)
        right_trigger = int(axes.right_trigger * 255)
        self._gamepad.left_trigger(value=left_trigger)
        self._gamepad.right_trigger(value=right_trigger)

    def __del__(self):
        """Ensure cleanup on destruction."""
        if self._connected:
            # Note: We can't use await in __del__, so just do sync cleanup
            try:
                if self._gamepad:
                    self.reset_state()
                    self._gamepad = None
                self._connected = False
            except:
                pass  # Ignore errors during destruction
