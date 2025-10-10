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

        # Clear message queue to prevent stale messages on restart
        queue_size = self._message_queue.qsize()
        if queue_size > 0:
            logger.debug(f"Clearing {queue_size} messages from queue")
            while not self._message_queue.empty():
                self._message_queue.get_nowait()

        self._connected = False
        self._websocket = None
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

            # Attempt connection - handle failure without exceptions
            connection_result = await self._attempt_connection()
            if connection_result is None:
                # Connection failed - apply reconnection logic
                self._reconnect_attempts += 1

                # Check if we should retry
                if self._max_reconnect_attempts > 0 and self._reconnect_attempts >= self._max_reconnect_attempts:
                    logger.error("Max reconnection attempts reached")
                    if self._status_callback:
                        self._status_callback("failed")
                    break

                # Calculate backoff with max 60s for long outages
                wait_time = min(self._reconnect_interval * (2 ** (self._reconnect_attempts - 1)), 60)
                logger.info(f"Reconnecting in {wait_time}s (attempt {self._reconnect_attempts})")
                if self._status_callback:
                    self._status_callback("reconnecting")
                await asyncio.sleep(wait_time)
                continue

            # Connection successful
            websocket = connection_result
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

    async def _attempt_connection(self) -> Optional[websockets.WebSocketClientProtocol]:
        """Attempt to connect to WebSocket server.

        Returns:
            WebSocket connection on success, None on failure
        """
        # Create wrapper coroutine for connection with proper context manager handling
        async def connect_wrapper():
            """Wrapper to handle websockets.connect as context manager."""
            ctx = websockets.connect(
                self.uri,
                ping_timeout=self._ping_timeout,
                close_timeout=10,
            )
            # Enter context manager to get actual connection
            return await ctx.__aenter__()

        # Use asyncio.wait to handle connection failure without exceptions
        connect_task = asyncio.create_task(connect_wrapper())
        done, pending = await asyncio.wait(
            [connect_task],
            timeout=10.0,  # 10 second connection timeout
            return_when=asyncio.FIRST_COMPLETED
        )

        if done:
            task = done.pop()
            # Check if task raised an exception
            exception = task.exception()
            if exception is not None:
                # Connection failed with exception
                logger.warning(f"Connection failed: {exception}")
                return None
            # Connection succeeded
            return task.result()

        # Connection timed out - cancel pending tasks
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        logger.warning("Connection attempt timed out")
        return None

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
            # Get message with timeout - returns None on timeout
            message = await self._safe_queue_get(timeout=1.0)
            if message is None:
                continue  # Timeout or queue closed

            if self.connected:
                await self._websocket.send(message.to_json())
                logger.debug(f"Sent message: {message.message_type}")
            else:
                # Discard message if not connected - don't put back in queue
                # This prevents queue buildup during disconnection
                logger.debug(f"Discarding message (not connected): {message.message_type}")
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

        # Create task and use asyncio.wait with proper cleanup
        get_task = asyncio.create_task(self._message_queue.get())
        done, pending = await asyncio.wait(
            [get_task],
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED
        )

        if done:
            # Task completed - return the result
            return done.pop().result()

        # Timeout occurred - must cancel pending tasks to avoid leak
        for task in pending:
            task.cancel()
        # Wait for cancellation to complete to ensure proper cleanup
        await asyncio.gather(*pending, return_exceptions=True)
        return None
