"""Integration tests for controller scanning functionality."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from input_link.gui.application import AsyncWorker
from input_link.core import ControllerManager, DetectedController
from input_link.core.controller_manager import ControllerConnectionState


@pytest.fixture
def qt_app():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    if app:
        app.quit()


@pytest.fixture
def async_worker(qt_app):
    """Create AsyncWorker instance for tests."""
    worker = AsyncWorker()
    yield worker
    if hasattr(worker, 'controller_manager') and worker.controller_manager:
        worker.controller_manager.cleanup()


class TestControllerScanning:
    """Test controller scanning functionality in GUI context."""

    def test_scan_controllers_empty_result(self, async_worker):
        """Should handle empty controller scan correctly."""
        # Mock controller manager to return no controllers
        mock_manager = Mock(spec=ControllerManager)
        mock_manager.scan_controllers.return_value = []
        mock_manager.get_connected_controllers.return_value = []
        async_worker.controller_manager = mock_manager

        # Track emitted signals
        detected_controllers = []
        async_worker.controller_detected.connect(lambda c: detected_controllers.append(c))

        # Perform scan
        async_worker.scan_controllers()

        # Should emit empty list
        assert len(detected_controllers) == 1
        assert detected_controllers[0] == []

    def test_scan_controllers_with_results(self, async_worker):
        """Should handle controller scan with results correctly."""
        # Create mock controllers
        controller1 = DetectedController(
            pygame_id=0,
            device_id=1,
            name="Xbox 360 Controller",
            guid="abc123",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )

        controller2 = DetectedController(
            pygame_id=1,
            device_id=2,
            name="DualShock 4",
            guid="def456",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=2
        )

        # Mock controller manager
        mock_manager = Mock(spec=ControllerManager)
        mock_manager.scan_controllers.return_value = [controller1, controller2]
        mock_manager.get_connected_controllers.return_value = [controller1, controller2]
        async_worker.controller_manager = mock_manager

        # Track emitted signals
        detected_controllers = []
        async_worker.controller_detected.connect(lambda c: detected_controllers.append(c))

        # Perform scan
        async_worker.scan_controllers()

        # Should emit connected controllers
        assert len(detected_controllers) == 1
        assert len(detected_controllers[0]) == 2
        assert detected_controllers[0][0].name == "Xbox 360 Controller"
        assert detected_controllers[0][1].name == "DualShock 4"

    def test_rescan_controllers_filtering_disconnected(self, async_worker):
        """Should filter out disconnected controllers on rescan."""
        # Create mock controllers - one connected, one disconnected
        connected_controller = DetectedController(
            pygame_id=0,
            device_id=1,
            name="Xbox 360 Controller",
            guid="abc123",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )

        disconnected_controller = DetectedController(
            pygame_id=1,
            device_id=2,
            name="DualShock 4",
            guid="def456",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.DISCONNECTED,
            assigned_number=2
        )

        # Mock controller manager to return all controllers in scan but only connected in get_connected
        mock_manager = Mock(spec=ControllerManager)
        mock_manager.scan_controllers.return_value = [connected_controller, disconnected_controller]
        mock_manager.get_connected_controllers.return_value = [connected_controller]  # Only connected
        async_worker.controller_manager = mock_manager

        # Track emitted signals
        detected_controllers = []
        async_worker.controller_detected.connect(lambda c: detected_controllers.append(c))

        # Perform scan
        async_worker.scan_controllers()

        # Should emit only connected controllers
        assert len(detected_controllers) == 1
        assert len(detected_controllers[0]) == 1
        assert detected_controllers[0][0].name == "Xbox 360 Controller"
        assert detected_controllers[0][0].state == ControllerConnectionState.CONNECTED

    def test_multiple_scans_consistency(self, async_worker):
        """Should return consistent results on multiple scans."""
        # Create mock controller
        controller = DetectedController(
            pygame_id=0,
            device_id=1,
            name="Test Controller",
            guid="test123",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )

        # Mock controller manager to always return the same controller
        mock_manager = Mock(spec=ControllerManager)
        mock_manager.scan_controllers.return_value = [controller]
        mock_manager.get_connected_controllers.return_value = [controller]
        async_worker.controller_manager = mock_manager

        # Track emitted signals
        detected_controllers = []
        async_worker.controller_detected.connect(lambda c: detected_controllers.append(c))

        # Perform first scan
        async_worker.scan_controllers()

        # Perform second scan
        async_worker.scan_controllers()

        # Should have two scan results, both with same controller
        assert len(detected_controllers) == 2
        assert len(detected_controllers[0]) == 1
        assert len(detected_controllers[1]) == 1
        assert detected_controllers[0][0].identifier == detected_controllers[1][0].identifier
        assert detected_controllers[0][0].name == "Test Controller"
        assert detected_controllers[1][0].name == "Test Controller"

    @patch('input_link.gui.application.ControllerManager')
    def test_scan_controllers_initialization(self, mock_controller_manager_class, async_worker):
        """Should initialize ControllerManager if not present."""
        mock_manager = Mock(spec=ControllerManager)
        mock_manager.scan_controllers.return_value = []
        mock_manager.get_connected_controllers.return_value = []
        mock_controller_manager_class.return_value = mock_manager

        # Ensure no controller manager initially
        async_worker.controller_manager = None

        # Track emitted signals
        detected_controllers = []
        async_worker.controller_detected.connect(lambda c: detected_controllers.append(c))

        # Perform scan
        async_worker.scan_controllers()

        # Should create new controller manager
        mock_controller_manager_class.assert_called_once()
        mock_manager.initialize.assert_called_once()
        mock_manager.scan_controllers.assert_called_once()
        mock_manager.get_connected_controllers.assert_called_once()

        # Should emit empty result
        assert len(detected_controllers) == 1
        assert detected_controllers[0] == []


class TestControllerManagerIntegration:
    """Test ControllerManager behavior in integration context."""

    def test_scan_returns_all_but_get_connected_filters(self):
        """Should demonstrate the difference between scan_controllers and get_connected_controllers."""
        manager = ControllerManager()

        # Mock pygame to simulate one controller that gets disconnected
        with patch('pygame.joystick.get_count', return_value=1), \
             patch('pygame.joystick.Joystick') as mock_joystick_class:

            # Setup mock joystick
            mock_joystick = Mock()
            mock_joystick.get_instance_id.return_value = 1
            mock_joystick.get_name.return_value = "Test Controller"
            mock_joystick.get_guid.return_value = "test_guid"
            mock_joystick.get_numaxes.return_value = 6
            mock_joystick.get_numbuttons.return_value = 14
            mock_joystick.get_numhats.return_value = 1
            mock_joystick_class.return_value = mock_joystick

            with patch.object(manager, 'initialize'):
                # First scan - controller present
                controllers = manager.scan_controllers()

            assert len(controllers) == 1
            assert controllers[0].state == ControllerConnectionState.CONNECTED

            connected = manager.get_connected_controllers()
            assert len(connected) == 1

        # Second scan - no controllers found
        with patch('pygame.joystick.get_count', return_value=0):
            with patch.object(manager, 'initialize'):
                controllers = manager.scan_controllers()

        # scan_controllers returns all (including disconnected)
        assert len(controllers) == 1
        assert controllers[0].state == ControllerConnectionState.DISCONNECTED

        # get_connected_controllers filters to only connected
        connected = manager.get_connected_controllers()
        assert len(connected) == 0

        manager.cleanup()