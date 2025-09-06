"""Controller input data models with validation."""

from enum import Enum
from typing import Dict, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, computed_field


class InputMethod(str, Enum):
    """Supported controller input methods."""
    XINPUT = "xinput"
    DINPUT = "dinput"


class ButtonState(BaseModel):
    """Button state with validation."""
    
    a: bool = False
    b: bool = False  
    x: bool = False
    y: bool = False
    lb: bool = False
    rb: bool = False
    back: bool = False
    start: bool = False
    ls: bool = False  # left stick click
    rs: bool = False  # right stick click
    dpad_up: bool = False
    dpad_down: bool = False
    dpad_left: bool = False
    dpad_right: bool = False


class ControllerState(BaseModel):
    """Complete controller state with axis normalization."""
    
    left_stick_x: float = Field(default=0.0, ge=-1.0, le=1.0)
    left_stick_y: float = Field(default=0.0, ge=-1.0, le=1.0) 
    right_stick_x: float = Field(default=0.0, ge=-1.0, le=1.0)
    right_stick_y: float = Field(default=0.0, ge=-1.0, le=1.0)
    left_trigger: float = Field(default=0.0, ge=0.0, le=1.0)
    right_trigger: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @field_validator('left_stick_x', 'left_stick_y', 'right_stick_x', 'right_stick_y')
    @classmethod
    def clamp_stick_values(cls, v: float) -> float:
        """Ensure stick values are within valid range."""
        return max(-1.0, min(1.0, v))
    
    @field_validator('left_trigger', 'right_trigger') 
    @classmethod
    def clamp_trigger_values(cls, v: float) -> float:
        """Ensure trigger values are within valid range."""
        return max(0.0, min(1.0, v))


class ControllerInputData(BaseModel):
    """Complete controller input data packet for network transmission."""
    
    controller_number: int = Field(..., ge=1, le=8, description="Controller number assignment")
    controller_id: str = Field(..., min_length=1, description="Unique controller identifier")
    input_method: InputMethod = Field(default=InputMethod.XINPUT)
    buttons: ButtonState = Field(default_factory=ButtonState)
    axes: ControllerState = Field(default_factory=ControllerState)
    timestamp: Optional[float] = Field(default=None, description="Unix timestamp when input was captured")
    
    @computed_field
    @property  
    def capture_time(self) -> datetime:
        """Get capture time as datetime object."""
        if self.timestamp is None:
            return datetime.now()
        return datetime.fromtimestamp(self.timestamp)
    
    @field_validator('controller_id')
    @classmethod
    def validate_controller_id(cls, v: str) -> str:
        """Ensure controller ID is valid."""
        if not v or v.isspace():
            raise ValueError("Controller ID cannot be empty or whitespace")
        return v.strip()
    
    def model_post_init(self, __context) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()
    
    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "use_enum_values": True,
    }