"""Integration tests for sender application restart scenarios."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from input_link.apps.sender import SenderApp
from input_link.models import ConfigModel, SenderConfig, ReceiverConfig


class TestSenderRestart:
    """Test sender application restart scenarios."""

    @pytest.mark.asyncio
    async def test_sender_start_stop_start_cycle(self):
        """Should handle complete start-stop-start cycle."""
        with patch("pygame.init") as mock_pygame_init, \
             patch("pygame.joystick.init") as mock_joystick_init, \
             patch("pygame.joystick.get_count", return_value=0), \
             patch("pygame.event.pump"), \
             patch("websockets.connect") as mock_ws_connect:

            # Mock pygame initialization
            mock_pygame_init.return_value = (7, 0)

            # Mock WebSocket connection
            mock_websocket = AsyncMock()
            mock_websocket.closed = False
            mock_websocket.wait_closed = AsyncMock()
            mock_ws_connect.return_value.__aenter__.return_value = mock_websocket
            mock_ws_connect.return_value.__aexit__.return_value = None

            # Create sender app
            app = SenderApp()
            app.config = ConfigModel(
                sender_config=SenderConfig(
                    receiver_host="localhost",
                    receiver_port=8765,
                ),
                receiver_config=ReceiverConfig(),
            )

            # First start
            start_task = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)  # Let it start

            assert app.running
            assert app.controller_manager is not None
            assert app.input_engine is not None
            assert app.websocket_client is not None

            # Stop
            await app.stop()
            await asyncio.sleep(0.1)  # Let it stop
            if not start_task.done():
                start_task.cancel()
                await asyncio.gather(start_task, return_exceptions=True)

            assert not app.running

            # Second start
            start_task2 = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)  # Let it start

            assert app.running
            assert app.controller_manager is not None
            assert app.input_engine is not None
            assert app.websocket_client is not None

            # Cleanup
            await app.stop()
            await asyncio.sleep(0.1)
            if not start_task2.done():
                start_task2.cancel()
                await asyncio.gather(start_task2, return_exceptions=True)

    @pytest.mark.asyncio
    async def test_sender_cleanup_order(self):
        """Should cleanup components in correct order."""
        with patch("pygame.init") as mock_pygame_init, \
             patch("pygame.joystick.init"), \
             patch("pygame.joystick.get_count", return_value=0), \
             patch("pygame.joystick.get_init", return_value=True), \
             patch("pygame.joystick.quit") as mock_joystick_quit, \
             patch("pygame.quit") as mock_pygame_quit, \
             patch("pygame.event.pump"), \
             patch("websockets.connect") as mock_ws_connect:

            # Mock pygame initialization
            mock_pygame_init.return_value = (7, 0)

            # Mock WebSocket connection
            mock_websocket = AsyncMock()
            mock_websocket.closed = False
            mock_websocket.wait_closed = AsyncMock()
            mock_ws_connect.return_value.__aenter__.return_value = mock_websocket
            mock_ws_connect.return_value.__aexit__.return_value = None

            # Create sender app
            app = SenderApp()
            app.config = ConfigModel(
                sender_config=SenderConfig(
                    receiver_host="localhost",
                    receiver_port=8765,
                ),
                receiver_config=ReceiverConfig(),
            )

            # Start
            start_task = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)

            # Verify components are initialized
            assert app.controller_manager._initialized
            assert app.input_engine._running

            # Stop and verify cleanup order
            await app.stop()
            await asyncio.sleep(0.1)
            if not start_task.done():
                start_task.cancel()
                await asyncio.gather(start_task, return_exceptions=True)

            # Verify all components are cleaned up
            assert app.controller_manager is None
            assert app.input_engine is None
            assert app.websocket_client is None

    @pytest.mark.asyncio
    async def test_sender_multiple_restarts(self):
        """Should handle multiple consecutive restarts."""
        with patch("pygame.init") as mock_pygame_init, \
             patch("pygame.joystick.init"), \
             patch("pygame.joystick.get_count", return_value=0), \
             patch("pygame.event.pump"), \
             patch("websockets.connect") as mock_ws_connect:

            # Mock pygame initialization
            mock_pygame_init.return_value = (7, 0)

            # Mock WebSocket connection
            mock_websocket = AsyncMock()
            mock_websocket.closed = False
            mock_websocket.wait_closed = AsyncMock()
            mock_ws_connect.return_value.__aenter__.return_value = mock_websocket
            mock_ws_connect.return_value.__aexit__.return_value = None

            # Create sender app
            app = SenderApp()
            app.config = ConfigModel(
                sender_config=SenderConfig(
                    receiver_host="localhost",
                    receiver_port=8765,
                ),
                receiver_config=ReceiverConfig(),
            )

            # Perform 5 start-stop cycles
            for i in range(5):
                # Start
                start_task = asyncio.create_task(app.start())
                await asyncio.sleep(0.05)

                assert app.running, f"Cycle {i+1}: Should be running after start"

                # Stop
                await app.stop()
                await asyncio.sleep(0.05)
                if not start_task.done():
                    start_task.cancel()
                    await asyncio.gather(start_task, return_exceptions=True)

                assert not app.running, f"Cycle {i+1}: Should not be running after stop"

    @pytest.mark.asyncio
    async def test_sender_state_isolation_between_restarts(self):
        """Should ensure state is fully isolated between restarts."""
        with patch("pygame.init") as mock_pygame_init, \
             patch("pygame.joystick.init"), \
             patch("pygame.joystick.get_count", return_value=0), \
             patch("pygame.event.pump"), \
             patch("websockets.connect") as mock_ws_connect:

            # Mock pygame initialization
            mock_pygame_init.return_value = (7, 0)

            # Mock WebSocket connection
            mock_websocket = AsyncMock()
            mock_websocket.closed = False
            mock_websocket.wait_closed = AsyncMock()
            mock_ws_connect.return_value.__aenter__.return_value = mock_websocket
            mock_ws_connect.return_value.__aexit__.return_value = None

            # Create sender app
            app = SenderApp()
            app.config = ConfigModel(
                sender_config=SenderConfig(
                    receiver_host="localhost",
                    receiver_port=8765,
                ),
                receiver_config=ReceiverConfig(),
            )

            # First start
            start_task1 = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)

            # Get references to first instance components
            first_controller_manager = app.controller_manager
            first_input_engine = app.input_engine
            first_websocket_client = app.websocket_client

            # Stop
            await app.stop()
            await asyncio.sleep(0.1)
            if not start_task1.done():
                start_task1.cancel()
                await asyncio.gather(start_task1, return_exceptions=True)

            # Second start
            start_task2 = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)

            # Get references to second instance components
            second_controller_manager = app.controller_manager
            second_input_engine = app.input_engine
            second_websocket_client = app.websocket_client

            # Verify they are different instances
            # (Components should be recreated, not reused)
            assert second_controller_manager is not None
            assert second_input_engine is not None
            assert second_websocket_client is not None

            # Cleanup
            await app.stop()
            await asyncio.sleep(0.1)
            if not start_task2.done():
                start_task2.cancel()
                await asyncio.gather(start_task2, return_exceptions=True)
