"""WebSocket server for receiving controller input data."""

import asyncio
import logging
from typing import Set, Optional, Callable, Dict
import uuid
from datetime import datetime

import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError

from .message_protocol import NetworkMessage, MessageType
from ..models import ControllerInputData


logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server with client management and message routing."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        ping_timeout: float = 20.0,
        input_callback: Optional[Callable[[ControllerInputData], None]] = None,
        message_callback: Optional[Callable[[NetworkMessage, str], None]] = None
    ):
        """Initialize WebSocket server.
        
        Args:
            host: Server bind address
            port: Server port
            ping_timeout: WebSocket ping timeout
            input_callback: Optional callback for controller input
            message_callback: Optional callback for all messages
        """
        self._host = host
        self._port = port
        self._ping_timeout = ping_timeout
        self._input_callback = input_callback
        self._message_callback = message_callback
        
        self._server: Optional[websockets.WebSocketServer] = None
        self._running = False
        self._clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self._client_tasks: Dict[str, Set[asyncio.Task]] = {}
        
    @property
    def address(self) -> str:
        """Get server address."""
        return f"{self._host}:{self._port}"
    
    @property
    def running(self) -> bool:
        """Check if server is running."""
        return self._running
    
    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)
    
    async def start(self) -> None:
        """Start WebSocket server."""
        if self._running:
            logger.warning("WebSocket server is already running")
            return
            
        logger.info(f"Starting WebSocket server on {self.address}")
        
        try:
            self._server = await websockets.serve(
                self._handle_client,
                self._host,
                self._port,
                ping_timeout=self._ping_timeout
            )
            self._running = True
            logger.info(f"WebSocket server listening on {self.address}")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop WebSocket server."""
        if not self._running:
            return
            
        self._running = False
        logger.info("Stopping WebSocket server")
        
        # Close all client connections
        for client_id in list(self._clients.keys()):
            await self._disconnect_client(client_id)
            
        # Stop server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            
        logger.info("WebSocket server stopped")
    
    async def broadcast_message(self, message: NetworkMessage) -> int:
        """Broadcast message to all connected clients.
        
        Args:
            message: Message to broadcast
            
        Returns:
            Number of clients message was sent to
        """
        if not self._running:
            logger.warning("Cannot broadcast - server not running")
            return 0
            
        sent_count = 0
        for client_id, websocket in list(self._clients.items()):
            if not websocket.closed:
                try:
                    await websocket.send(message.to_json())
                    sent_count += 1
                    logger.debug(f"Broadcast message to client {client_id}")
                except ConnectionClosed:
                    logger.debug(f"Client {client_id} disconnected during broadcast")
                    await self._disconnect_client(client_id)
                except Exception as e:
                    logger.error(f"Failed to send to client {client_id}: {e}")
                    
        return sent_count
    
    async def send_to_client(self, client_id: str, message: NetworkMessage) -> bool:
        """Send message to specific client.
        
        Args:
            client_id: Target client ID
            message: Message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._running:
            logger.warning("Cannot send message - server not running")
            return False
            
        websocket = self._clients.get(client_id)
        if not websocket or websocket.closed:
            logger.warning(f"Client {client_id} not found or disconnected")
            return False
            
        try:
            await websocket.send(message.to_json())
            logger.debug(f"Sent message to client {client_id}")
            return True
        except ConnectionClosed:
            logger.debug(f"Client {client_id} disconnected during send")
            await self._disconnect_client(client_id)
            return False
        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            return False
    
    async def _handle_client(self, websocket, path: str) -> None:
        """Handle new client connection.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        client_id = str(uuid.uuid4())
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        
        logger.info(f"New client connected: {client_id} from {client_addr}")
        
        # Register client
        self._clients[client_id] = websocket
        self._client_tasks[client_id] = set()
        
        try:
            # Send welcome message
            welcome_message = NetworkMessage.create_status_response_message(
                active_controllers=0,
                connection_status="connected"
            )
            await websocket.send(welcome_message.to_json())
            
            # Handle client messages
            await self._handle_client_messages(client_id, websocket)
            
        except ConnectionClosed:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            await self._disconnect_client(client_id)
    
    async def _handle_client_messages(
        self, 
        client_id: str, 
        websocket
    ) -> None:
        """Handle messages from a specific client.
        
        Args:
            client_id: Client identifier
            websocket: WebSocket connection
        """
        try:
            async for raw_message in websocket:
                try:
                    message = NetworkMessage.from_json(raw_message)
                    logger.debug(f"Received {message.message_type} from client {client_id}")
                    
                    # Process message based on type
                    await self._process_client_message(client_id, websocket, message)
                    
                except Exception as e:
                    logger.error(f"Failed to process message from client {client_id}: {e}")
                    
                    # Send error response
                    error_message = NetworkMessage.create_error_message(
                        error_code="INVALID_MESSAGE",
                        error_description=str(e)
                    )
                    try:
                        await websocket.send(error_message.to_json())
                    except:
                        pass  # Client may have disconnected
                        
        except ConnectionClosed:
            logger.debug(f"Client {client_id} message handler connection closed")
        except Exception as e:
            logger.error(f"Error in client {client_id} message handler: {e}")
    
    async def _process_client_message(
        self,
        client_id: str,
        websocket,
        message: NetworkMessage
    ) -> None:
        """Process individual client message.
        
        Args:
            client_id: Client identifier
            websocket: WebSocket connection  
            message: Received message
        """
        # Call message callback if provided
        if self._message_callback:
            try:
                self._message_callback(message, client_id)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
        
        # Handle specific message types
        if message.message_type == MessageType.CONTROLLER_INPUT:
            await self._handle_controller_input(message)
            
        elif message.message_type == MessageType.STATUS_REQUEST:
            await self._handle_status_request(client_id, websocket, message)
            
        elif message.message_type == MessageType.HEARTBEAT:
            await self._handle_heartbeat(client_id, websocket, message)
    
    async def _handle_controller_input(self, message: NetworkMessage) -> None:
        """Handle controller input message.
        
        Args:
            message: Controller input message
        """
        input_data = message.get_controller_input_data()
        if input_data and self._input_callback:
            try:
                self._input_callback(input_data)
            except Exception as e:
                logger.error(f"Error in input callback: {e}")
    
    async def _handle_status_request(
        self,
        client_id: str,
        websocket,
        message: NetworkMessage
    ) -> None:
        """Handle status request message.
        
        Args:
            client_id: Client identifier
            websocket: WebSocket connection
            message: Status request message
        """
        response = NetworkMessage.create_status_response_message(
            active_controllers=0,  # TODO: Get actual count from controller manager
            connection_status="active"
        )
        
        try:
            await websocket.send(response.to_json())
        except ConnectionClosed:
            logger.debug(f"Client {client_id} disconnected during status response")
        except Exception as e:
            logger.error(f"Failed to send status response to {client_id}: {e}")
    
    async def _handle_heartbeat(
        self,
        client_id: str,
        websocket,
        message: NetworkMessage
    ) -> None:
        """Handle heartbeat message.
        
        Args:
            client_id: Client identifier
            websocket: WebSocket connection
            message: Heartbeat message
        """
        # Echo heartbeat back
        try:
            await websocket.send(message.to_json())
        except ConnectionClosed:
            logger.debug(f"Client {client_id} disconnected during heartbeat response")
        except Exception as e:
            logger.error(f"Failed to send heartbeat response to {client_id}: {e}")
    
    async def _disconnect_client(self, client_id: str) -> None:
        """Disconnect and cleanup client.
        
        Args:
            client_id: Client identifier
        """
        logger.info(f"Disconnecting client {client_id}")
        
        # Cancel client tasks
        tasks = self._client_tasks.get(client_id, set())
        for task in tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
        # Remove from tracking
        self._clients.pop(client_id, None)
        self._client_tasks.pop(client_id, None)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()