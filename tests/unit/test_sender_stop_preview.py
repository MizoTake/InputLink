"""Tests for sender stop and preview restart functionality."""

import asyncio
from unittest.mock import MagicMock, Mock, patch

import pytest

from input_link.apps.sender import SenderApp
from input_link.core import ControllerManager
from input_link.models import ConfigModel, SenderConfig, ReceiverConfig


@pytest.mark.asyncio
async def test_sender_stop_callback_has_controller_manager_access():
    """Test that status callback is called before controller_manager is cleared."""

    # Track callback invocations
    callback_data = {"status": None, "controller_manager_available": False}

    def status_callback(status: str):
        callback_data["status"] = status
        # Check if controller_manager is still available when callback is called
        if sender_app.controller_manager is not None:
            callback_data["controller_manager_available"] = True

    # Create config
    config = ConfigModel(
        sender_config=SenderConfig(
            receiver_host="127.0.0.1",
            receiver_port=8765,
        ),
        receiver_config=ReceiverConfig(),
    )

    # Create sender app with cleanup disabled (GUI mode)
    sender_app = SenderApp(
        status_callback=status_callback,
        cleanup_controller_manager=False,
    )
    sender_app.config = config

    # Mock components to avoid actual pygame initialization
    with patch('input_link.apps.sender.ControllerManager') as mock_cm_class, \
         patch('input_link.apps.sender.InputCaptureEngine') as mock_ice_class, \
         patch('input_link.apps.sender.WebSocketClient') as mock_ws_class:

        # Setup mocks
        mock_cm = Mock()
        mock_cm.initialize = Mock()
        mock_cm.scan_controllers = Mock(return_value=[])
        mock_cm.get_connected_controllers = Mock(return_value=[])
        mock_cm_class.return_value = mock_cm

        mock_ice = Mock()
        mock_ice.start_capture = Mock()
        mock_ice.stop_capture = Mock()
        mock_ice_class.return_value = mock_ice

        mock_ws = Mock()
        mock_ws.start = Mock(return_value=asyncio.Future())
        mock_ws.start.return_value.set_result(None)
        mock_ws.stop = Mock(return_value=asyncio.Future())
        mock_ws.stop.return_value.set_result(None)
        mock_ws.connected = True
        mock_ws.send_message = Mock(return_value=asyncio.Future())
        mock_ws.send_message.return_value.set_result(None)
        mock_ws_class.return_value = mock_ws

        # Initialize components
        await sender_app._initialize_components()

        # Verify controller_manager is set
        assert sender_app.controller_manager is not None

        # Call cleanup
        await sender_app._cleanup()

        # Verify callback was called with "stopped"
        assert callback_data["status"] == "stopped"

        # Verify controller_manager was still available when callback was called
        assert callback_data["controller_manager_available"] is True

        # In GUI mode (cleanup disabled), controller_manager should be preserved for preview
        assert sender_app.controller_manager is not None


@pytest.mark.asyncio
async def test_sender_cleanup_order_preserves_controller_manager():
    """Test that controller_manager is preserved during status callback."""

    controller_manager_refs = []

    def status_callback(status: str):
        if status == "stopped":
            # Store reference to controller_manager when callback is called
            controller_manager_refs.append(sender_app.controller_manager)

    # Create config
    config = ConfigModel(
        sender_config=SenderConfig(
            receiver_host="127.0.0.1",
            receiver_port=8765,
        ),
        receiver_config=ReceiverConfig(),
    )

    # Create sender app with cleanup disabled (GUI mode)
    sender_app = SenderApp(
        status_callback=status_callback,
        cleanup_controller_manager=False,
    )
    sender_app.config = config

    # Mock components
    with patch('input_link.apps.sender.ControllerManager') as mock_cm_class, \
         patch('input_link.apps.sender.InputCaptureEngine') as mock_ice_class, \
         patch('input_link.apps.sender.WebSocketClient') as mock_ws_class:

        # Setup mocks
        mock_cm = Mock()
        mock_cm.initialize = Mock()
        mock_cm.scan_controllers = Mock(return_value=[])
        mock_cm.get_connected_controllers = Mock(return_value=[])
        mock_cm_class.return_value = mock_cm

        mock_ice = Mock()
        mock_ice.start_capture = Mock()
        mock_ice.stop_capture = Mock()
        mock_ice_class.return_value = mock_ice

        mock_ws = Mock()
        mock_ws.start = Mock(return_value=asyncio.Future())
        mock_ws.start.return_value.set_result(None)
        mock_ws.stop = Mock(return_value=asyncio.Future())
        mock_ws.stop.return_value.set_result(None)
        mock_ws.connected = True
        mock_ws.send_message = Mock(return_value=asyncio.Future())
        mock_ws.send_message.return_value.set_result(None)
        mock_ws_class.return_value = mock_ws

        # Initialize components
        await sender_app._initialize_components()

        # Call cleanup
        await sender_app._cleanup()

        # Verify callback was called and captured controller_manager reference
        assert len(controller_manager_refs) == 1
        assert controller_manager_refs[0] is not None
        assert controller_manager_refs[0] == mock_cm
        # And the controller_manager remains available after cleanup in GUI mode
        assert sender_app.controller_manager is not None
