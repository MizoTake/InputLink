"""Message protocol for network communication."""

import logging
import uuid
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
