"""Base classes for virtual controller management."""

from __future__ import annotations

import logging
import platform
from abc import ABC, abstractmethod
from typing import Optional

from input_link.models import ControllerInputData

logger = logging.getLogger(__name__)


class VirtualController(ABC):
    """Abstract base class for virtual controllers."""

    def __init__(self, controller_number: int):
        """Initialize virtual controller.
        
        Args:
            controller_number: Controller number (1-8)
        """
        self.controller_number = controller_number
        self._connected = False

    @property
    def connected(self) -> bool:
        """Check if virtual controller is connected."""
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        """Connect virtual controller.
        
        Returns:
            True if connected successfully, False otherwise
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect virtual controller."""

    @abstractmethod
    async def update_state(self, input_data: ControllerInputData) -> bool:
        """Update controller state with input data.
        
        Args:
            input_data: Controller input data
            
        Returns:
            True if updated successfully, False otherwise
        """

    @abstractmethod
    def reset_state(self) -> None:
        """Reset controller to neutral state."""

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(controller_number={self.controller_number}, connected={self.connected})"


class VirtualControllerFactory:
    """Factory for creating platform-specific virtual controllers."""

    @staticmethod
    def create_controller(controller_number: int, **kwargs) -> Optional[VirtualController]:
        """Create virtual controller for current platform.
        
        Args:
            controller_number: Controller number (1-8)
            **kwargs: Additional platform-specific arguments
            
        Returns:
            Virtual controller instance or None if unsupported
        """
        current_platform = platform.system().lower()

        if current_platform == "windows":
            return VirtualControllerFactory._create_windows_controller(
                controller_number, **kwargs,
            )
        if current_platform == "darwin":  # macOS
            return VirtualControllerFactory._create_macos_controller(
                controller_number, **kwargs,
            )
        logger.error(f"Unsupported platform: {current_platform}")
        return None

    @staticmethod
    def _create_windows_controller(controller_number: int, **kwargs) -> Optional[VirtualController]:
        """Create Windows virtual controller using vgamepad.
        
        Args:
            controller_number: Controller number
            **kwargs: Additional arguments
            
        Returns:
            Windows virtual controller or None
        """
        try:
            from input_link.virtual.windows import WindowsVirtualController
            return WindowsVirtualController(controller_number, **kwargs)
        except ImportError as e:
            logger.error(f"Failed to import Windows virtual controller: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create Windows virtual controller: {e}")
            return None

    @staticmethod
    def _create_macos_controller(controller_number: int, **kwargs) -> Optional[VirtualController]:
        """Create macOS virtual controller using pygame.
        
        Args:
            controller_number: Controller number
            **kwargs: Additional arguments
            
        Returns:
            macOS virtual controller or None
        """
        try:
            from input_link.virtual.macos import MacOSVirtualController
            return MacOSVirtualController(controller_number, **kwargs)
        except ImportError as e:
            logger.error(f"Failed to import macOS virtual controller: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create macOS virtual controller: {e}")
            return None
