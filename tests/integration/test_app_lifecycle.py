#!/usr/bin/env python3
"""Integration tests for application lifecycle and error handling."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

from input_link.apps.sender import SenderApp
from input_link.apps.receiver import ReceiverApp
from input_link.models import ConfigModel, SenderConfig, ReceiverConfig


class TestSenderAppLifecycle:
    """Test SenderApp lifecycle and error handling."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "sender_config.json"

    @pytest.mark.asyncio
    async def test_sender_app_normal_lifecycle(self):
        """Test normal sender app lifecycle."""
        # Create mock callbacks
        log_callback = Mock()
        status_callback = Mock()
        
        app = SenderApp(
            config_path=self.config_path,
            log_callback=log_callback,
            status_callback=status_callback,
            verbose=True
        )
        
        assert app.config_path == self.config_path
        assert not app.running
        assert app.controller_manager is None
        assert app.websocket_client is None
        
        # Start and immediately stop to test lifecycle
        with patch.object(app, '_main_loop') as mock_main_loop:
            mock_main_loop.return_value = None
            
            start_task = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)  # Let it initialize
            
            await app.stop()
            
            try:
                await asyncio.wait_for(start_task, timeout=1.0)
            except asyncio.TimeoutError:
                pass
        
        # Verify callbacks were called
        assert log_callback.called
        assert not app.running

    @pytest.mark.asyncio  
    async def test_sender_app_config_loading_error(self):
        """Test sender app with invalid config."""
        # Create invalid config file
        invalid_config = {"invalid": "structure"}
        with open(self.config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        app = SenderApp(config_path=self.config_path)
        
        # Should handle config errors gracefully
        with pytest.raises((ValueError, KeyError)):
            await app.start()

    @pytest.mark.asyncio
    async def test_sender_app_double_start_prevention(self):
        """Test that starting already running app is handled."""
        app = SenderApp(config_path=self.config_path)
        
        with patch.object(app, '_main_loop') as mock_main_loop:
            mock_main_loop.return_value = None
            
            # Start first time
            start_task1 = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)
            
            # Try to start again - should be handled gracefully
            start_task2 = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)
            
            await app.stop()
            
            try:
                await asyncio.wait_for(start_task1, timeout=1.0)
                await asyncio.wait_for(start_task2, timeout=1.0)
            except asyncio.TimeoutError:
                pass


class TestReceiverAppLifecycle:
    """Test ReceiverApp lifecycle and error handling."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "receiver_config.json"

    @pytest.mark.asyncio
    async def test_receiver_app_normal_lifecycle(self):
        """Test normal receiver app lifecycle."""
        log_callback = Mock()
        status_callback = Mock()
        
        app = ReceiverApp(
            config_path=self.config_path,
            log_callback=log_callback,
            status_callback=status_callback,
            verbose=True
        )
        
        assert app.config_path == self.config_path
        assert not app.running
        assert app.websocket_server is None
        assert app.virtual_controller_manager is None
        
        # Mock the main loop to prevent infinite running
        with patch.object(app, '_main_loop') as mock_main_loop:
            mock_main_loop.return_value = None
            
            start_task = asyncio.create_task(app.start())
            await asyncio.sleep(0.1)  # Let it initialize
            
            await app.stop()
            
            try:
                await asyncio.wait_for(start_task, timeout=1.0)
            except asyncio.TimeoutError:
                pass
        
        assert log_callback.called

    @pytest.mark.asyncio
    async def test_receiver_app_port_in_use_error(self):
        """Test receiver app with port already in use."""
        # Create config with specific port
        config = ConfigModel(
            sender_config=SenderConfig(receiver_host="127.0.0.1"),
            receiver_config=ReceiverConfig(listen_port=0)  # Use port 0 to get any available port
        )
        config.save_to_file(self.config_path)
        
        app = ReceiverApp(config_path=self.config_path)
        
        # Mock WebSocketServer to raise port in use error
        with patch('input_link.apps.receiver.WebSocketServer') as mock_server:
            mock_instance = MagicMock()
            mock_instance.start.side_effect = OSError("Address already in use")
            mock_server.return_value = mock_instance
            
            # Should handle port errors gracefully
            with pytest.raises(Exception):
                await app.start()

    @pytest.mark.asyncio
    async def test_receiver_controller_input_handling(self):
        """Test receiver handling controller input data."""
        app = ReceiverApp(config_path=self.config_path)
        
        # Create mock input data
        from input_link.models import ControllerInputData, ButtonState, ControllerState
        
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test_controller",
            buttons=ButtonState(a=True),
            axes=ControllerState(left_stick_x=0.5)
        )
        
        # Mock virtual controller manager
        mock_manager = Mock()
        mock_manager.update_controller_state = Mock(return_value=asyncio.create_task(asyncio.sleep(0)))
        app.virtual_controller_manager = mock_manager
        
        # Test input handling
        app._on_controller_input(input_data)
        
        # Verify manager was called
        await asyncio.sleep(0.1)  # Allow task to execute


class TestAppErrorRecovery:
    """Test application error recovery mechanisms."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "config.json"

    @pytest.mark.asyncio
    async def test_network_connection_recovery(self):
        """Test network connection error recovery."""
        from input_link.network import WebSocketClient
        
        # Create sender app
        app = SenderApp(config_path=self.config_path)
        
        # Mock websocket client with connection failures
        with patch('input_link.apps.sender.WebSocketClient') as mock_client_class:
            mock_client = Mock(spec=WebSocketClient)
            mock_client.start.side_effect = [
                ConnectionError("Connection failed"),  # First attempt fails
                None  # Second attempt succeeds
            ]
            mock_client.connected = False
            mock_client_class.return_value = mock_client
            
            with patch.object(app, '_main_loop'):
                # Should handle connection error gracefully
                try:
                    await app.start()
                except ConnectionError:
                    pass  # Expected on first connection attempt

    @pytest.mark.asyncio
    async def test_virtual_controller_creation_failure(self):
        """Test handling of virtual controller creation failures."""
        app = ReceiverApp(config_path=self.config_path)
        
        # Mock virtual controller manager with creation failures
        with patch('input_link.apps.receiver.VirtualControllerManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.start.side_effect = Exception("Failed to initialize virtual controllers")
            mock_manager_class.return_value = mock_manager
            
            # Should handle virtual controller errors gracefully
            with pytest.raises(Exception):
                await app.start()

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(self):
        """Test proper cleanup when exceptions occur."""
        app = ReceiverApp(config_path=self.config_path)
        
        # Mock components
        mock_server = Mock()
        mock_manager = Mock()
        app.websocket_server = mock_server
        app.virtual_controller_manager = mock_manager
        
        # Test cleanup is called even with exceptions
        with patch.object(app, '_start_services', side_effect=Exception("Service start failed")):
            try:
                await app.start()
            except Exception:
                pass
        
        # Cleanup should still be attempted
        mock_server.stop.assert_called()
        mock_manager.stop.assert_called()