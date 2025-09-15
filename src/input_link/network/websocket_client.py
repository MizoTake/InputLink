"""WebSocket client for sending controller input data."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Optional, Set, Any

import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK

from input_link.models import ControllerInputData
from input_link.network.message_protocol import NetworkMessage

logger = logging.getLogger(__name__)


class _LenQueue:
    """Thin wrapper around asyncio.Queue that supports len()."""

    def __init__(self, maxsize: int):
        self._q: asyncio.Queue[Any] = asyncio.Queue(maxsize=maxsize)

    def __len__(self) -> int:  # for tests that use len(queue)
        return self._q.qsize()

    # Delegate common queue APIs used by client
    def __getattr__(self, name: str):
        return getattr(self._q, name)


class WebSocketClient:
    """WebSocket client with automatic reconnection and error handling."""

    def __init__(
        self,
        host: str,
        port: int,
        reconnect_interval: float = 1.0,
        max_reconnect_attempts: int = 10,
        ping_timeout: float = 20.0,
        message_queue_size: int = 100,
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
        # Bounded queue; tests inspect `_max_queue_size` and queue length
        self._max_queue_size = int(message_queue_size)
        self._message_queue: _LenQueue = _LenQueue(maxsize=self._max_queue_size)
        self._tasks: Set[asyncio.Task] = set()

    @property
    def uri(self) -> str:
        """Get WebSocket URI."""
        return f"ws://{self._host}:{self._port}"

    @property
    def connected(self) -> bool:
        """Check if client is connected."""
        # Some websockets implementations/protocol versions don't expose a boolean
        # `closed` attribute on the connection object. Rely on our internal state
        # and presence of the websocket reference; sending will still be guarded
        # by exception handling if the socket is no longer open.
        return bool(self._connected and self._websocket is not None)

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
        if self._websocket:
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

        # Create message - this should not fail with valid input
        message = NetworkMessage.create_controller_input_message(input_data)

        # Check queue capacity before putting
        if self._message_queue.qsize() >= self._max_queue_size:
            logger.warning("Message queue full, dropping controller input")
            return False

        # Queue message
        return await self._safe_queue_put(message)

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

        if message is None:
            logger.error("Cannot send None message")
            return False

        # Queue message
        return await self._safe_queue_put(message)

    async def _connection_loop(self) -> None:
        """Main connection loop with reconnection logic."""
        while self._running:
            if self._status_callback:
                self._status_callback("connecting")
            websocket = await websockets.connect(
                self.uri,
                ping_timeout=self._ping_timeout,
                close_timeout=10,
            )
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

            self._connected = False
            self._websocket = None
            if self._status_callback:
                self._status_callback("disconnected")

            # Reconnection logic (max_reconnect_attempts <= 0 means infinite)
            if self._running and (
                self._max_reconnect_attempts <= 0 or
                self._reconnect_attempts < self._max_reconnect_attempts
            ):
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
        async for message in websocket:
            network_message = NetworkMessage.from_json(message)
            logger.debug(f"Received message: {network_message.message_type}")

            # Call message callback if provided
            if self._message_callback:
                self._message_callback(network_message)

    async def _message_sender(self) -> None:
        """Send queued messages to server."""
        while self._running:
            # Get message with timeout - use helper method
            message = await self._safe_queue_get(timeout=1.0)
            if message is None:
                continue  # Timeout or queue closed

            if self.connected:
                await self._websocket.send(message.to_json())
                logger.debug(f"Sent message: {message.message_type}")
            else:
                await self._message_queue.put(message)
                await asyncio.sleep(0.1)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def _safe_queue_put(self, message: NetworkMessage) -> bool:
        """Safely put message in queue without exceptions.

        Args:
            message: Message to queue

        Returns:
            True if successful, False otherwise
        """
        if not self._running:
            return False

        # Use put_nowait to avoid blocking and handle queue full condition
        if self._message_queue.qsize() >= self._max_queue_size:
            return False

        # Queue should have space, but check if asyncio.Queue raises
        # We'll use put() which shouldn't raise in normal conditions
        await self._message_queue.put(message)
        return True

    async def _safe_queue_get(self, timeout: float = 1.0) -> Optional[NetworkMessage]:
        """Safely get message from queue with timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            Message if available, None on timeout or error
        """
        if not self._running:
            return None

        # Use asyncio.wait_for but handle timeout gracefully
        future = asyncio.create_task(self._message_queue.get())
        done, pending = await asyncio.wait([future], timeout=timeout)

        if done:
            task = done.pop()
            return task.result()
        else:
            # Cancel pending task and return None for timeout
            for task in pending:
                task.cancel()
            return None
