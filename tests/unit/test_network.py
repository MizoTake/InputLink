"""Tests for network communication components."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from input_link.models import ButtonState, ControllerInputData, ControllerState
from input_link.network import MessageType, NetworkMessage, WebSocketClient, WebSocketServer


class TestMessageProtocol:
    """Test network message protocol."""

    def test_controller_input_message_creation(self):
        """Should create controller input message correctly."""
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test_controller",
            buttons=ButtonState(a=True),
            axes=ControllerState(left_stick_x=0.5),
        )

        message = NetworkMessage.create_controller_input_message(input_data)

        assert message.message_type == MessageType.CONTROLLER_INPUT
        assert message.message_id is not None
        assert "controller_number" in message.payload
        assert message.payload["controller_number"] == 1

    def test_status_request_message_creation(self):
        """Should create status request message correctly."""
        message = NetworkMessage.create_status_request_message()

        assert message.message_type == MessageType.STATUS_REQUEST
        assert message.message_id is not None
        assert message.payload == {}

    def test_status_response_message_creation(self):
        """Should create status response message correctly."""
        message = NetworkMessage.create_status_response_message(
            active_controllers=2,
            connection_status="connected",
        )

        assert message.message_type == MessageType.STATUS_RESPONSE
        assert message.payload["active_controllers"] == 2
        assert message.payload["connection_status"] == "connected"
        assert "server_time" in message.payload

    def test_error_message_creation(self):
        """Should create error message correctly."""
        message = NetworkMessage.create_error_message(
            error_code="INVALID_INPUT",
            error_description="Controller input validation failed",
        )

        assert message.message_type == MessageType.ERROR
        assert message.payload["error_code"] == "INVALID_INPUT"
        assert message.payload["error_description"] == "Controller input validation failed"

    def test_heartbeat_message_creation(self):
        """Should create heartbeat message correctly."""
        message = NetworkMessage.create_heartbeat_message()

        assert message.message_type == MessageType.HEARTBEAT
        assert message.message_id is not None
        assert message.payload == {}

    def test_json_serialization_roundtrip(self):
        """Should serialize and deserialize correctly."""
        original = NetworkMessage.create_status_request_message()

        json_str = original.to_json()
        deserialized = NetworkMessage.from_json(json_str)

        assert deserialized.message_id == original.message_id
        assert deserialized.message_type == original.message_type
        assert deserialized.payload == original.payload

    def test_controller_input_data_extraction(self):
        """Should extract controller input data from payload."""
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test_controller",
        )

        message = NetworkMessage.create_controller_input_message(input_data)
        extracted = message.get_controller_input_data()

        assert extracted is not None
        assert extracted.controller_number == 1
        assert extracted.controller_id == "test_controller"

    def test_controller_input_data_extraction_wrong_type(self):
        """Should return None for non-input messages."""
        message = NetworkMessage.create_status_request_message()
        extracted = message.get_controller_input_data()

        assert extracted is None

    def test_invalid_json_handling(self):
        """Should handle invalid JSON gracefully."""
        with pytest.raises(Exception):  # ValidationError from Pydantic
            NetworkMessage.from_json("invalid json")

    def test_custom_message_id(self):
        """Should accept custom message ID."""
        custom_id = "test-message-123"
        message = NetworkMessage.create_heartbeat_message(message_id=custom_id)

        assert message.message_id == custom_id


class TestWebSocketClient:
    """Test WebSocket client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = WebSocketClient(
            host="localhost",
            port=8765,
            reconnect_interval=0.1,
            max_reconnect_attempts=3,
        )

    def teardown_method(self):
        """Clean up after tests."""
        # Ensure client is stopped
        if hasattr(self.client, "_running") and self.client._running:
            asyncio.run(self.client.stop())

    def test_uri_property(self):
        """Should generate correct WebSocket URI."""
        assert self.client.uri == "ws://localhost:8765"

    def test_connected_property_no_websocket(self):
        """Should return False when no websocket connection."""
        assert not self.client.connected

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self):
        """Should handle start/stop lifecycle correctly."""
        # Mock websockets.connect to avoid actual connection
        with patch("websockets.connect") as mock_connect:
            mock_websocket = AsyncMock()
            mock_websocket.closed = False
            mock_websocket.wait_closed = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            mock_connect.return_value.__aexit__.return_value = None

            await self.client.start()
            assert self.client._running

            await asyncio.sleep(0.01)  # Let connection task start

            await self.client.stop()
            assert not self.client._running

    @pytest.mark.asyncio
    async def test_send_controller_input_not_running(self):
        """Should reject input when not running."""
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test",
        )

        success = await self.client.send_controller_input(input_data)
        assert not success

    @pytest.mark.asyncio
    async def test_send_controller_input_queuing(self):
        """Should queue controller input when running."""
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test",
        )

        self.client._running = True
        success = await self.client.send_controller_input(input_data)
        assert success

        # Check queue has message
        assert not self.client._message_queue.empty()
        message = await self.client._message_queue.get()
        assert message.message_type == MessageType.CONTROLLER_INPUT

    @pytest.mark.asyncio
    async def test_send_message_queuing(self):
        """Should queue network messages when running."""
        message = NetworkMessage.create_heartbeat_message()

        self.client._running = True
        success = await self.client.send_message(message)
        assert success

        # Check queue has message
        assert not self.client._message_queue.empty()
        queued_message = await self.client._message_queue.get()
        assert queued_message.message_id == message.message_id

    @pytest.mark.asyncio
    async def test_message_callback(self):
        """Should call message callback when provided."""
        received_messages = []

        def callback(message):
            received_messages.append(message)

        client = WebSocketClient(
            host="localhost",
            port=8765,
            message_callback=callback,
        )

        # Simulate receiving a message
        test_message = NetworkMessage.create_heartbeat_message()
        client._message_callback(test_message)

        assert len(received_messages) == 1
        assert received_messages[0].message_id == test_message.message_id

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Should work as async context manager."""
        with patch("websockets.connect") as mock_connect:
            mock_websocket = AsyncMock()
            mock_websocket.closed = False
            mock_websocket.wait_closed = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            mock_connect.return_value.__aexit__.return_value = None

            async with self.client as client:
                assert client._running

            assert not client._running

    @pytest.mark.asyncio
    async def test_safe_queue_put_not_running(self):
        """Should fail to queue when not running."""
        message = NetworkMessage.create_heartbeat_message()

        result = await self.client._safe_queue_put(message)
        assert not result

    @pytest.mark.asyncio
    async def test_safe_queue_put_queue_full(self):
        """Should fail when queue is full."""
        # Fill the queue to capacity
        self.client._running = True
        message = NetworkMessage.create_heartbeat_message()

        # Fill queue to max capacity
        for _ in range(self.client._max_queue_size):
            await self.client._message_queue.put(message)

        # Should fail to add more
        result = await self.client._safe_queue_put(message)
        assert not result

    @pytest.mark.asyncio
    async def test_safe_queue_put_success(self):
        """Should successfully queue message."""
        self.client._running = True
        message = NetworkMessage.create_heartbeat_message()

        result = await self.client._safe_queue_put(message)
        assert result

        # Verify message was queued
        queued_message = await self.client._message_queue.get()
        assert queued_message.message_id == message.message_id

    @pytest.mark.asyncio
    async def test_safe_queue_get_not_running(self):
        """Should return None when not running."""
        result = await self.client._safe_queue_get(timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_queue_get_timeout(self):
        """Should return None on timeout."""
        self.client._running = True

        result = await self.client._safe_queue_get(timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_queue_get_success(self):
        """Should return message when available."""
        self.client._running = True
        message = NetworkMessage.create_heartbeat_message()

        # Put message in queue
        await self.client._message_queue.put(message)

        result = await self.client._safe_queue_get(timeout=1.0)
        assert result is not None
        assert result.message_id == message.message_id

    @pytest.mark.asyncio
    async def test_send_controller_input_queue_full_check(self):
        """Should check queue capacity before queuing controller input."""
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test",
        )

        self.client._running = True

        # Fill queue to capacity
        dummy_message = NetworkMessage.create_heartbeat_message()
        for _ in range(self.client._max_queue_size):
            await self.client._message_queue.put(dummy_message)

        success = await self.client.send_controller_input(input_data)
        assert not success

    @pytest.mark.asyncio
    async def test_send_message_none_check(self):
        """Should reject None messages."""
        self.client._running = True

        success = await self.client.send_message(None)
        assert not success


class TestWebSocketServer:
    """Test WebSocket server."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = WebSocketServer(
            host="localhost",
            port=8765,
        )

    def teardown_method(self):
        """Clean up after tests."""
        # Ensure server is stopped
        if hasattr(self.server, "_running") and self.server._running:
            asyncio.run(self.server.stop())

    def test_address_property(self):
        """Should generate correct server address."""
        assert self.server.address == "localhost:8765"

    def test_running_property(self):
        """Should report running state correctly."""
        assert not self.server.running

    def test_client_count_property(self):
        """Should report client count correctly."""
        assert self.server.client_count == 0

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self):
        """Should handle start/stop lifecycle correctly."""
        # Mock websockets.serve to avoid binding to actual port
        with patch("websockets.serve") as mock_serve:
            mock_server = AsyncMock()
            mock_server.close = Mock()
            mock_server.wait_closed = AsyncMock()

            # Make websockets.serve return an awaitable that returns the mock server
            async def mock_serve_coroutine(*args, **kwargs):
                return mock_server
            mock_serve.side_effect = mock_serve_coroutine

            await self.server.start()
            assert self.server.running

            await self.server.stop()
            assert not self.server.running
            mock_server.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_message_not_running(self):
        """Should handle broadcast when not running."""
        message = NetworkMessage.create_heartbeat_message()

        count = await self.server.broadcast_message(message)
        assert count == 0

    @pytest.mark.asyncio
    async def test_send_to_client_not_running(self):
        """Should handle send to client when not running."""
        message = NetworkMessage.create_heartbeat_message()

        success = await self.server.send_to_client("test-client", message)
        assert not success

    @pytest.mark.asyncio
    async def test_input_callback(self):
        """Should call input callback when provided."""
        received_inputs = []

        def callback(input_data):
            received_inputs.append(input_data)

        server = WebSocketServer(
            host="localhost",
            port=8765,
            input_callback=callback,
        )

        # Simulate receiving controller input
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test",
        )

        message = NetworkMessage.create_controller_input_message(input_data)
        await server._handle_controller_input(message)

        assert len(received_inputs) == 1
        assert received_inputs[0].controller_number == 1

    @pytest.mark.asyncio
    async def test_message_callback(self):
        """Should call message callback when provided."""
        received_messages = []

        def callback(message, client_id):
            received_messages.append((message, client_id))

        server = WebSocketServer(
            host="localhost",
            port=8765,
            message_callback=callback,
        )

        # Simulate message processing
        test_message = NetworkMessage.create_heartbeat_message()
        server._message_callback(test_message, "test-client")

        assert len(received_messages) == 1
        assert received_messages[0][0].message_id == test_message.message_id
        assert received_messages[0][1] == "test-client"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Should work as async context manager."""
        with patch("websockets.serve") as mock_serve:
            mock_server = AsyncMock()
            mock_server.close = Mock()
            mock_server.wait_closed = AsyncMock()
            # Make websockets.serve return an awaitable that returns the mock server
            async def mock_serve_coroutine(*args, **kwargs):
                return mock_server
            mock_serve.side_effect = mock_serve_coroutine

            async with self.server as server:
                assert server.running

            assert not server.running
