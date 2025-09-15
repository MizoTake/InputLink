"""Controller detection and management system."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

import pygame

from input_link.models import InputMethod

logger = logging.getLogger(__name__)


class ControllerConnectionState(Enum):
    """Controller connection states."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class DetectedController:
    """Information about a detected controller."""

    pygame_id: int
    device_id: int
    name: str
    guid: str
    num_axes: int
    num_buttons: int
    num_hats: int
    state: ControllerConnectionState = ControllerConnectionState.CONNECTED
    assigned_number: Optional[int] = None
    preferred_input_method: InputMethod = InputMethod.XINPUT

    @property
    def identifier(self) -> str:
        """Unique identifier for this controller."""
        return f"{self.guid}_{self.device_id}"

    def is_xbox_controller(self) -> bool:
        """Check if this is an Xbox-style controller."""
        name_lower = self.name.lower()
        return any(keyword in name_lower for keyword in [
            "xbox", "x360", "xinput", "360 controller", "x-box",
        ])

    def is_playstation_controller(self) -> bool:
        """Check if this is a PlayStation-style controller."""
        name_lower = self.name.lower()
        return any(keyword in name_lower for keyword in [
            "playstation", "ps3", "ps4", "ps5", "dualshock", "dualsense",
        ])

    def get_recommended_input_method(self) -> InputMethod:
        """Get recommended input method based on controller type."""
        if self.is_xbox_controller():
            return InputMethod.XINPUT
        return InputMethod.DINPUT


class ControllerManager:
    """Manages controller detection and state tracking."""

    def __init__(self, auto_assign_numbers: bool = True):
        """Initialize controller manager.
        
        Args:
            auto_assign_numbers: Automatically assign controller numbers
        """
        self._controllers: Dict[int, DetectedController] = {}
        self._device_id_to_pygame_id: Dict[int, int] = {}
        self._assigned_numbers: Set[int] = set()
        self._auto_assign_numbers = auto_assign_numbers
        self._initialized = False

    def initialize(self) -> None:
        """Initialize pygame and joystick subsystem."""
        if self._initialized:
            return

        # Initialize pygame - if this fails, it will raise an exception
        # which we let propagate according to project coding rules
        init_result = pygame.init()
        if init_result[1] > 0:  # Check for initialization failures
            failed_modules = init_result[1]
            logger.error(f"Failed to initialize {failed_modules} pygame modules")
            raise RuntimeError(f"Pygame initialization failed: {failed_modules} modules failed")

        pygame.joystick.init()
        self._initialized = True
        logger.info("Controller manager initialized successfully")

    def scan_controllers(self) -> List[DetectedController]:
        """Scan for connected controllers."""
        if not self._initialized:
            self.initialize()

        current_controllers = {}

        # Get current joystick count
        joystick_count = pygame.joystick.get_count()
        logger.debug(f"Found {joystick_count} joystick(s)")

        for i in range(joystick_count):
            # Create joystick and handle pygame.error
            # Since we must avoid try-catch, we'll let errors propagate but handle them at higher level
            joystick = pygame.joystick.Joystick(i)

            # Get device instance ID (unique per session)
            device_id = joystick.get_instance_id()

            controller = DetectedController(
                pygame_id=i,
                device_id=device_id,
                name=joystick.get_name(),
                guid=joystick.get_guid(),
                num_axes=joystick.get_numaxes(),
                num_buttons=joystick.get_numbuttons(),
                num_hats=joystick.get_numhats(),
            )

            # Set recommended input method
            controller.preferred_input_method = controller.get_recommended_input_method()

            # Auto-assign number if enabled and not already assigned
            if (self._auto_assign_numbers and
                controller.identifier not in [c.identifier for c in self._controllers.values()]):
                controller.assigned_number = self._get_next_available_number()
                if controller.assigned_number:
                    self._assigned_numbers.add(controller.assigned_number)

            current_controllers[i] = controller
            self._device_id_to_pygame_id[device_id] = i

            logger.info(f"Detected controller: {controller.name} (ID: {device_id})")

        # Update controller list
        old_controllers = set(self._controllers.keys())
        new_controllers = set(current_controllers.keys())

        # Mark disconnected controllers
        for pygame_id in old_controllers - new_controllers:
            if pygame_id in self._controllers:
                self._controllers[pygame_id].state = ControllerConnectionState.DISCONNECTED
                logger.info(f"Controller disconnected: {self._controllers[pygame_id].name}")

        # Add or update controllers, preserving existing state and assigned numbers
        for pygame_id, new_controller in current_controllers.items():
            if pygame_id in self._controllers:
                # Preserve existing assigned number and state
                existing_controller = self._controllers[pygame_id]
                new_controller.assigned_number = existing_controller.assigned_number
                new_controller.state = ControllerConnectionState.CONNECTED
            else:
                # New controller - ensure it's marked as connected
                new_controller.state = ControllerConnectionState.CONNECTED

            self._controllers[pygame_id] = new_controller

        return list(self._controllers.values())

    def get_controller_by_id(self, device_id: int) -> Optional[DetectedController]:
        """Get controller by device ID."""
        pygame_id = self._device_id_to_pygame_id.get(device_id)
        if pygame_id is not None:
            return self._controllers.get(pygame_id)
        return None

    def get_controller_by_pygame_id(self, pygame_id: int) -> Optional[DetectedController]:
        """Get controller by pygame ID."""
        return self._controllers.get(pygame_id)

    def get_connected_controllers(self) -> List[DetectedController]:
        """Get list of currently connected controllers."""
        return [
            controller for controller in self._controllers.values()
            if controller.state == ControllerConnectionState.CONNECTED
        ]

    def assign_controller_number(self, controller_id: str, number: int) -> bool:
        """Assign a controller number to a specific controller.
        
        Args:
            controller_id: Controller identifier
            number: Controller number (1-8)
            
        Returns:
            True if assignment successful, False otherwise
        """
        if not (1 <= number):
            logger.error(f"Invalid controller number: {number}")
            return False

        # Find controller by identifier; if not found, try GUID-only fallback
        controller = None
        for c in self._controllers.values():
            if c.identifier == controller_id:
                controller = c
                break

        if not controller:
            # Fallback: match by GUID prefix (identifier is GUID_instanceId)
            guid_key = controller_id.split("_")[0] if controller_id else ""
            if guid_key:
                candidates = [c for c in self._controllers.values() if c.guid == guid_key]
                if candidates:
                    # Prefer unassigned candidate
                    controller = next((c for c in candidates if c.assigned_number is None), candidates[0])

        if not controller:
            logger.error(f"Controller not found: {controller_id}")
            return False

        # Check if number is already assigned
        if number in self._assigned_numbers:
            # Remove from previous controller
            for c in self._controllers.values():
                if c.assigned_number == number and c.identifier != controller_id:
                    c.assigned_number = None
                    logger.info(f"Unassigned number {number} from {c.name}")
                    break

        # Remove old assignment
        if controller.assigned_number:
            self._assigned_numbers.discard(controller.assigned_number)

        # Assign new number
        controller.assigned_number = number
        self._assigned_numbers.add(number)

        logger.info(f"Assigned controller number {number} to {controller.name}")
        return True

    def unassign_controller(self, controller_id: str) -> bool:
        """Clear assigned number for a specific controller.
        
        Args:
            controller_id: Controller identifier
        Returns:
            True if unassigned, False otherwise
        """
        for c in self._controllers.values():
            if c.identifier == controller_id:
                if c.assigned_number:
                    self._assigned_numbers.discard(c.assigned_number)
                    c.assigned_number = None
                    logger.info(f"Unassigned number from {c.name}")
                return True
        logger.error(f"Controller not found for unassign: {controller_id}")
        return False

    def set_input_method(self, controller_id: str, method: InputMethod) -> bool:
        """Set preferred input method for a controller.
        
        Args:
            controller_id: Controller identifier
            method: Input method to use
            
        Returns:
            True if setting successful, False otherwise
        """
        for controller in self._controllers.values():
            if controller.identifier == controller_id:
                controller.preferred_input_method = method
                logger.info(f"Set input method {method.value} for {controller.name}")
                return True

        logger.error(f"Controller not found: {controller_id}")
        return False

    def _get_next_available_number(self) -> Optional[int]:
        """Get the next available controller number (no fixed upper bound)."""
        i = 1
        # Find the smallest positive integer not in the assigned set
        while i in self._assigned_numbers:
            i += 1
        return i

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._initialized:
            try:
                pygame.joystick.quit()
                pygame.quit()
                self._initialized = False
                logger.info("Controller manager cleaned up")
            except pygame.error as e:
                logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Ensure cleanup on destruction."""
        self.cleanup()
