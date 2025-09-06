"""Receiver application for simulating controller inputs."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from ..network import WebSocketServer
from ..virtual import VirtualControllerManager
from ..models import ConfigModel, ControllerInputData


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReceiverApp:
    """Receiver application for Input Link."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize receiver application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or Path.home() / ".input-link" / "config.json"
        self.config: Optional[ConfigModel] = None
        self.websocket_server: Optional[WebSocketServer] = None
        self.virtual_controller_manager: Optional[VirtualControllerManager] = None
        self.running = False
        
    async def start(self) -> None:
        """Start the receiver application."""
        try:
            # Load configuration
            await self._load_config()
            
            # Initialize components
            await self._initialize_components()
            
            # Start services
            await self._start_services()
            
            self.running = True
            logger.info("Receiver application started successfully")
            
            # Run main loop
            await self._main_loop()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Failed to start receiver application: {e}")
            sys.exit(1)
        finally:
            await self._cleanup()
    
    async def _load_config(self) -> None:
        """Load application configuration."""
        try:
            # Create config directory if needed
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load or create config
            self.config = ConfigModel.load_from_file(self.config_path)
            logger.info(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    async def _initialize_components(self) -> None:
        """Initialize application components."""
        # Initialize virtual controller manager
        self.virtual_controller_manager = VirtualControllerManager(
            max_controllers=self.config.receiver_config.max_controllers,
            auto_create=self.config.receiver_config.auto_create_virtual,
            creation_callback=self._on_controller_created,
            destruction_callback=self._on_controller_destroyed
        )
        
        # Initialize WebSocket server
        self.websocket_server = WebSocketServer(
            host="0.0.0.0",  # Listen on all interfaces
            port=self.config.receiver_config.listen_port,
            input_callback=self._on_controller_input
        )
        
        logger.info("Components initialized")
    
    async def _start_services(self) -> None:
        """Start application services."""
        # Start virtual controller manager
        await self.virtual_controller_manager.start()
        
        # Start WebSocket server
        await self.websocket_server.start()
        
        logger.info(
            f"Server listening on port {self.config.receiver_config.listen_port}"
        )
    
    async def _main_loop(self) -> None:
        """Main application loop."""
        logger.info("Receiver running - Press Ctrl+C to stop")
        
        try:
            while self.running:
                # Display status periodically
                await asyncio.sleep(30.0)
                
                client_count = self.websocket_server.client_count
                controller_count = self.virtual_controller_manager.active_controller_count
                
                logger.info(
                    f"Status: {client_count} client(s), "
                    f"{controller_count} virtual controller(s)"
                )
                
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
    
    def _on_controller_input(self, input_data: ControllerInputData) -> None:
        """Handle received controller input data.
        
        Args:
            input_data: Controller input data from sender
        """
        # Forward to virtual controller manager
        asyncio.create_task(
            self.virtual_controller_manager.update_controller_state(input_data)
        )
    
    def _on_controller_created(self, controller_number: int) -> None:
        """Handle virtual controller creation.
        
        Args:
            controller_number: Controller number that was created
        """
        logger.info(f"Virtual controller {controller_number} created")
    
    def _on_controller_destroyed(self, controller_number: int) -> None:
        """Handle virtual controller destruction.
        
        Args:
            controller_number: Controller number that was destroyed
        """
        logger.info(f"Virtual controller {controller_number} destroyed")
    
    async def _cleanup(self) -> None:
        """Cleanup application resources."""
        logger.info("Cleaning up...")
        
        self.running = False
        
        # Stop WebSocket server
        if self.websocket_server:
            await self.websocket_server.stop()
        
        # Stop virtual controller manager
        if self.virtual_controller_manager:
            await self.virtual_controller_manager.stop()
        
        logger.info("Cleanup complete")


@click.command()
@click.option(
    '--config',
    type=click.Path(exists=False, path_type=Path),
    help='Path to configuration file'
)
@click.option(
    '--port',
    default=8765,
    type=int,
    help='Server port to listen on'
)
@click.option(
    '--max-controllers',
    default=4,
    type=int,
    help='Maximum number of virtual controllers'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def main(
    config: Optional[Path], 
    port: int, 
    max_controllers: int, 
    verbose: bool
) -> None:
    """Input Link Receiver - Simulate controller inputs from network."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create receiver app
    app = ReceiverApp(config)
    
    # Override config if command line options provided
    if config is None and (port != 8765 or max_controllers != 4):
        # Create temporary config with command line values
        from ..models import SenderConfig, ReceiverConfig
        app.config = ConfigModel(
            sender_config=SenderConfig(receiver_host="127.0.0.1"),
            receiver_config=ReceiverConfig(
                listen_port=port,
                max_controllers=max_controllers
            )
        )
    
    # Run application
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()