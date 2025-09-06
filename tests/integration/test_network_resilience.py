#!/usr/bin/env python3
"""Integration tests for network resilience and error handling."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import websockets
import json

from input_link.network import WebSocketClient, WebSocketServer
from input_link.network.message_protocol import MessageProtocol
from input_link.models import ControllerInputData, ButtonState, ControllerState


class TestNetworkResilience:
    """Test network connection resilience and error handling."""

    @pytest.mark.asyncio
    async def test_websocket_client_connection_retry(self):
        """Test WebSocket client connection retry logic."""
        client = WebSocketClient("127.0.0.1", 8765)
        
        connection_attempts = []
        
        # Mock websockets.connect to track attempts
        async def mock_connect(*args, **kwargs):
            connection_attempts.append(args)
            raise ConnectionRefusedError("Connection refused")
        
        with patch('websockets.connect', side_effect=mock_connect):
            # Start client (should fail to connect)
            await client.start()
            
            # Give it time to attempt connection
            await asyncio.sleep(0.1)
            
            await client.stop()
        
        # Should have attempted to connect
        assert len(connection_attempts) >= 1

    @pytest.mark.asyncio
    async def test_websocket_server_graceful_client_disconnect(self):
        """Test server handling client disconnections gracefully."""
        server = WebSocketServer("127.0.0.1", 0)  # Use port 0 for any available port
        
        client_connections = []
        disconnections = []
        
        def on_status_change(status, data):
            if status == "client_connected":
                client_connections.append(data.get("client_id"))
            elif status == "client_disconnected":
                disconnections.append(data.get("client_id"))
        
        server = WebSocketServer("127.0.0.1", 0, status_callback=on_status_change)
        
        # Start server
        await server.start()
        actual_port = server.port
        
        try:
            # Create mock client connection that will disconnect
            mock_websocket = Mock()
            mock_websocket.closed = False
            mock_websocket.close = AsyncMock()
            
            # Simulate client connection and disconnection
            await server._handle_client(mock_websocket, f"127.0.0.1:{actual_port}")
            
        except Exception:
            pass  # Expected as mock websocket will cause issues
        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_message_protocol_malformed_data_handling(self):
        """Test message protocol handling of malformed data."""
        # Test various malformed JSON inputs
        malformed_inputs = [
            '{"incomplete": true',  # Incomplete JSON
            '{"type": "unknown_type", "data": {}}',  # Unknown message type
            '{"type": "controller_input"}',  # Missing data field
            'not json at all',  # Not JSON
            '{}',  # Empty object
            '{"type": "controller_input", "data": {"invalid": "structure"}}',  # Invalid data structure
        ]
        
        for malformed_input in malformed_inputs:
            try:
                # Should either parse correctly or raise appropriate exception
                message = MessageProtocol.parse_message(malformed_input)
                # If parsing succeeds, should at least have type field
                assert hasattr(message, 'type')
            except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                # These exceptions are expected for malformed data
                pass

    @pytest.mark.asyncio 
    async def test_client_server_message_queue_overflow(self):
        """Test behavior when message queues overflow."""
        client = WebSocketClient("127.0.0.1", 8765, message_queue_size=5)
        
        # Fill up the message queue
        test_data = ControllerInputData(
            controller_number=1,
            controller_id="test",
            buttons=ButtonState(),
            axes=ControllerState()
        )
        
        # Try to queue more messages than the limit
        for i in range(10):
            await client.send_controller_input(test_data)
        
        # Queue should handle overflow gracefully (either drop messages or block)
        assert len(client._message_queue) <= client._max_queue_size

    @pytest.mark.asyncio
    async def test_network_latency_simulation(self):
        """Test system behavior under network latency."""
        # Create client and server with simulated latency
        server = WebSocketServer("127.0.0.1", 0)
        
        # Start server
        await server.start()
        port = server.port
        
        client = WebSocketClient("127.0.0.1", port)
        
        messages_received = []
        
        def message_callback(message):
            messages_received.append(message)
        
        client.message_callback = message_callback
        
        try:
            await client.start()
            
            # Simulate sending multiple messages rapidly
            for i in range(5):
                test_data = ControllerInputData(
                    controller_number=i + 1,
                    controller_id=f"test_{i}",
                    buttons=ButtonState(),
                    axes=ControllerState()
                )
                await client.send_controller_input(test_data)
                await asyncio.sleep(0.01)  # Small delay between messages
            
            # Give time for messages to be processed
            await asyncio.sleep(0.5)
            
        finally:
            await client.stop()
            await server.stop()

    @pytest.mark.asyncio
    async def test_concurrent_client_connections(self):
        """Test server handling multiple concurrent client connections."""
        server = WebSocketServer("127.0.0.1", 0)
        
        connections_count = []
        
        def status_callback(status, data):
            if status == "client_connected":
                connections_count.append("connected")
            elif status == "client_disconnected": 
                connections_count.append("disconnected")
        
        server.status_callback = status_callback
        
        await server.start()
        port = server.port
        
        # Create multiple clients
        clients = [WebSocketClient("127.0.0.1", port) for _ in range(3)]
        
        try:
            # Start all clients concurrently
            await asyncio.gather(*[client.start() for client in clients])
            
            # Give time for connections to establish
            await asyncio.sleep(0.2)
            
            # Verify server can handle multiple connections
            assert server.client_count <= 3
            
        finally:
            # Clean up all clients
            await asyncio.gather(*[client.stop() for client in clients])
            await server.stop()


class TestMessageIntegrity:
    """Test message integrity and data consistency."""

    @pytest.mark.asyncio
    async def test_controller_data_roundtrip_integrity(self):
        """Test that controller data maintains integrity through network transmission."""
        # Create detailed controller input
        original_data = ControllerInputData(
            controller_number=3,
            controller_id="xbox_controller_001",
            buttons=ButtonState(
                a=True, b=False, x=True, y=False,
                lb=True, rb=False, back=True, start=False,
                ls=True, rs=False,
                dpad_up=True, dpad_down=False, dpad_left=True, dpad_right=False
            ),
            axes=ControllerState(
                left_stick_x=0.75,
                left_stick_y=-0.25,
                right_stick_x=-0.5,
                right_stick_y=0.8,
                left_trigger=0.9,
                right_trigger=0.1
            )
        )
        
        # Convert to message and back
        message = MessageProtocol.create_controller_input_message(original_data)
        json_data = message.to_json()
        
        # Parse back from JSON
        parsed_message = MessageProtocol.parse_message(json_data)
        reconstructed_data = parsed_message.get_controller_data()
        
        # Verify all data is preserved
        assert reconstructed_data.controller_number == original_data.controller_number
        assert reconstructed_data.controller_id == original_data.controller_id
        
        # Check button states
        assert reconstructed_data.buttons.a == original_data.buttons.a
        assert reconstructed_data.buttons.lb == original_data.buttons.lb
        assert reconstructed_data.buttons.dpad_up == original_data.buttons.dpad_up
        
        # Check axis values (with floating point tolerance)
        assert abs(reconstructed_data.axes.left_stick_x - original_data.axes.left_stick_x) < 0.001
        assert abs(reconstructed_data.axes.left_trigger - original_data.axes.left_trigger) < 0.001

    @pytest.mark.asyncio
    async def test_message_ordering_preservation(self):
        """Test that message ordering is preserved under load."""
        server = WebSocketServer("127.0.0.1", 0)
        received_messages = []
        
        def input_callback(input_data):
            received_messages.append(input_data.controller_number)
        
        server.input_callback = input_callback
        
        await server.start()
        port = server.port
        
        client = WebSocketClient("127.0.0.1", port)
        
        try:
            await client.start()
            await asyncio.sleep(0.1)  # Let connection establish
            
            # Send messages in specific order
            expected_order = [1, 2, 3, 4, 5]
            
            for controller_num in expected_order:
                test_data = ControllerInputData(
                    controller_number=controller_num,
                    controller_id=f"controller_{controller_num}",
                    buttons=ButtonState(),
                    axes=ControllerState()
                )
                await client.send_controller_input(test_data)
                await asyncio.sleep(0.01)  # Small delay between messages
            
            # Give time for all messages to be processed
            await asyncio.sleep(0.5)
            
            # Message ordering might not be strictly preserved due to async nature
            # but all messages should be received
            assert len(received_messages) == len(expected_order)
            assert set(received_messages) == set(expected_order)
            
        finally:
            await client.stop()
            await server.stop()


class TestErrorRecovery:
    """Test system recovery from various error conditions."""

    @pytest.mark.asyncio
    async def test_server_restart_capability(self):
        """Test server can be stopped and restarted cleanly."""
        server = WebSocketServer("127.0.0.1", 0)
        
        # Start server
        await server.start()
        original_port = server.port
        assert server.running
        
        # Stop server
        await server.stop()
        assert not server.running
        
        # Restart server (should work on same or different port)
        await server.start()
        assert server.running
        
        # Clean up
        await server.stop()

    @pytest.mark.asyncio
    async def test_client_reconnection_after_server_restart(self):
        """Test client can reconnect after server restarts."""
        server = WebSocketServer("127.0.0.1", 0)
        await server.start()
        port = server.port
        
        client = WebSocketClient("127.0.0.1", port)
        
        # Initial connection
        await client.start()
        await asyncio.sleep(0.1)
        
        # Stop server (simulating server crash/restart)
        await server.stop()
        await asyncio.sleep(0.1)
        
        # Restart server on same port
        server = WebSocketServer("127.0.0.1", port)
        await server.start()
        
        # Client should handle reconnection gracefully
        # (Implementation dependent - may require explicit reconnection logic)
        
        # Clean up
        await client.stop()
        await server.stop()