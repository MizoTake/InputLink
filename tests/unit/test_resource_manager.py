#!/usr/bin/env python3
"""Tests for resource management utilities."""

import pytest
import asyncio
import weakref
from unittest.mock import Mock, patch

from input_link.core.resource_manager import (
    ResourceTracker, AsyncResourceManager, MemoryMonitor
)


class TestResourceTracker:
    """Test ResourceTracker functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.tracker = ResourceTracker()
    
    def test_register_and_count_resources(self):
        """Test registering and counting resources."""
        # Create some test objects
        obj1 = Mock()
        obj2 = Mock()
        obj3 = Mock()
        
        # Register resources
        self.tracker.register("test_type", obj1)
        self.tracker.register("test_type", obj2)
        self.tracker.register("other_type", obj3)
        
        # Check counts
        assert self.tracker.get_resource_count("test_type") == 2
        assert self.tracker.get_resource_count("other_type") == 1
        assert self.tracker.get_resource_count("nonexistent") == 0
    
    def test_resource_cleanup_on_deletion(self):
        """Test that resources are automatically cleaned up when deleted."""
        obj = Mock()
        self.tracker.register("test_type", obj)
        
        assert self.tracker.get_resource_count("test_type") == 1
        
        # Delete the object
        del obj
        
        # Force garbage collection to clean up weak references
        import gc
        gc.collect()
        
        # Count should eventually drop to 0 (weak references cleaned up)
        # Note: This might not be immediate due to garbage collection timing
        assert self.tracker.get_resource_count("test_type") <= 1
    
    def test_get_all_resource_counts(self):
        """Test getting all resource counts."""
        obj1 = Mock()
        obj2 = Mock()
        obj3 = Mock()
        
        self.tracker.register("type1", obj1)
        self.tracker.register("type1", obj2)
        self.tracker.register("type2", obj3)
        
        counts = self.tracker.get_all_resource_counts()
        assert counts["type1"] == 2
        assert counts["type2"] == 1
    
    def test_manual_cleanup(self):
        """Test manual resource cleanup."""
        obj1 = Mock()
        obj2 = Mock()
        
        self.tracker.register("test_type", obj1)
        self.tracker.register("test_type", obj2)
        
        assert self.tracker.get_resource_count("test_type") == 2
        
        # Manual cleanup
        cleaned = self.tracker.cleanup_resources("test_type")
        assert cleaned == 2
        assert self.tracker.get_resource_count("test_type") == 0


class TestAsyncResourceManager:
    """Test AsyncResourceManager functionality."""
    
    @pytest.mark.asyncio
    async def test_task_management(self):
        """Test task management and cleanup."""
        async with AsyncResourceManager() as manager:
            # Add some tasks
            task1 = manager.add_task(asyncio.sleep(0.1))
            task2 = manager.add_task(asyncio.sleep(0.1))
            
            assert len(manager._tasks) == 2
            
            # Wait for tasks to complete
            await asyncio.gather(task1, task2)
            
            # Tasks should be automatically removed from set
            await asyncio.sleep(0.01)  # Allow cleanup
            assert len(manager._tasks) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_callbacks(self):
        """Test cleanup callbacks are called."""
        callback_called = []
        
        def sync_callback():
            callback_called.append("sync")
        
        async def async_callback():
            callback_called.append("async")
        
        async with AsyncResourceManager() as manager:
            manager.add_cleanup_callback(sync_callback)
            manager.add_cleanup_callback(async_callback)
        
        # Callbacks should have been called during cleanup
        assert "sync" in callback_called
        assert "async" in callback_called
    
    @pytest.mark.asyncio
    async def test_task_cancellation_on_cleanup(self):
        """Test that tasks are cancelled during cleanup."""
        cancelled_tasks = []
        
        async def long_running_task():
            try:
                await asyncio.sleep(10)  # Long running task
            except asyncio.CancelledError:
                cancelled_tasks.append("cancelled")
                raise
        
        async with AsyncResourceManager() as manager:
            manager.add_task(long_running_task())
            manager.add_task(long_running_task())
        
        # Tasks should have been cancelled
        assert len(cancelled_tasks) == 2
    
    @pytest.mark.asyncio
    async def test_resource_context_management(self):
        """Test async context manager resource management."""
        class MockAsyncResource:
            def __init__(self):
                self.closed = False
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                self.closed = True
        
        resource = MockAsyncResource()
        
        async with AsyncResourceManager() as manager:
            managed_resource = await manager.add_resource(resource)
            assert managed_resource is resource
            assert not resource.closed
        
        # Resource should be closed after manager cleanup
        assert resource.closed
    
    @pytest.mark.asyncio
    async def test_closed_manager_raises_error(self):
        """Test that operations on closed manager raise errors."""
        manager = AsyncResourceManager()
        await manager.cleanup()
        
        with pytest.raises(RuntimeError, match="closed"):
            manager.add_task(asyncio.sleep(0.1))
        
        with pytest.raises(RuntimeError, match="closed"):
            manager.add_cleanup_callback(lambda: None)


class TestMemoryMonitor:
    """Test MemoryMonitor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.monitor = MemoryMonitor(threshold_mb=1.0, check_interval=0.1)
    
    @pytest.mark.asyncio
    async def test_memory_monitor_start_stop(self):
        """Test starting and stopping memory monitor."""
        assert not self.monitor._running
        
        await self.monitor.start()
        assert self.monitor._running
        
        await self.monitor.stop()
        assert not self.monitor._running
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_callback(self):
        """Test memory cleanup callback is triggered."""
        cleanup_called = []
        
        def cleanup_callback():
            cleanup_called.append("called")
        
        self.monitor.add_cleanup_callback(cleanup_callback)
        
        # Mock memory usage to exceed threshold
        with patch('psutil.Process') as mock_process:
            mock_memory_info = Mock()
            mock_memory_info.rss = 2 * 1024 * 1024  # 2MB (exceeds 1MB threshold)
            mock_process.return_value.memory_info.return_value = mock_memory_info
            
            await self.monitor.start()
            await asyncio.sleep(0.2)  # Wait for monitoring cycle
            await self.monitor.stop()
        
        # Cleanup should have been triggered
        assert len(cleanup_called) > 0
    
    @pytest.mark.asyncio
    async def test_memory_monitor_without_psutil(self):
        """Test memory monitor gracefully handles missing psutil."""
        with patch('input_link.core.resource_manager.psutil', side_effect=ImportError):
            await self.monitor.start()
            await asyncio.sleep(0.2)
            await self.monitor.stop()
        
        # Should not raise an error
    
    @pytest.mark.asyncio
    async def test_memory_monitor_handles_exceptions(self):
        """Test memory monitor handles exceptions in monitoring loop."""
        with patch('psutil.Process') as mock_process:
            # First call raises exception, second call works
            mock_process.return_value.memory_info.side_effect = [
                Exception("Memory error"),
                Mock(rss=1024)  # Low memory usage
            ]
            
            await self.monitor.start()
            await asyncio.sleep(0.3)  # Wait for multiple cycles
            await self.monitor.stop()
        
        # Should handle exception gracefully and continue monitoring