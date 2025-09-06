"""macOS virtual controller implementation using system APIs."""

import logging
from typing import Optional, Dict, Any

from .base import VirtualController
from ..models import ControllerInputData, ButtonState, ControllerState


logger = logging.getLogger(__name__)


class MacOSVirtualController(VirtualController):
    """macOS virtual controller using system APIs and pynput."""
    
    def __init__(self, controller_number: int):
        """Initialize macOS virtual controller.
        
        Args:
            controller_number: Controller number (1-8)
        """
        super().__init__(controller_number)
        self._keyboard_controller = None
        self._last_state: Optional[ControllerInputData] = None
        
        # Key mappings for controller buttons (using common game key bindings)
        self._button_key_mapping = {
            'a': 'z',      # A button -> Z key
            'b': 'x',      # B button -> X key  
            'x': 'c',      # X button -> C key
            'y': 'v',      # Y button -> V key
            'lb': 'q',     # Left bumper -> Q key
            'rb': 'e',     # Right bumper -> E key
            'back': 'tab', # Back -> Tab key
            'start': 'return',  # Start -> Enter key
            'ls': 'f',     # Left stick click -> F key
            'rs': 'g',     # Right stick click -> G key
            'dpad_up': 'up',     # D-pad up -> Up arrow
            'dpad_down': 'down', # D-pad down -> Down arrow
            'dpad_left': 'left', # D-pad left -> Left arrow  
            'dpad_right': 'right', # D-pad right -> Right arrow
        }
        
        # Stick to keyboard mapping (WASD for left stick, arrow keys for right)
        self._stick_key_mapping = {
            'left_stick': {
                'up': 'w',
                'down': 's', 
                'left': 'a',
                'right': 'd'
            },
            'right_stick': {
                'up': 'i',
                'down': 'k',
                'left': 'j', 
                'right': 'l'
            }
        }
    
    async def connect(self) -> bool:
        """Connect virtual controller using pynput.
        
        Returns:
            True if connected successfully, False otherwise
        """
        if self._connected:
            logger.warning(f"Controller {self.controller_number} is already connected")
            return True
            
        try:
            from pynput.keyboard import Controller as KeyboardController
            
            self._keyboard_controller = KeyboardController()
            self._connected = True
            
            logger.info(f"macOS virtual controller {self.controller_number} connected (keyboard simulation)")
            logger.info("Note: This implementation simulates controller input via keyboard keys")
            
            # Reset to neutral state
            self.reset_state()
            
            return True
            
        except ImportError:
            logger.error("pynput not available - install with: pip install pynput")
            return False
        except Exception as e:
            logger.error(f"Failed to connect macOS virtual controller: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect virtual controller."""
        if not self._connected:
            return
            
        try:
            # Reset to neutral state before disconnecting
            self.reset_state()
            
            self._keyboard_controller = None
            self._connected = False
            
            logger.info(f"macOS virtual controller {self.controller_number} disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting macOS virtual controller: {e}")
    
    async def update_state(self, input_data: ControllerInputData) -> bool:
        """Update controller state with input data.
        
        Args:
            input_data: Controller input data
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self._connected or not self._keyboard_controller:
            logger.warning("Cannot update state - controller not connected")
            return False
            
        try:
            # Update button states
            self._update_buttons(input_data.buttons)
            
            # Update stick states (mapped to keyboard)
            self._update_sticks(input_data.axes)
            
            # Update triggers (mapped to keyboard)
            self._update_triggers(input_data.axes)
            
            # Store last state
            self._last_state = input_data
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update controller state: {e}")
            return False
    
    def reset_state(self) -> None:
        """Reset controller to neutral state.""" 
        if not self._connected or not self._keyboard_controller:
            return
            
        try:
            # Release all mapped keys
            all_keys = set()
            
            # Add button keys
            all_keys.update(self._button_key_mapping.values())
            
            # Add stick keys
            for stick_mapping in self._stick_key_mapping.values():
                all_keys.update(stick_mapping.values())
                
            # Add trigger keys (hardcoded for now)
            all_keys.add('r')  # Left trigger
            all_keys.add('t')  # Right trigger
            
            # Release all keys
            for key in all_keys:
                try:
                    self._keyboard_controller.release(key)
                except:
                    pass  # Ignore errors for individual key releases
                    
            logger.debug(f"Controller {self.controller_number} reset to neutral state")
            
        except Exception as e:
            logger.error(f"Failed to reset controller state: {e}")
    
    def _update_buttons(self, buttons: ButtonState) -> None:
        """Update button states via keyboard simulation.
        
        Args:
            buttons: Button state
        """
        # Get previous button state
        prev_buttons = self._last_state.buttons if self._last_state else ButtonState()
        
        # Update each button
        for button_name, key in self._button_key_mapping.items():
            current_pressed = getattr(buttons, button_name)
            previous_pressed = getattr(prev_buttons, button_name)
            
            # Only update if state changed
            if current_pressed != previous_pressed:
                try:
                    if current_pressed:
                        self._keyboard_controller.press(key)
                    else:
                        self._keyboard_controller.release(key)
                except Exception as e:
                    logger.debug(f"Failed to update button {button_name}: {e}")
    
    def _update_sticks(self, axes: ControllerState) -> None:
        """Update stick states via keyboard simulation.
        
        Args:
            axes: Controller axis state
        """
        # Get previous axis state
        prev_axes = self._last_state.axes if self._last_state else ControllerState()
        
        # Dead zone threshold
        dead_zone = 0.3
        
        # Update left stick
        self._update_stick_axis(
            'left_stick',
            (axes.left_stick_x, axes.left_stick_y),
            (prev_axes.left_stick_x, prev_axes.left_stick_y),
            dead_zone
        )
        
        # Update right stick
        self._update_stick_axis(
            'right_stick', 
            (axes.right_stick_x, axes.right_stick_y),
            (prev_axes.right_stick_x, prev_axes.right_stick_y),
            dead_zone
        )
    
    def _update_stick_axis(
        self, 
        stick_name: str, 
        current: tuple[float, float], 
        previous: tuple[float, float],
        dead_zone: float
    ) -> None:
        """Update individual stick axis.
        
        Args:
            stick_name: Name of stick ('left_stick' or 'right_stick')
            current: Current (x, y) values
            previous: Previous (x, y) values  
            dead_zone: Dead zone threshold
        """
        if stick_name not in self._stick_key_mapping:
            return
            
        keys = self._stick_key_mapping[stick_name]
        current_x, current_y = current
        previous_x, previous_y = previous
        
        # Handle X axis (left/right)
        current_left = current_x < -dead_zone
        current_right = current_x > dead_zone
        previous_left = previous_x < -dead_zone  
        previous_right = previous_x > dead_zone
        
        # Update left key
        if current_left != previous_left:
            try:
                if current_left:
                    self._keyboard_controller.press(keys['left'])
                else:
                    self._keyboard_controller.release(keys['left'])
            except Exception as e:
                logger.debug(f"Failed to update {stick_name} left: {e}")
                
        # Update right key
        if current_right != previous_right:
            try:
                if current_right:
                    self._keyboard_controller.press(keys['right'])
                else:
                    self._keyboard_controller.release(keys['right'])
            except Exception as e:
                logger.debug(f"Failed to update {stick_name} right: {e}")
        
        # Handle Y axis (up/down) 
        current_up = current_y > dead_zone
        current_down = current_y < -dead_zone
        previous_up = previous_y > dead_zone
        previous_down = previous_y < -dead_zone
        
        # Update up key
        if current_up != previous_up:
            try:
                if current_up:
                    self._keyboard_controller.press(keys['up'])
                else:
                    self._keyboard_controller.release(keys['up'])
            except Exception as e:
                logger.debug(f"Failed to update {stick_name} up: {e}")
                
        # Update down key  
        if current_down != previous_down:
            try:
                if current_down:
                    self._keyboard_controller.press(keys['down'])
                else:
                    self._keyboard_controller.release(keys['down'])
            except Exception as e:
                logger.debug(f"Failed to update {stick_name} down: {e}")
    
    def _update_triggers(self, axes: ControllerState) -> None:
        """Update trigger states via keyboard simulation.
        
        Args:
            axes: Controller axis state
        """
        # Get previous axis state
        prev_axes = self._last_state.axes if self._last_state else ControllerState()
        
        # Trigger threshold
        trigger_threshold = 0.1
        
        # Left trigger -> R key
        current_lt = axes.left_trigger > trigger_threshold
        previous_lt = prev_axes.left_trigger > trigger_threshold
        
        if current_lt != previous_lt:
            try:
                if current_lt:
                    self._keyboard_controller.press('r')
                else:
                    self._keyboard_controller.release('r')
            except Exception as e:
                logger.debug(f"Failed to update left trigger: {e}")
        
        # Right trigger -> T key
        current_rt = axes.right_trigger > trigger_threshold  
        previous_rt = prev_axes.right_trigger > trigger_threshold
        
        if current_rt != previous_rt:
            try:
                if current_rt:
                    self._keyboard_controller.press('t')
                else:
                    self._keyboard_controller.release('t')
            except Exception as e:
                logger.debug(f"Failed to update right trigger: {e}")
    
    def __del__(self):
        """Ensure cleanup on destruction."""
        if self._connected:
            # Note: We can't use await in __del__, so just do sync cleanup
            try:
                self.reset_state()
                self._keyboard_controller = None
                self._connected = False
            except:
                pass  # Ignore errors during destruction