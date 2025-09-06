"""Tests for input capture engine."""

import time
from unittest.mock import Mock, patch

from input_link.core import ControllerManager, DetectedController, InputCaptureEngine
from input_link.core.input_capture import InputCaptureConfig
from input_link.models import ButtonState, ControllerInputData, ControllerState


class TestInputCaptureConfig:
    """Test input capture configuration."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = InputCaptureConfig()

        assert config.polling_rate == 60
        assert config.dead_zone == 0.1
        assert config.enable_button_repeat is False
        assert config.max_queue_size == 1000


class TestInputCaptureEngine:
    """Test input capture engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller_manager = Mock(spec=ControllerManager)
        self.engine = InputCaptureEngine(self.mock_controller_manager)

        # Create mock controller
        self.mock_controller = DetectedController(
            pygame_id=0,
            device_id=1,
            name="Test Controller",
            guid="test_guid",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            assigned_number=1,
        )

    def teardown_method(self):
        """Clean up after tests."""
        if self.engine._running:
            self.engine.stop_capture()

    def test_initialization(self):
        """Should initialize with correct defaults."""
        assert not self.engine._running
        assert self.engine._config.polling_rate == 60
        assert self.engine._input_queue.maxsize == 1000

    def test_start_capture(self):
        """Should start capture thread."""
        self.engine.start_capture()

        assert self.engine._running
        assert self.engine._capture_thread is not None
        assert self.engine._capture_thread.is_alive()

        # Stop to cleanup
        self.engine.stop_capture()

    def test_stop_capture(self):
        """Should stop capture thread cleanly."""
        self.engine.start_capture()
        assert self.engine._running

        self.engine.stop_capture()

        assert not self.engine._running
        # Give thread time to stop
        time.sleep(0.1)
        assert not self.engine._capture_thread.is_alive()

    def test_double_start_prevention(self):
        """Should prevent double start."""
        self.engine.start_capture()

        # Try to start again
        with patch("logging.Logger.warning") as mock_warning:
            self.engine.start_capture()
            mock_warning.assert_called_with("Input capture is already running")

        self.engine.stop_capture()

    def test_get_input_data_timeout(self):
        """Should timeout when no data available."""
        data = self.engine.get_input_data(timeout=0.001)
        assert data is None

    def test_get_input_data_with_data(self):
        """Should return queued input data."""
        # Create test input data
        test_data = ControllerInputData(
            controller_number=1,
            controller_id="test_controller",
        )

        # Manually add to queue
        self.engine._input_queue.put(test_data)

        retrieved_data = self.engine.get_input_data(timeout=0.1)
        assert retrieved_data is not None
        assert retrieved_data.controller_number == 1
        assert retrieved_data.controller_id == "test_controller"

    def test_dead_zone_application(self):
        """Should apply dead zone correctly."""
        config = InputCaptureConfig(dead_zone=0.2)
        engine = InputCaptureEngine(self.mock_controller_manager, config)

        # Test values within dead zone
        assert engine._apply_dead_zone(0.1) == 0.0
        assert engine._apply_dead_zone(-0.15) == 0.0

        # Test values outside dead zone
        result = engine._apply_dead_zone(0.5)
        assert result > 0.0
        assert result < 0.5  # Should be scaled

        result = engine._apply_dead_zone(-0.8)
        assert result < 0.0
        assert result > -0.8  # Should be scaled

    def test_dead_zone_full_range_preservation(self):
        """Should preserve full range after dead zone."""
        config = InputCaptureConfig(dead_zone=0.2)
        engine = InputCaptureEngine(self.mock_controller_manager, config)

        # Test maximum values
        assert abs(engine._apply_dead_zone(1.0) - 1.0) < 0.01
        assert abs(engine._apply_dead_zone(-1.0) - (-1.0)) < 0.01

    @patch("pygame.joystick.Joystick")
    def test_button_state_capture(self, mock_joystick_class):
        """Should capture button states correctly."""
        mock_joystick = Mock()
        mock_joystick.get_numbuttons.return_value = 10
        mock_joystick.get_numhats.return_value = 1

        # Mock button states (A and X pressed)
        def mock_get_button(index):
            return index in [0, 2]  # A and X buttons
        mock_joystick.get_button.side_effect = mock_get_button

        # Mock hat state (up pressed)
        mock_joystick.get_hat.return_value = (0, 1)

        buttons = self.engine._capture_button_state(mock_joystick)

        assert buttons.a is True
        assert buttons.b is False
        assert buttons.x is True
        assert buttons.y is False
        assert buttons.dpad_up is True
        assert buttons.dpad_down is False

    @patch("pygame.joystick.Joystick")
    def test_axis_state_capture(self, mock_joystick_class):
        """Should capture axis states correctly."""
        mock_joystick = Mock()
        mock_joystick.get_numaxes.return_value = 6

        # Mock axis values
        axis_values = [0.5, -0.3, 0.8, -0.1, 0.0, 1.0]  # LX, LY, RX, RY, LT, RT
        mock_joystick.get_axis.side_effect = lambda i: axis_values[i]

        axes = self.engine._capture_axis_state(mock_joystick)

        # Check stick values (Y should be inverted, and dead zone applied)
        # Note: Dead zone scaling affects values
        expected_lx = self.engine._apply_dead_zone(0.5)
        expected_ly = -self.engine._apply_dead_zone(-0.3)  # Inverted
        expected_rx = self.engine._apply_dead_zone(0.8)
        expected_ry = -self.engine._apply_dead_zone(-0.1)  # Inverted

        assert abs(axes.left_stick_x - expected_lx) < 0.01
        assert abs(axes.left_stick_y - expected_ly) < 0.01
        assert abs(axes.right_stick_x - expected_rx) < 0.01
        assert abs(axes.right_stick_y - expected_ry) < 0.01

        # Check trigger values (converted from [-1,1] to [0,1])
        assert axes.left_trigger == 0.5  # (0 + 1) / 2
        assert axes.right_trigger == 1.0  # (1 + 1) / 2

    def test_state_change_detection_buttons(self):
        """Should detect button state changes."""
        # Create two input data with different button states
        data1 = ControllerInputData(
            controller_number=1,
            controller_id="test",
            buttons=ButtonState(a=False, b=False),
        )

        data2 = ControllerInputData(
            controller_number=1,
            controller_id="test",
            buttons=ButtonState(a=True, b=False),  # A button pressed
        )

        assert self.engine._state_changed(data1, data2)

    def test_state_change_detection_axes(self):
        """Should detect axis state changes."""
        # Create two input data with different axis states
        data1 = ControllerInputData(
            controller_number=1,
            controller_id="test",
            axes=ControllerState(left_stick_x=0.0),
        )

        data2 = ControllerInputData(
            controller_number=1,
            controller_id="test",
            axes=ControllerState(left_stick_x=0.5),  # Stick moved
        )

        assert self.engine._state_changed(data1, data2)

    def test_state_change_detection_no_change(self):
        """Should not detect change when states are identical."""
        data1 = ControllerInputData(
            controller_number=1,
            controller_id="test",
            buttons=ButtonState(a=True),
            axes=ControllerState(left_stick_x=0.5),
        )

        data2 = ControllerInputData(
            controller_number=1,
            controller_id="test",
            buttons=ButtonState(a=True),
            axes=ControllerState(left_stick_x=0.5),
        )

        assert not self.engine._state_changed(data1, data2)

    def test_state_change_detection_small_axis_change(self):
        """Should ignore very small axis changes (noise)."""
        data1 = ControllerInputData(
            controller_number=1,
            controller_id="test",
            axes=ControllerState(left_stick_x=0.5000),
        )

        data2 = ControllerInputData(
            controller_number=1,
            controller_id="test",
            axes=ControllerState(left_stick_x=0.5005),  # Very small change
        )

        assert not self.engine._state_changed(data1, data2)

    def test_input_callback(self):
        """Should call input callback when provided."""
        callback_called = []

        def test_callback(data):
            callback_called.append(data)

        engine = InputCaptureEngine(
            self.mock_controller_manager,
            input_callback=test_callback,
        )

        # Manually trigger callback by adding data
        test_data = ControllerInputData(
            controller_number=1,
            controller_id="test",
        )

        # Simulate callback call
        engine._input_callback(test_data)

        assert len(callback_called) == 1
        assert callback_called[0] == test_data

    def test_queue_overflow_handling(self):
        """Should handle queue overflow gracefully."""
        # Create engine with small queue
        config = InputCaptureConfig(max_queue_size=2)
        engine = InputCaptureEngine(self.mock_controller_manager, config)

        # Fill queue beyond capacity
        for i in range(5):
            data = ControllerInputData(
                controller_number=1,
                controller_id=f"test_{i}",
            )
            try:
                engine._input_queue.put_nowait(data)
            except:
                # Queue full, this is expected
                pass

        # Should still be able to get data
        retrieved = engine.get_input_data(timeout=0.1)
        assert retrieved is not None
