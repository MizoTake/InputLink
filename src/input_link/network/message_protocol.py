"""Message protocol for network communication.

This module defines the canonical Pydantic model `NetworkMessage` used across
the codebase. Some tests and legacy callers expect a higher-level
`MessageProtocol` API with helpers like `parse_message()` and a returned object
exposing a `.type` attribute and `.get_controller_data()` method. To maintain
compatibility, a thin wrapper is provided around `NetworkMessage`.
"""

from __future__ import annotations

import logging
import uuid
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError

from input_link.models import ControllerInputData

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Network message types."""
    CONTROLLER_INPUT = "controller_input"
    CONTROLLER_CONNECT = "controller_connect"
    CONTROLLER_DISCONNECT = "controller_disconnect"
    STATUS_REQUEST = "status_request"
    STATUS_RESPONSE = "status_response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class NetworkMessage(BaseModel):
    """Network message wrapper with validation."""

    message_id: str = Field(..., description="Unique message identifier")
    message_type: MessageType = Field(..., description="Type of message")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload")

    @classmethod
    def create_controller_input_message(
        cls,
        input_data: ControllerInputData,
        message_id: Optional[str] = None,
    ) -> "NetworkMessage":
        """Create controller input message.
        
        Args:
            input_data: Controller input data
            message_id: Optional custom message ID
            
        Returns:
            Network message
        """
        return cls(
            message_id=message_id or str(uuid.uuid4()),
            message_type=MessageType.CONTROLLER_INPUT,
            payload=input_data.model_dump(),
        )

    @classmethod
    def create_status_request_message(cls, message_id: Optional[str] = None) -> "NetworkMessage":
        """Create status request message.
        
        Args:
            message_id: Optional custom message ID
            
        Returns:
            Network message
        """
        return cls(
            message_id=message_id or str(uuid.uuid4()),
            message_type=MessageType.STATUS_REQUEST,
        )

    @classmethod
    def create_status_response_message(
        cls,
        active_controllers: int,
        connection_status: str,
        message_id: Optional[str] = None,
    ) -> "NetworkMessage":
        """Create status response message.
        
        Args:
            active_controllers: Number of active controllers
            connection_status: Connection status
            message_id: Optional custom message ID
            
        Returns:
            Network message
        """
        return cls(
            message_id=message_id or str(uuid.uuid4()),
            message_type=MessageType.STATUS_RESPONSE,
            payload={
                "active_controllers": active_controllers,
                "connection_status": connection_status,
                "server_time": datetime.now(timezone.utc).isoformat(),
            },
        )

    @classmethod
    def create_error_message(
        cls,
        error_code: str,
        error_description: str,
        message_id: Optional[str] = None,
    ) -> "NetworkMessage":
        """Create error message.
        
        Args:
            error_code: Error code
            error_description: Error description
            message_id: Optional custom message ID
            
        Returns:
            Network message
        """
        return cls(
            message_id=message_id or str(uuid.uuid4()),
            message_type=MessageType.ERROR,
            payload={
                "error_code": error_code,
                "error_description": error_description,
            },
        )

    @classmethod
    def create_heartbeat_message(cls, message_id: Optional[str] = None) -> "NetworkMessage":
        """Create heartbeat message.
        
        Args:
            message_id: Optional custom message ID
            
        Returns:
            Network message
        """
        return cls(
            message_id=message_id or str(uuid.uuid4()),
            message_type=MessageType.HEARTBEAT,
        )

    def to_json(self) -> str:
        """Serialize message to JSON string.
        
        Returns:
            JSON string
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "NetworkMessage":
        """Deserialize message from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            Network message
            
        Raises:
            ValidationError: If JSON is invalid
        """
        return cls.model_validate_json(json_str)

    def get_controller_input_data(self) -> Optional[ControllerInputData]:
        """Extract controller input data from payload.
        
        Returns:
            Controller input data or None if not applicable
        """
        if self.message_type != MessageType.CONTROLLER_INPUT:
            return None

        try:
            return ControllerInputData.model_validate(self.payload)
        except ValidationError as e:
            logger.error(f"Failed to parse controller input data: {e}")
            return None

    model_config = {
        "use_enum_values": True,
        "str_strip_whitespace": True,
    }


# ------------------------------
# Compatibility wrapper for tests/legacy API
# ------------------------------

class _ProtocolParsedMessage:
    """Lightweight wrapper exposing a stable interface for tests.

    Attributes:
        type: Message type as a simple string (e.g., "controller_input").
    """

    def __init__(self, *, network_message: Optional[NetworkMessage] = None, raw: Optional[Dict[str, Any]] = None):
        self._nm = network_message
        self._raw = raw or {}
        if self._nm is not None:
            # NetworkMessage keeps the enum value via model config
            self.type = str(self._nm.message_type)
        else:
            # Fallback: accept legacy schema with 'type'
            self.type = str(self._raw.get("type", ""))

    def get_controller_data(self) -> Optional[ControllerInputData]:
        """Return ControllerInputData if present, otherwise None."""
        if self._nm is not None:
            return self._nm.get_controller_input_data()

        # Legacy/loose schema path: expect controller input under 'data'
        if self.type == "controller_input" and isinstance(self._raw.get("data"), dict):
            try:
                return ControllerInputData.model_validate(self._raw["data"])
            except Exception:
                return None
        return None


class MessageProtocol:
    """Helper API compatibility layer around NetworkMessage."""

    @staticmethod
    def create_controller_input_message(input_data: ControllerInputData, message_id: Optional[str] = None) -> NetworkMessage:
        return NetworkMessage.create_controller_input_message(input_data, message_id=message_id)

    @staticmethod
    def parse_message(json_str: str) -> _ProtocolParsedMessage:
        """Parse a JSON string into a protocol message wrapper.

        Accepts both the canonical `NetworkMessage` JSON and a looser legacy
        format with fields `type` and `data`.
        """
        # First try to recognize the canonical schema fast path
        try:
            obj = json.loads(json_str)
        except json.JSONDecodeError:
            # Re-raise JSON error as tests may expect it
            raise

        if isinstance(obj, dict) and ("message_type" in obj or "payload" in obj):
            # Validate via Pydantic to ensure consistent types
            nm = NetworkMessage.from_json(json_str)
            return _ProtocolParsedMessage(network_message=nm)

        # Legacy/loose format: keep minimal info for tests that only assert `.type`
        if isinstance(obj, dict) and "type" in obj:
            return _ProtocolParsedMessage(raw=obj)

        # Unknown structure
        raise ValueError("Invalid message format")


__all__ = [
    "MessageType",
    "NetworkMessage",
    "MessageProtocol",
]
