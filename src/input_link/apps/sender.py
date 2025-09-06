"""Sender application for capturing and forwarding controller inputs."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from ..core import ControllerManager, InputCaptureEngine
from ..network import WebSocketClient
from ..models import ConfigModel


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SenderApp:
    """Sender application for Input Link."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize sender application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or Path.home() / ".input-link" / "config.json"
        self.config: Optional[ConfigModel] = None
        self.controller_manager: Optional[ControllerManager] = None
        self.input_engine: Optional[InputCaptureEngine] = None
        self.websocket_client: Optional[WebSocketClient] = None
        self.running = False
        
    async def start(self) -> None:
        """Start the sender application."""
        try:
            # Load configuration
            await self._load_config()
            
            # Initialize components
            await self._initialize_components()
            
            # Start services
            await self._start_services()
            
            self.running = True
            logger.info("Sender application started successfully")
            
            # Run main loop
            await self._main_loop()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Failed to start sender application: {e}")
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
        # Initialize controller manager
        self.controller_manager = ControllerManager(auto_assign_numbers=True)
        self.controller_manager.initialize()
        
        # Initialize input capture engine
        self.input_engine = InputCaptureEngine(
            self.controller_manager,
            input_callback=self._on_controller_input
        )
        
        # Initialize WebSocket client
        self.websocket_client = WebSocketClient(
            host=self.config.sender_config.receiver_host,
            port=self.config.sender_config.receiver_port,
            reconnect_interval=self.config.sender_config.retry_interval,
            max_reconnect_attempts=self.config.sender_config.max_retry_attempts
        )
        
        logger.info("Components initialized")
    
    async def _start_services(self) -> None:
        """Start application services.""" 
        # Start WebSocket client
        await self.websocket_client.start()
        
        # Scan for controllers
        controllers = self.controller_manager.scan_controllers()
        logger.info(f"Found {len(controllers)} controller(s)")
        
        for controller in controllers:
            logger.info(f"  - {controller.name} (Number: {controller.assigned_number})")
        
        # Start input capture
        self.input_engine.start_capture()
        
        logger.info("Services started")
    
    async def _main_loop(self) -> None:
        """Main application loop."""
        logger.info("Sender running - Press Ctrl+C to stop")
        
        try:
            while self.running:
                # Periodically scan for new controllers
                self.controller_manager.scan_controllers()
                
                # Sleep to prevent busy waiting
                await asyncio.sleep(5.0)
                
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
    
    async def _on_controller_input(self, input_data) -> None:
        """Handle controller input data.
        
        Args:
            input_data: Controller input data
        """
        if self.websocket_client and self.websocket_client.connected:
            await self.websocket_client.send_controller_input(input_data)
    
    async def _cleanup(self) -> None:
        """Cleanup application resources.""" 
        logger.info("Cleaning up...")
        
        self.running = False
        
        # Stop input capture
        if self.input_engine:
            self.input_engine.stop_capture()
        
        # Stop WebSocket client
        if self.websocket_client:
            await self.websocket_client.stop()
        
        # Cleanup controller manager
        if self.controller_manager:
            self.controller_manager.cleanup()
        
        logger.info("Cleanup complete")


@click.command()
@click.option(
    '--config', 
    type=click.Path(exists=False, path_type=Path),
    help='Path to configuration file'
)
@click.option(
    '--host',
    default="127.0.0.1",
    help='Receiver host address'
)
@click.option(
    '--port',
    default=8765,
    type=int,
    help='Receiver port'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def main(config: Optional[Path], host: str, port: int, verbose: bool) -> None:
    """Input Link Sender - Capture and forward controller inputs."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create sender app
    app = SenderApp(config)
    
    # Override config if command line options provided
    if config is None and (host != "127.0.0.1" or port != 8765):
        # Create temporary config with command line values
        from ..models import SenderConfig, ReceiverConfig
        app.config = ConfigModel(
            sender_config=SenderConfig(receiver_host=host, receiver_port=port),
            receiver_config=ReceiverConfig()
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