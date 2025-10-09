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
            logger.info(f"vgamepad module loaded from: {vg.__file__}")

            # Create gamepad based on type
            if self.controller_type == "xbox360":
                logger.info("Creating VX360Gamepad...")
                self._gamepad = vg.VX360Gamepad()
                logger.info("VX360Gamepad created successfully")
            elif self.controller_type == "ds4":
                logger.info("Creating VDS4Gamepad...")
                self._gamepad = vg.VDS4Gamepad()
                logger.info("VDS4Gamepad created successfully")
            else:
                logger.error(f"Unsupported controller type: {self.controller_type}")
                return False

            self._connected = True
            logger.info(f"Windows virtual controller {self.controller_number} connected ({self.controller_type})")

            # Reset to neutral state
            self.reset_state()

            return True

        except ImportError as e:
            logger.error(f"vgamepad not available - install with: pip install vgamepad. Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        except Exception as e:
            logger.error(f"Failed to connect Windows virtual controller: {e}")
            import traceback
            logger.error(traceback.format_exc())
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

            if self.controller_type == "xbox360":
                # Reset all Xbox360 buttons
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

            elif self.controller_type == "ds4":
                # Reset all DS4 buttons
                buttons = [
                    vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
                    vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
                    vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
                    vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
                    vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
                    vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
                    vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
                    vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
                    vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
                    vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
                ]

                for button in buttons:
                    self._gamepad.release_button(button)

                # Reset D-pad
                self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)

                # Reset sticks (DS4 uses 0-255 range with 128 as center)
                self._gamepad.left_joystick(x_value=128, y_value=128)
                self._gamepad.right_joystick(x_value=128, y_value=128)

                # Reset triggers
                self._gamepad.left_trigger(value=0)
                self._gamepad.right_trigger(value=0)

            # Send update
            self._gamepad.update()
            logger.debug(f"Controller {self.controller_number} ({self.controller_type}) reset to neutral state")

        except Exception as e:
            logger.error(f"Failed to reset controller state: {e}")

    def _update_buttons(self, buttons: ButtonState) -> None:
        """Update button states.

        Args:
            buttons: Button state
        """
        import vgamepad as vg

        # Get previous button state
        prev_buttons = self._last_state.buttons if self._last_state else ButtonState()

        if self.controller_type == "xbox360":
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

        elif self.controller_type == "ds4":
            # Button mapping for DS4 (DualShock 4)
            button_mapping = {
                "a": vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
                "b": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
                "x": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
                "y": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
                "lb": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
                "rb": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
                "back": vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
                "start": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
                "ls": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
                "rs": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
            }

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

            # DS4 D-pad uses directional_pad method instead of buttons
            if (buttons.dpad_up != prev_buttons.dpad_up or
                buttons.dpad_down != prev_buttons.dpad_down or
                buttons.dpad_left != prev_buttons.dpad_left or
                buttons.dpad_right != prev_buttons.dpad_right):

                # Determine direction
                if buttons.dpad_up and buttons.dpad_right:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST)
                elif buttons.dpad_up and buttons.dpad_left:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST)
                elif buttons.dpad_down and buttons.dpad_right:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST)
                elif buttons.dpad_down and buttons.dpad_left:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST)
                elif buttons.dpad_up:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH)
                elif buttons.dpad_down:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH)
                elif buttons.dpad_left:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST)
                elif buttons.dpad_right:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST)
                else:
                    self._gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)

    def _update_axes(self, axes: ControllerState) -> None:
        """Update axis states.

        Args:
            axes: Controller axis state
        """
        if self.controller_type == "xbox360":
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

        elif self.controller_type == "ds4":
            # Convert from [-1, 1] to DS4's expected ranges

            # Left stick (range: 0 to 255, with 128 as center)
            left_x = int((axes.left_stick_x + 1.0) * 127.5)
            left_y = int((axes.left_stick_y + 1.0) * 127.5)
            self._gamepad.left_joystick(x_value=left_x, y_value=left_y)

            # Right stick (range: 0 to 255, with 128 as center)
            right_x = int((axes.right_stick_x + 1.0) * 127.5)
            right_y = int((axes.right_stick_y + 1.0) * 127.5)
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
