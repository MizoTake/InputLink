"""Tests for data models."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json

from input_link.models import (
    ControllerInputData,
    ButtonState, 
    ControllerState,
    ConfigModel,
    SenderConfig,
    ReceiverConfig,
    InputMethod
)


class TestButtonState:
    """Test button state model."""
    
    def test_default_all_false(self):
        """All buttons should default to False."""
        buttons = ButtonState()
        assert not buttons.a
        assert not buttons.b
        assert not buttons.dpad_up
        
    def test_explicit_button_states(self):
        """Should accept explicit button states."""
        buttons = ButtonState(a=True, x=True, dpad_left=True)
        assert buttons.a
        assert buttons.x  
        assert buttons.dpad_left
        assert not buttons.b


class TestControllerState:
    """Test controller axis state model."""
    
    def test_default_values(self):
        """All axes should default to 0.0."""
        state = ControllerState()
        assert state.left_stick_x == 0.0
        assert state.left_trigger == 0.0
        
    def test_stick_value_validation(self):
        """Stick values should validate within range [-1, 1]."""
        # Valid values should work
        state = ControllerState(
            left_stick_x=0.5,
            left_stick_y=-0.8,
            right_stick_x=1.0,
            right_stick_y=-1.0
        )
        assert state.left_stick_x == 0.5
        assert state.left_stick_y == -0.8
        
        # Invalid values should raise validation error
        with pytest.raises(ValueError):
            ControllerState(left_stick_x=2.0)
            
        with pytest.raises(ValueError):
            ControllerState(left_stick_y=-5.0)
        
    def test_trigger_value_validation(self):
        """Trigger values should validate within range [0, 1]."""
        # Valid values should work
        state = ControllerState(
            left_trigger=0.0,
            right_trigger=1.0
        )
        assert state.left_trigger == 0.0
        assert state.right_trigger == 1.0
        
        # Invalid values should raise validation error
        with pytest.raises(ValueError):
            ControllerState(left_trigger=-0.5)
            
        with pytest.raises(ValueError):
            ControllerState(right_trigger=2.0)
        
    def test_invalid_range_validation(self):
        """Should validate ranges in Pydantic validation."""
        with pytest.raises(ValueError):
            ControllerState.model_validate({'left_stick_x': 'invalid'})


class TestControllerInputData:
    """Test controller input data model."""
    
    def test_minimal_valid_data(self):
        """Should create with minimal required fields."""
        data = ControllerInputData(
            controller_number=1,
            controller_id="test_controller"
        )
        assert data.controller_number == 1
        assert data.controller_id == "test_controller"
        assert data.input_method == InputMethod.XINPUT
        assert isinstance(data.timestamp, float)
        
    def test_controller_number_validation(self):
        """Should validate controller number range."""
        with pytest.raises(ValueError):
            ControllerInputData(controller_number=0, controller_id="test")
            
        with pytest.raises(ValueError):
            ControllerInputData(controller_number=9, controller_id="test")
            
    def test_controller_id_validation(self):
        """Should validate controller ID."""
        with pytest.raises(ValueError):
            ControllerInputData(controller_number=1, controller_id="")
            
        with pytest.raises(ValueError):
            ControllerInputData(controller_number=1, controller_id="   ")
            
    def test_controller_id_stripping(self):
        """Should strip whitespace from controller ID."""
        data = ControllerInputData(
            controller_number=1,
            controller_id="  test_controller  "
        )
        assert data.controller_id == "test_controller"
        
    def test_timestamp_auto_generation(self):
        """Should auto-generate timestamp if not provided."""
        before = datetime.now().timestamp()
        data = ControllerInputData(
            controller_number=1,
            controller_id="test"
        )
        after = datetime.now().timestamp()
        
        assert before <= data.timestamp <= after
        
    def test_capture_time_property(self):
        """Should provide datetime property."""
        timestamp = datetime.now().timestamp()
        data = ControllerInputData(
            controller_number=1,
            controller_id="test",
            timestamp=timestamp
        )
        
        capture_time = data.capture_time
        assert isinstance(capture_time, datetime)
        assert abs((capture_time.timestamp() - timestamp)) < 0.001
        
    def test_json_serialization(self):
        """Should serialize to/from JSON correctly."""
        original = ControllerInputData(
            controller_number=2,
            controller_id="xbox_360",
            input_method=InputMethod.DINPUT,
            buttons=ButtonState(a=True, b=True),
            axes=ControllerState(left_stick_x=0.5, left_trigger=0.8)
        )
        
        json_str = original.model_dump_json()
        deserialized = ControllerInputData.model_validate_json(json_str)
        
        assert deserialized.controller_number == original.controller_number
        assert deserialized.controller_id == original.controller_id
        assert deserialized.input_method == original.input_method
        assert deserialized.buttons.a == original.buttons.a
        assert deserialized.axes.left_stick_x == original.axes.left_stick_x


class TestSenderConfig:
    """Test sender configuration model."""
    
    def test_ip_address_validation(self):
        """Should validate IP addresses."""
        config = SenderConfig(receiver_host="192.168.1.100")
        assert config.receiver_host == "192.168.1.100"
        
    def test_hostname_validation(self):
        """Should validate hostnames."""
        config = SenderConfig(receiver_host="my-computer.local")
        assert config.receiver_host == "my-computer.local"
        
    def test_invalid_host_rejection(self):
        """Should reject invalid hosts."""
        with pytest.raises(ValueError):
            SenderConfig(receiver_host="")
            
        with pytest.raises(ValueError):
            SenderConfig(receiver_host="invalid@host")
            
    def test_port_range_validation(self):
        """Should validate port ranges."""
        with pytest.raises(ValueError):
            SenderConfig(receiver_host="127.0.0.1", receiver_port=1023)
            
        with pytest.raises(ValueError): 
            SenderConfig(receiver_host="127.0.0.1", receiver_port=65536)


class TestConfigModel:
    """Test main configuration model."""
    
    def test_default_creation(self):
        """Should create valid default config."""
        config = ConfigModel.create_default()
        assert config.sender_config.receiver_host == "127.0.0.1"
        assert config.receiver_config.listen_port == 8765
        
    def test_port_consistency_validation(self):
        """Should validate port consistency for localhost."""
        with pytest.raises(ValueError):
            ConfigModel(
                sender_config=SenderConfig(
                    receiver_host="127.0.0.1",
                    receiver_port=8765
                ),
                receiver_config=ReceiverConfig(listen_port=9999)
            )
            
    def test_file_save_load_roundtrip(self):
        """Should save and load from file correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            
            original = ConfigModel.create_default()
            original.debug_logging = True
            original.save_to_file(config_path)
            
            loaded = ConfigModel.load_from_file(config_path)
            
            assert loaded.debug_logging == original.debug_logging
            assert loaded.sender_config.receiver_host == original.sender_config.receiver_host
            
    def test_nonexistent_file_creates_default(self):
        """Should create default config for nonexistent file.""" 
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent.json"
            
            config = ConfigModel.load_from_file(config_path)
            
            assert config_path.exists()
            assert config.sender_config.receiver_host == "127.0.0.1"