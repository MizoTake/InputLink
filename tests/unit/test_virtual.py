"""Tests for virtual controller management."""

import pytest
import asyncio
import platform
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from input_link.virtual import VirtualControllerManager, VirtualController, VirtualControllerFactory
from input_link.models import ControllerInputData, ButtonState, ControllerState


class MockVirtualController(VirtualController):
    """Mock virtual controller for testing."""
    
    def __init__(self, controller_number: int):
        super().__init__(controller_number)
        self.connect_called = False
        self.disconnect_called = False
        self.update_called = False
        self.reset_called = False
        self.last_input_data = None
        self.should_connect = True
        
    async def connect(self) -> bool:
        self.connect_called = True
        if self.should_connect:
            self._connected = True
            return True
        return False
    
    async def disconnect(self) -> None:
        self.disconnect_called = True
        self._connected = False
    
    async def update_state(self, input_data: ControllerInputData) -> bool:
        self.update_called = True
        self.last_input_data = input_data
        return True
    
    def reset_state(self) -> None:
        self.reset_called = True


class TestVirtualControllerFactory:
    """Test virtual controller factory."""
    
    @patch('platform.system')
    def test_create_windows_controller(self, mock_system):
        """Should create Windows controller on Windows platform."""
        mock_system.return_value = "Windows"
        
        with patch('input_link.virtual.base.VirtualControllerFactory._create_windows_controller') as mock_create:
            mock_controller = Mock()
            mock_create.return_value = mock_controller
            
            result = VirtualControllerFactory.create_controller(1)
            
            assert result == mock_controller
            mock_create.assert_called_once_with(1)
    
    @patch('platform.system')
    def test_create_macos_controller(self, mock_system):
        """Should create macOS controller on Darwin platform."""
        mock_system.return_value = "Darwin"
        
        with patch('input_link.virtual.base.VirtualControllerFactory._create_macos_controller') as mock_create:
            mock_controller = Mock()
            mock_create.return_value = mock_controller
            
            result = VirtualControllerFactory.create_controller(1)
            
            assert result == mock_controller
            mock_create.assert_called_once_with(1)
    
    @patch('platform.system')
    def test_create_unsupported_platform(self, mock_system):
        """Should return None for unsupported platforms."""
        mock_system.return_value = "Linux"
        
        result = VirtualControllerFactory.create_controller(1)
        
        assert result is None
    
    @patch('platform.system')
    def test_create_windows_controller_import_error(self, mock_system):
        """Should handle import errors gracefully."""
        mock_system.return_value = "Windows"
        
        with patch('input_link.virtual.base.VirtualControllerFactory._create_windows_controller') as mock_create:
            mock_create.return_value = None  # Simulate the factory returning None on error
            
            result = VirtualControllerFactory.create_controller(1)
            
            assert result is None


class TestVirtualControllerManager:
    """Test virtual controller manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = VirtualControllerManager(max_controllers=4)
        
        # Patch factory to return mock controllers
        self.factory_patcher = patch.object(
            VirtualControllerFactory, 
            'create_controller',
            side_effect=self._create_mock_controller
        )
        self.factory_patcher.start()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.factory_patcher.stop()
        
        # Ensure manager is stopped
        if hasattr(self.manager, '_running') and self.manager._running:
            asyncio.run(self.manager.stop())
    
    def _create_mock_controller(self, controller_number: int, **kwargs):
        """Create mock controller."""
        return MockVirtualController(controller_number)
    
    def test_initial_state(self):
        """Should have correct initial state."""
        assert not self.manager._running
        assert self.manager.active_controller_count == 0
        assert self.manager.controller_numbers == []
    
    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self):
        """Should handle start/stop lifecycle correctly."""
        await self.manager.start()
        assert self.manager._running
        
        await self.manager.stop()
        assert not self.manager._running
    
    @pytest.mark.asyncio
    async def test_create_controller_success(self):
        """Should create controller successfully."""
        await self.manager.start()
        
        success = await self.manager.create_controller(1)
        assert success
        assert 1 in self.manager._controllers
        assert self.manager.active_controller_count == 1
        
        controller = self.manager._controllers[1]
        assert controller.connect_called
        assert controller.connected
    
    @pytest.mark.asyncio
    async def test_create_controller_not_running(self):
        """Should reject creation when not running."""
        success = await self.manager.create_controller(1)
        assert not success
    
    @pytest.mark.asyncio
    async def test_create_controller_invalid_number(self):
        """Should reject invalid controller numbers."""
        await self.manager.start()
        
        success = await self.manager.create_controller(0)
        assert not success
        
        success = await self.manager.create_controller(9)
        assert not success
    
    @pytest.mark.asyncio
    async def test_create_controller_already_exists(self):
        """Should handle existing controller gracefully."""
        await self.manager.start()
        
        # Create first time
        success1 = await self.manager.create_controller(1)
        assert success1
        
        # Create second time (should succeed but not create new)
        success2 = await self.manager.create_controller(1)
        assert success2
        assert self.manager.active_controller_count == 1
    
    @pytest.mark.asyncio
    async def test_create_controller_max_limit(self):
        """Should respect maximum controller limit.""" 
        manager = VirtualControllerManager(max_controllers=2)
        
        with patch.object(VirtualControllerFactory, 'create_controller', side_effect=self._create_mock_controller):
            await manager.start()
            
            # Create up to limit
            assert await manager.create_controller(1)
            assert await manager.create_controller(2)
            assert manager.active_controller_count == 2
            
            # Should reject beyond limit
            success = await manager.create_controller(3)
            assert not success
            assert manager.active_controller_count == 2
    
    @pytest.mark.asyncio
    async def test_remove_controller_success(self):
        """Should remove controller successfully."""
        await self.manager.start()
        await self.manager.create_controller(1)
        
        success = await self.manager.remove_controller(1)
        assert success
        assert 1 not in self.manager._controllers
        assert self.manager.active_controller_count == 0
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_controller(self):
        """Should handle removing nonexistent controller."""
        await self.manager.start()
        
        success = await self.manager.remove_controller(1)
        assert not success
    
    @pytest.mark.asyncio
    async def test_update_controller_state_existing(self):
        """Should update existing controller state."""
        await self.manager.start()
        await self.manager.create_controller(1)
        
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test"
        )
        
        success = await self.manager.update_controller_state(input_data)
        assert success
        
        controller = self.manager._controllers[1]
        assert controller.update_called
        assert controller.last_input_data == input_data
    
    @pytest.mark.asyncio
    async def test_update_controller_state_auto_create(self):
        """Should auto-create controller when enabled."""
        manager = VirtualControllerManager(auto_create=True)
        
        with patch.object(VirtualControllerFactory, 'create_controller', side_effect=self._create_mock_controller):
            await manager.start()
            
            input_data = ControllerInputData(
                controller_number=1,
                controller_id="test"
            )
            
            success = await manager.update_controller_state(input_data)
            assert success
            assert 1 in manager._controllers
            assert manager.active_controller_count == 1
    
    @pytest.mark.asyncio
    async def test_update_controller_state_no_auto_create(self):
        """Should not auto-create when disabled."""
        manager = VirtualControllerManager(auto_create=False)
        await manager.start()
        
        input_data = ControllerInputData(
            controller_number=1,
            controller_id="test"
        )
        
        success = await manager.update_controller_state(input_data)
        assert not success
        assert manager.active_controller_count == 0
    
    @pytest.mark.asyncio
    async def test_reset_controller(self):
        """Should reset specific controller."""
        await self.manager.start()
        await self.manager.create_controller(1)
        
        success = await self.manager.reset_controller(1)
        assert success
        
        controller = self.manager._controllers[1]
        assert controller.reset_called
    
    @pytest.mark.asyncio
    async def test_reset_nonexistent_controller(self):
        """Should handle resetting nonexistent controller."""
        await self.manager.start()
        
        success = await self.manager.reset_controller(1)
        assert not success
    
    @pytest.mark.asyncio
    async def test_reset_all_controllers(self):
        """Should reset all controllers."""
        await self.manager.start()
        await self.manager.create_controller(1)
        await self.manager.create_controller(2)
        
        await self.manager.reset_all_controllers()
        
        for controller in self.manager._controllers.values():
            assert controller.reset_called
    
    def test_get_controller_info(self):
        """Should return controller information.""" 
        # Manually add mock controller for this test
        mock_controller = MockVirtualController(1)
        mock_controller._connected = True
        self.manager._controllers[1] = mock_controller
        
        info = self.manager.get_controller_info()
        
        assert len(info) == 1
        assert info[0]["controller_number"] == 1
        assert info[0]["connected"] is True
        assert info[0]["controller_type"] == "MockVirtualController"
        assert info[0]["controller_obj"] == mock_controller
    
    def test_is_controller_active(self):
        """Should check controller active status correctly."""
        # Test nonexistent controller
        assert not self.manager.is_controller_active(1)
        
        # Test existing but disconnected controller
        mock_controller = MockVirtualController(1)
        mock_controller._connected = False
        self.manager._controllers[1] = mock_controller
        assert not self.manager.is_controller_active(1)
        
        # Test existing and connected controller
        mock_controller._connected = True
        assert self.manager.is_controller_active(1)
    
    @pytest.mark.asyncio
    async def test_creation_callback(self):
        """Should call creation callback."""
        callback_calls = []
        
        def creation_callback(controller_number):
            callback_calls.append(controller_number)
        
        manager = VirtualControllerManager(creation_callback=creation_callback)
        
        with patch.object(VirtualControllerFactory, 'create_controller', side_effect=self._create_mock_controller):
            await manager.start()
            await manager.create_controller(1)
            
            assert callback_calls == [1]
    
    @pytest.mark.asyncio
    async def test_destruction_callback(self):
        """Should call destruction callback."""
        callback_calls = []
        
        def destruction_callback(controller_number):
            callback_calls.append(controller_number)
        
        manager = VirtualControllerManager(destruction_callback=destruction_callback)
        
        with patch.object(VirtualControllerFactory, 'create_controller', side_effect=self._create_mock_controller):
            await manager.start()
            await manager.create_controller(1)
            await manager.remove_controller(1)
            
            assert callback_calls == [1]
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Should work as async context manager."""
        with patch.object(VirtualControllerFactory, 'create_controller', side_effect=self._create_mock_controller):
            async with self.manager as manager:
                assert manager._running
                await manager.create_controller(1)
                assert manager.active_controller_count == 1
                
            assert not manager._running
            assert manager.active_controller_count == 0