"""Tests for controller manager."""

from unittest.mock import Mock, patch

import pytest

from input_link.core import ControllerManager, DetectedController
from input_link.core.controller_manager import ControllerConnectionState
from input_link.models import InputMethod


class TestDetectedController:
    """Test detected controller data class."""

    def test_identifier_generation(self):
        """Should generate unique identifier."""
        controller = DetectedController(
            pygame_id=0,
            device_id=12345,
            name="Xbox Controller",
            guid="abc123",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
        )

        assert controller.identifier == "abc123_12345"

    def test_xbox_controller_detection(self):
        """Should detect Xbox controllers."""
        xbox_names = [
            "Xbox 360 Controller",
            "Xbox One Controller",
            "Microsoft X-Box 360 pad",
            "xinput device",
        ]

        for name in xbox_names:
            controller = DetectedController(
                pygame_id=0, device_id=1, name=name, guid="test",
                num_axes=6, num_buttons=14, num_hats=1,
            )
            assert controller.is_xbox_controller()
            assert not controller.is_playstation_controller()

    def test_playstation_controller_detection(self):
        """Should detect PlayStation controllers."""
        ps_names = [
            "Sony DualShock 4",
            "PlayStation 3 Controller",
            "PS5 Controller",
            "DualSense Wireless Controller",
        ]

        for name in ps_names:
            controller = DetectedController(
                pygame_id=0, device_id=1, name=name, guid="test",
                num_axes=6, num_buttons=14, num_hats=1,
            )
            assert controller.is_playstation_controller()
            assert not controller.is_xbox_controller()

    def test_input_method_recommendation(self):
        """Should recommend appropriate input method."""
        xbox_controller = DetectedController(
            pygame_id=0, device_id=1, name="Xbox 360 Controller", guid="test",
            num_axes=6, num_buttons=14, num_hats=1,
        )
        assert xbox_controller.get_recommended_input_method() == InputMethod.XINPUT

        ps_controller = DetectedController(
            pygame_id=0, device_id=1, name="DualShock 4", guid="test",
            num_axes=6, num_buttons=14, num_hats=1,
        )
        assert ps_controller.get_recommended_input_method() == InputMethod.DINPUT


class TestControllerManager:
    """Test controller manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ControllerManager()

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self.manager, "_initialized") and self.manager._initialized:
            self.manager.cleanup()

    @patch("pygame.init")
    @patch("pygame.joystick.init")
    def test_initialization(self, mock_joystick_init, mock_pygame_init):
        """Should initialize pygame correctly."""
        # Mock pygame.init() to return (success_count, failure_count) with no failures
        mock_pygame_init.return_value = (7, 0)  # All modules successful

        self.manager.initialize()

        mock_pygame_init.assert_called_once()
        mock_joystick_init.assert_called_once()
        assert self.manager._initialized

    @patch("pygame.init")
    @patch("pygame.joystick.init")
    def test_initialization_failure(self, mock_joystick_init, mock_pygame_init):
        """Should handle initialization failure."""
        # Mock pygame.init() to return (success_count, failure_count) with failures
        mock_pygame_init.return_value = (5, 2)  # 5 successful, 2 failed modules

        with pytest.raises(RuntimeError, match="Pygame initialization failed: 2 modules failed"):
            self.manager.initialize()

    @patch("pygame.joystick.get_count", return_value=2)
    @patch("pygame.joystick.Joystick")
    def test_scan_controllers_success(self, mock_joystick_class, mock_get_count):
        """Should scan and detect controllers successfully."""
        # Mock joysticks
        mock_joystick1 = Mock()
        mock_joystick1.get_instance_id.return_value = 1
        mock_joystick1.get_name.return_value = "Xbox 360 Controller"
        mock_joystick1.get_guid.return_value = "abc123"
        mock_joystick1.get_numaxes.return_value = 6
        mock_joystick1.get_numbuttons.return_value = 14
        mock_joystick1.get_numhats.return_value = 1

        mock_joystick2 = Mock()
        mock_joystick2.get_instance_id.return_value = 2
        mock_joystick2.get_name.return_value = "DualShock 4"
        mock_joystick2.get_guid.return_value = "def456"
        mock_joystick2.get_numaxes.return_value = 6
        mock_joystick2.get_numbuttons.return_value = 14
        mock_joystick2.get_numhats.return_value = 1

        mock_joystick_class.side_effect = [mock_joystick1, mock_joystick2]

        with patch.object(self.manager, "initialize"):
            controllers = self.manager.scan_controllers()

        assert len(controllers) == 2
        assert controllers[0].name == "Xbox 360 Controller"
        assert controllers[1].name == "DualShock 4"
        assert controllers[0].assigned_number == 1
        assert controllers[1].assigned_number == 2

    @patch("pygame.joystick.get_count", return_value=1)
    @patch("pygame.joystick.Joystick")
    def test_scan_controllers_with_error(self, mock_joystick_class, mock_get_count):
        """Should handle joystick access errors by letting exception propagate."""
        # Mock pygame.error instead of generic Exception
        import pygame
        mock_joystick_class.side_effect = pygame.error("Joystick access failed")

        with patch.object(self.manager, "initialize"):
            # According to project rules, errors should propagate instead of being caught
            with pytest.raises(pygame.error, match="Joystick access failed"):
                self.manager.scan_controllers()

    def test_controller_number_assignment(self):
        """Should assign and manage controller numbers."""
        # Create mock controller
        controller = DetectedController(
            pygame_id=0, device_id=1, name="Test Controller", guid="test_guid",
            num_axes=6, num_buttons=14, num_hats=1,
        )

        self.manager._controllers[0] = controller

        # Test assignment
        success = self.manager.assign_controller_number("test_guid_1", 3)
        assert success
        assert controller.assigned_number == 3
        assert 3 in self.manager._assigned_numbers

    def test_controller_number_assignment_invalid_number(self):
        """Should reject invalid controller numbers."""
        success = self.manager.assign_controller_number("test", 0)
        assert not success

    def test_controller_number_assignment_nonexistent_controller(self):
        """Should handle nonexistent controller gracefully."""
        success = self.manager.assign_controller_number("nonexistent", 1)
        assert not success

    def test_input_method_setting(self):
        """Should set input method for controllers."""
        controller = DetectedController(
            pygame_id=0, device_id=1, name="Test Controller", guid="test_guid",
            num_axes=6, num_buttons=14, num_hats=1,
        )

        self.manager._controllers[0] = controller

        success = self.manager.set_input_method("test_guid_1", InputMethod.DINPUT)
        assert success
        assert controller.preferred_input_method == InputMethod.DINPUT

    def test_get_connected_controllers(self):
        """Should return only connected controllers."""
        controller1 = DetectedController(
            pygame_id=0, device_id=1, name="Controller 1", guid="guid1",
            num_axes=6, num_buttons=14, num_hats=1,
            state=ControllerConnectionState.CONNECTED,
        )

        controller2 = DetectedController(
            pygame_id=1, device_id=2, name="Controller 2", guid="guid2",
            num_axes=6, num_buttons=14, num_hats=1,
            state=ControllerConnectionState.DISCONNECTED,
        )

        self.manager._controllers[0] = controller1
        self.manager._controllers[1] = controller2

        connected = self.manager.get_connected_controllers()
        assert len(connected) == 1
        assert connected[0] == controller1

    def test_next_available_number(self):
        """Should find next available controller number."""
        # Assign some numbers
        self.manager._assigned_numbers = {1, 3, 5}

        next_num = self.manager._get_next_available_number()
        assert next_num == 2

    def test_next_available_number_large_numbers(self):
        """Should handle large controller numbers correctly."""
        self.manager._assigned_numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

        next_num = self.manager._get_next_available_number()
        assert next_num == 11

    @patch("pygame.joystick.quit")
    @patch("pygame.quit")
    def test_cleanup(self, mock_pygame_quit, mock_joystick_quit):
        """Should cleanup resources properly."""
        self.manager._initialized = True

        self.manager.cleanup()

        mock_joystick_quit.assert_called_once()
        mock_pygame_quit.assert_called_once()
        assert not self.manager._initialized

    @patch("pygame.joystick.get_count")
    @patch("pygame.joystick.Joystick")
    def test_rescan_controllers_consistency(self, mock_joystick_class, mock_get_count):
        """Should return consistent results on multiple scans."""
        # First scan - controller present
        mock_get_count.return_value = 1
        mock_joystick = Mock()
        mock_joystick.get_instance_id.return_value = 1
        mock_joystick.get_name.return_value = "Test Controller"
        mock_joystick.get_guid.return_value = "test_guid"
        mock_joystick.get_numaxes.return_value = 6
        mock_joystick.get_numbuttons.return_value = 14
        mock_joystick.get_numhats.return_value = 1
        mock_joystick_class.return_value = mock_joystick

        with patch.object(self.manager, "initialize"):
            controllers_first = self.manager.scan_controllers()

        assert len(controllers_first) == 1
        assert controllers_first[0].state == ControllerConnectionState.CONNECTED

        # Second scan - same controller
        with patch.object(self.manager, "initialize"):
            controllers_second = self.manager.scan_controllers()

        assert len(controllers_second) == 1
        assert controllers_second[0].state == ControllerConnectionState.CONNECTED

        # Connected controllers should be the same
        connected_first = self.manager.get_connected_controllers()
        connected_second = self.manager.get_connected_controllers()
        assert len(connected_first) == 1
        assert len(connected_second) == 1
        assert connected_first[0].identifier == connected_second[0].identifier

    @patch("pygame.joystick.get_count")
    @patch("pygame.joystick.Joystick")
    def test_controller_disconnect_and_reconnect(self, mock_joystick_class, mock_get_count):
        """Should handle controller disconnect and reconnect properly."""
        # First scan - controller present
        mock_get_count.return_value = 1
        mock_joystick = Mock()
        mock_joystick.get_instance_id.return_value = 1
        mock_joystick.get_name.return_value = "Test Controller"
        mock_joystick.get_guid.return_value = "test_guid"
        mock_joystick.get_numaxes.return_value = 6
        mock_joystick.get_numbuttons.return_value = 14
        mock_joystick.get_numhats.return_value = 1
        mock_joystick_class.return_value = mock_joystick

        with patch.object(self.manager, "initialize"):
            controllers_first = self.manager.scan_controllers()

        assert len(controllers_first) == 1
        connected_first = self.manager.get_connected_controllers()
        assert len(connected_first) == 1

        # Second scan - controller disconnected
        mock_get_count.return_value = 0

        with patch.object(self.manager, "initialize"):
            controllers_second = self.manager.scan_controllers()

        # Should still have the controller in internal list but marked as disconnected
        assert len(controllers_second) == 1
        assert controllers_second[0].state == ControllerConnectionState.DISCONNECTED

        # Connected controllers should be empty
        connected_second = self.manager.get_connected_controllers()
        assert len(connected_second) == 0

        # Third scan - controller reconnected
        mock_get_count.return_value = 1

        with patch.object(self.manager, "initialize"):
            controllers_third = self.manager.scan_controllers()

        # Should have controller marked as connected again
        connected_third = self.manager.get_connected_controllers()
        assert len(connected_third) == 1
