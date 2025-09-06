"""Virtual controller manager for coordinating multiple virtual controllers."""

import logging
from typing import Dict, List, Optional, Callable
import asyncio

from .base import VirtualController, VirtualControllerFactory
from ..models import ControllerInputData


logger = logging.getLogger(__name__)


class VirtualControllerManager:
    """Manages multiple virtual controllers and their state synchronization."""
    
    def __init__(
        self,
        max_controllers: int = 4,
        auto_create: bool = True,
        creation_callback: Optional[Callable[[int], None]] = None,
        destruction_callback: Optional[Callable[[int], None]] = None
    ):
        """Initialize virtual controller manager.
        
        Args:
            max_controllers: Maximum number of virtual controllers
            auto_create: Automatically create controllers when needed
            creation_callback: Called when a controller is created
            destruction_callback: Called when a controller is destroyed
        """
        self.max_controllers = max_controllers
        self.auto_create = auto_create
        self.creation_callback = creation_callback
        self.destruction_callback = destruction_callback
        
        self._controllers: Dict[int, VirtualController] = {}
        self._running = False
        
    @property
    def active_controller_count(self) -> int:
        """Get number of active controllers."""
        return len([c for c in self._controllers.values() if c.connected])
    
    @property
    def controller_numbers(self) -> List[int]:
        """Get list of controller numbers.""" 
        return list(self._controllers.keys())
    
    async def start(self) -> None:
        """Start virtual controller manager."""
        if self._running:
            logger.warning("Virtual controller manager is already running")
            return
            
        self._running = True
        logger.info("Virtual controller manager started")
    
    async def stop(self) -> None:
        """Stop virtual controller manager and disconnect all controllers."""
        if not self._running:
            return
            
        self._running = False
        
        # Disconnect all controllers
        controller_numbers = list(self._controllers.keys())
        for controller_number in controller_numbers:
            await self.remove_controller(controller_number)
            
        logger.info("Virtual controller manager stopped")
    
    async def create_controller(self, controller_number: int, **kwargs) -> bool:
        """Create and connect virtual controller.
        
        Args:
            controller_number: Controller number (1-8)
            **kwargs: Additional controller-specific arguments
            
        Returns:
            True if created successfully, False otherwise
        """
        if not self._running:
            logger.warning("Cannot create controller - manager not running")
            return False
            
        if not (1 <= controller_number <= 8):
            logger.error(f"Invalid controller number: {controller_number}")
            return False
            
        if controller_number in self._controllers:
            logger.warning(f"Controller {controller_number} already exists")
            return True
            
        if len(self._controllers) >= self.max_controllers:
            logger.error(f"Maximum controllers ({self.max_controllers}) already created")
            return False
        
        try:
            # Create controller using factory
            controller = VirtualControllerFactory.create_controller(
                controller_number, **kwargs
            )
            
            if not controller:
                logger.error(f"Failed to create virtual controller {controller_number}")
                return False
            
            # Connect controller
            if not await controller.connect():
                logger.error(f"Failed to connect virtual controller {controller_number}")
                return False
            
            # Add to tracking
            self._controllers[controller_number] = controller
            
            logger.info(f"Virtual controller {controller_number} created and connected")
            
            # Call creation callback
            if self.creation_callback:
                try:
                    self.creation_callback(controller_number)
                except Exception as e:
                    logger.error(f"Error in creation callback: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create virtual controller {controller_number}: {e}")
            return False
    
    async def remove_controller(self, controller_number: int) -> bool:
        """Remove and disconnect virtual controller.
        
        Args:
            controller_number: Controller number to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if controller_number not in self._controllers:
            logger.warning(f"Controller {controller_number} does not exist")
            return False
            
        try:
            controller = self._controllers[controller_number]
            
            # Disconnect controller
            await controller.disconnect()
            
            # Remove from tracking
            del self._controllers[controller_number]
            
            logger.info(f"Virtual controller {controller_number} removed")
            
            # Call destruction callback
            if self.destruction_callback:
                try:
                    self.destruction_callback(controller_number)
                except Exception as e:
                    logger.error(f"Error in destruction callback: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove virtual controller {controller_number}: {e}")
            return False
    
    async def update_controller_state(self, input_data: ControllerInputData) -> bool:
        """Update virtual controller state with input data.
        
        Args:
            input_data: Controller input data
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self._running:
            logger.warning("Cannot update controller state - manager not running")
            return False
            
        controller_number = input_data.controller_number
        
        # Auto-create controller if enabled and doesn't exist
        if (controller_number not in self._controllers and 
            self.auto_create and 
            len(self._controllers) < self.max_controllers):
            
            logger.info(f"Auto-creating virtual controller {controller_number}")
            if not await self.create_controller(controller_number):
                return False
        
        # Get controller
        controller = self._controllers.get(controller_number)
        if not controller:
            logger.warning(f"Virtual controller {controller_number} not found")
            return False
            
        if not controller.connected:
            logger.warning(f"Virtual controller {controller_number} not connected")
            return False
        
        # Update controller state
        return await controller.update_state(input_data)
    
    async def reset_controller(self, controller_number: int) -> bool:
        """Reset virtual controller to neutral state.
        
        Args:
            controller_number: Controller number to reset
            
        Returns:
            True if reset successfully, False otherwise
        """
        controller = self._controllers.get(controller_number)
        if not controller:
            logger.warning(f"Virtual controller {controller_number} not found")
            return False
            
        try:
            controller.reset_state()
            logger.debug(f"Virtual controller {controller_number} reset to neutral state")
            return True
        except Exception as e:
            logger.error(f"Failed to reset virtual controller {controller_number}: {e}")
            return False
    
    async def reset_all_controllers(self) -> None:
        """Reset all virtual controllers to neutral state."""
        for controller_number in self._controllers:
            await self.reset_controller(controller_number)
    
    def get_controller_info(self) -> List[Dict[str, any]]:
        """Get information about all virtual controllers.
        
        Returns:
            List of controller information dictionaries
        """
        info = []
        for controller_number, controller in self._controllers.items():
            info.append({
                "controller_number": controller_number,
                "connected": controller.connected,
                "controller_type": controller.__class__.__name__,
                "controller_obj": controller
            })
        return info
    
    def is_controller_active(self, controller_number: int) -> bool:
        """Check if controller is active (exists and connected).
        
        Args:
            controller_number: Controller number to check
            
        Returns:
            True if active, False otherwise
        """
        controller = self._controllers.get(controller_number)
        return controller is not None and controller.connected
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()