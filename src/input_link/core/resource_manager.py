"""Resource management utilities for Input Link application."""

from __future__ import annotations

import asyncio
import logging
import threading
import weakref
from contextlib import AsyncExitStack
from typing import Dict, List, Optional, Set, Any

logger = logging.getLogger(__name__)


class ResourceTracker:
    """Track and manage application resources to prevent memory leaks."""
    
    def __init__(self):
        self._resources: Dict[str, weakref.WeakSet] = {}
        self._lock = threading.Lock()
    
    def register(self, resource_type: str, resource: Any) -> None:
        """Register a resource for tracking."""
        with self._lock:
            if resource_type not in self._resources:
                self._resources[resource_type] = weakref.WeakSet()
            self._resources[resource_type].add(resource)
            logger.debug(f"Registered {resource_type}: {resource}")
    
    def unregister(self, resource_type: str, resource: Any) -> None:
        """Unregister a resource."""
        with self._lock:
            if resource_type in self._resources:
                try:
                    self._resources[resource_type].discard(resource)
                    logger.debug(f"Unregistered {resource_type}: {resource}")
                except KeyError:
                    pass  # Resource already removed or garbage collected
    
    def get_resource_count(self, resource_type: str) -> int:
        """Get count of registered resources of a specific type."""
        with self._lock:
            if resource_type not in self._resources:
                return 0
            return len(self._resources[resource_type])
    
    def get_all_resource_counts(self) -> Dict[str, int]:
        """Get counts of all registered resource types."""
        with self._lock:
            return {
                resource_type: len(resource_set)
                for resource_type, resource_set in self._resources.items()
            }
    
    def cleanup_resources(self, resource_type: str) -> int:
        """Force cleanup of resources of a specific type."""
        with self._lock:
            if resource_type not in self._resources:
                return 0
            
            resource_set = self._resources[resource_type]
            initial_count = len(resource_set)
            
            # Force cleanup by creating a new WeakSet
            self._resources[resource_type] = weakref.WeakSet()
            
            cleaned_count = initial_count
            logger.info(f"Cleaned up {cleaned_count} {resource_type} resources")
            return cleaned_count


class AsyncResourceManager:
    """Manages async resources with proper cleanup."""
    
    def __init__(self):
        self._exit_stack = AsyncExitStack()
        self._tasks: Set[asyncio.Task] = set()
        self._cleanup_callbacks: List = []
        self._closed = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def add_resource(self, resource):
        """Add a resource that supports async context management."""
        if self._closed:
            raise RuntimeError("ResourceManager is closed")
        return await self._exit_stack.enter_async_context(resource)
    
    def add_task(self, coro) -> asyncio.Task:
        """Add a task to be managed."""
        if self._closed:
            raise RuntimeError("ResourceManager is closed")
        
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        
        # Clean up task from set when it completes
        task.add_done_callback(lambda t: self._tasks.discard(t))
        
        return task
    
    def add_cleanup_callback(self, callback):
        """Add a cleanup callback to be called during shutdown."""
        if self._closed:
            raise RuntimeError("ResourceManager is closed")
        self._cleanup_callbacks.append(callback)
    
    async def cleanup(self):
        """Clean up all managed resources."""
        if self._closed:
            return
        
        self._closed = True
        logger.info("Starting async resource cleanup")
        
        try:
            # Cancel all tasks
            for task in list(self._tasks):
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self._tasks:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            
            # Run cleanup callbacks
            for callback in reversed(self._cleanup_callbacks):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Error in cleanup callback: {e}")
            
            # Cleanup managed resources
            await self._exit_stack.aclose()
            
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")
        finally:
            self._tasks.clear()
            self._cleanup_callbacks.clear()
            logger.info("Async resource cleanup complete")


class ConnectionPool:
    """Manages connection pooling for network resources."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._connections: List = []
        self._in_use: Set = set()
        self._lock = asyncio.Lock()
        self._closed = False
    
    async def acquire(self):
        """Acquire a connection from the pool."""
        async with self._lock:
            if self._closed:
                raise RuntimeError("Connection pool is closed")
            
            # Try to reuse existing connection
            for conn in self._connections:
                if conn not in self._in_use:
                    self._in_use.add(conn)
                    return conn
            
            # Create new connection if under limit
            if len(self._connections) < self.max_connections:
                conn = await self._create_connection()
                self._connections.append(conn)
                self._in_use.add(conn)
                return conn
            
            # All connections in use
            raise RuntimeError("No available connections")
    
    async def release(self, connection):
        """Release a connection back to the pool."""
        async with self._lock:
            self._in_use.discard(connection)
    
    async def close_all(self):
        """Close all connections in the pool."""
        async with self._lock:
            self._closed = True
            
            for conn in self._connections:
                try:
                    await self._close_connection(conn)
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            
            self._connections.clear()
            self._in_use.clear()
    
    async def _create_connection(self):
        """Override to create actual connections."""
        raise NotImplementedError
    
    async def _close_connection(self, connection):
        """Override to close actual connections."""
        raise NotImplementedError


class MemoryMonitor:
    """Monitor memory usage and trigger cleanup when needed."""
    
    def __init__(self, threshold_mb: float = 100.0, check_interval: float = 30.0):
        self.threshold_bytes = threshold_mb * 1024 * 1024
        self.check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._cleanup_callbacks: List = []
    
    def add_cleanup_callback(self, callback):
        """Add callback to be called when memory threshold is exceeded."""
        self._cleanup_callbacks.append(callback)
    
    async def start(self):
        """Start memory monitoring."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started memory monitor (threshold: {self.threshold_bytes/1024/1024:.1f}MB)")
    
    async def stop(self):
        """Stop memory monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped memory monitor")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        try:
            import psutil
            process = psutil.Process()
            
            while self._running:
                try:
                    memory_info = process.memory_info()
                    memory_usage = memory_info.rss
                    
                    if memory_usage > self.threshold_bytes:
                        logger.warning(f"Memory usage high: {memory_usage/1024/1024:.1f}MB")
                        await self._trigger_cleanup()
                    
                    await asyncio.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in memory monitoring: {e}")
                    await asyncio.sleep(self.check_interval)
                    
        except ImportError:
            logger.warning("psutil not available, memory monitoring disabled")
        except asyncio.CancelledError:
            logger.debug("Memory monitor cancelled")
    
    async def _trigger_cleanup(self):
        """Trigger cleanup callbacks."""
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in memory cleanup callback: {e}")


# Global resource tracker instance
_resource_tracker = ResourceTracker()

def get_resource_tracker() -> ResourceTracker:
    """Get the global resource tracker instance."""
    return _resource_tracker