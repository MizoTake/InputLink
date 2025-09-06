"""WebSocket client for sending controller input data."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK

from input_link.models import ControllerInputData
from input_link.network.message_protocol import NetworkMessage

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client with automatic reconnection and error handling."""

    def __init__(
        self,
        host: str,
        port: int,
        reconnect_interval: float = 1.0,
        max_reconnect_attempts: int = 10,
        ping_timeout: float = 20.0,
        message_callback: Optional[Callable[[NetworkMessage], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize WebSocket client.
        
        Args:
            host: Server hostname or IP
            port: Server port
            reconnect_interval: Time between reconnection attempts
            max_reconnect_attempts: Maximum reconnection attempts
            ping_timeout: WebSocket ping timeout
            message_callback: Optional callback for received messages
            status_callback: Optional callback for connection status changes
        """
        self._host = host
        self._port = port
        self._reconnect_interval = reconnect_interval
        self._max_reconnect_attempts = max_reconnect_attempts
        self._ping_timeout = ping_timeout
        self._message_callback = message_callback
        self._status_callback = status_callback

        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._connected = False
        self._reconnect_attempts = 0
        self._message_queue: asyncio.Queue[NetworkMessage] = asyncio.Queue()
        self._tasks: Set[asyncio.Task] = set()

    @property
    def uri(self) -> str:
        """Get WebSocket URI."""
        return f"ws://{self._host}:{self._port}"

    @property
    def connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._websocket and not self._websocket.closed

    async def start(self) -> None:
        """Start WebSocket client."""
        if self._running:
            logger.warning("WebSocket client is already running")
            return

        self._running = True
        logger.info(f"Starting WebSocket client to {self.uri}")

        # Create connection task
        connect_task = asyncio.create_task(self._connection_loop())
        self._tasks.add(connect_task)
        connect_task.add_done_callback(self._tasks.discard)

        # Create message sender task
        sender_task = asyncio.create_task(self._message_sender())
        self._tasks.add(sender_task)
        sender_task.add_done_callback(self._tasks.discard)

    async def stop(self) -> None:
        """Stop WebSocket client."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping WebSocket client")

        # Close WebSocket connection
        if self._websocket and not self._websocket.closed:
            await self._websocket.close()

        # Cancel all tasks
        for task in list(self._tasks):
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._connected = False
        if self._status_callback:
            self._status_callback("disconnected")
        logger.info("WebSocket client stopped")

    async def send_controller_input(self, input_data: ControllerInputData) -> bool:
        """Send controller input data.
        
        Args:
            input_data: Controller input data to send
            
        Returns:
            True if queued successfully, False otherwise
        """
        if not self._running:
            logger.warning("Cannot send input data - client not running")
            return False

        try:
            message = NetworkMessage.create_controller_input_message(input_data)
            await self._message_queue.put(message)
            return True
        except Exception as e:
            logger.error(f"Failed to queue controller input: {e}")
            return False

    async def send_message(self, message: NetworkMessage) -> bool:
        """Send network message.
        
        Args:
            message: Network message to send
            
        Returns:
            True if queued successfully, False otherwise
        """
        if not self._running:
            logger.warning("Cannot send message - client not running")
            return False

        try:
            await self._message_queue.put(message)
            return True
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
            return False

    async def _connection_loop(self) -> None:
        """Main connection loop with reconnection logic."""
        while self._running:
            try:
                if self._status_callback:
                    self._status_callback("connecting")
                async with websockets.connect(
                    self.uri,
                    ping_timeout=self._ping_timeout,
                    close_timeout=10,
                ) as websocket:
                    self._websocket = websocket
                    self._connected = True
                    self._reconnect_attempts = 0

                    logger.info(f"Connected to WebSocket server at {self.uri}")
                    if self._status_callback:
                        self._status_callback("connected")

                    # Create message receiver task
                    receiver_task = asyncio.create_task(self._message_receiver(websocket))
                    self._tasks.add(receiver_task)
                    receiver_task.add_done_callback(self._tasks.discard)

                    # Wait for connection to close
                    await websocket.wait_closed()

            except (ConnectionClosed, ConnectionClosedOK, ConnectionClosedError) as e:
                logger.warning(f"WebSocket connection closed: {e}")

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")

            finally:
                self._connected = False
                self._websocket = None
                if self._status_callback:
                    self._status_callback("disconnected")

            # Reconnection logic
            if self._running and self._reconnect_attempts < self._max_reconnect_attempts:
                self._reconnect_attempts += 1
                wait_time = min(self._reconnect_interval * (2 ** (self._reconnect_attempts - 1)), 30)

                logger.info(f"Reconnecting in {wait_time}s (attempt {self._reconnect_attempts})")
                if self._status_callback:
                    self._status_callback("reconnecting")
                await asyncio.sleep(wait_time)
            elif self._running:
                logger.error("Max reconnection attempts reached")
                if self._status_callback:
                    self._status_callback("failed")
                break

    async def _message_receiver(self, websocket) -> None:
        """Receive and process messages from server.
        
        Args:
            websocket: WebSocket connection
        """
        try:
            async for message in websocket:
                try:
                    network_message = NetworkMessage.from_json(message)
                    logger.debug(f"Received message: {network_message.message_type}")

                    # Call message callback if provided
                    if self._message_callback:
                        try:
                            self._message_callback(network_message)
                        except Exception as e:
                            logger.error(f"Error in message callback: {e}")

                except Exception as e:
                    logger.error(f"Failed to parse received message: {e}")

        except ConnectionClosed:
            logger.debug("Message receiver connection closed")
        except Exception as e:
            logger.error(f"Error in message receiver: {e}")

    async def _message_sender(self) -> None:
        """Send queued messages to server."""
        while self._running:
            try:
                # Wait for message with timeout
                try:
                    message = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                # Send message if connected
                if self.connected:
                    try:
                        await self._websocket.send(message.to_json())
                        logger.debug(f"Sent message: {message.message_type}")
                    except ConnectionClosed:
                        logger.debug("Connection closed while sending message")
                        # Re-queue message
                        await self._message_queue.put(message)
                    except Exception as e:
                        logger.error(f"Failed to send message: {e}")
                        # Re-queue message
                        await self._message_queue.put(message)
                else:
                    # Re-queue message if not connected
                    await self._message_queue.put(message)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in message sender: {e}")
                await asyncio.sleep(0.1)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
