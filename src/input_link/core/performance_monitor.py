"""Performance monitoring and optimization utilities."""

from __future__ import annotations

import asyncio
import logging
import time
import statistics
from collections import deque
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    name: str
    execution_times: deque = field(default_factory=lambda: deque(maxlen=100))
    call_count: int = 0
    error_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    
    def add_execution(self, execution_time: float, success: bool = True):
        """Add execution time measurement."""
        self.execution_times.append(execution_time)
        self.call_count += 1
        self.total_time += execution_time
        
        if success:
            self.min_time = min(self.min_time, execution_time)
            self.max_time = max(self.max_time, execution_time)
        else:
            self.error_count += 1
    
    @property
    def average_time(self) -> float:
        """Get average execution time."""
        if self.call_count == 0:
            return 0.0
        return self.total_time / self.call_count
    
    @property
    def recent_average(self) -> float:
        """Get average of recent executions."""
        if not self.execution_times:
            return 0.0
        return statistics.mean(self.execution_times)
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.call_count == 0:
            return 100.0
        return ((self.call_count - self.error_count) / self.call_count) * 100
    
    def reset(self):
        """Reset all metrics."""
        self.execution_times.clear()
        self.call_count = 0
        self.error_count = 0
        self.total_time = 0.0
        self.min_time = float('inf')
        self.max_time = 0.0


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self._metrics: Dict[str, PerformanceMetrics] = {}
        self._thresholds: Dict[str, float] = {}
        self._warning_callbacks: List[Callable[[str, float], None]] = []
    
    def add_warning_callback(self, callback: Callable[[str, float], None]):
        """Add callback for performance warnings."""
        self._warning_callbacks.append(callback)
    
    def set_threshold(self, name: str, threshold_ms: float):
        """Set performance threshold for a metric."""
        self._thresholds[name] = threshold_ms / 1000.0  # Convert to seconds
    
    @contextmanager
    def measure(self, name: str):
        """Context manager to measure execution time."""
        start_time = time.perf_counter()
        success = True
        
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            # Record metrics
            if name not in self._metrics:
                self._metrics[name] = PerformanceMetrics(name)
            
            self._metrics[name].add_execution(execution_time, success)
            
            # Check threshold
            if name in self._thresholds and execution_time > self._thresholds[name]:
                self._trigger_warning(name, execution_time * 1000)  # Convert to ms
    
    def get_metrics(self, name: str) -> Optional[PerformanceMetrics]:
        """Get metrics for a specific operation."""
        return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get all metrics."""
        return self._metrics.copy()
    
    def reset_metrics(self, name: Optional[str] = None):
        """Reset metrics for specific operation or all operations."""
        if name:
            if name in self._metrics:
                self._metrics[name].reset()
        else:
            for metrics in self._metrics.values():
                metrics.reset()
    
    def get_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all metrics."""
        summary = {}
        for name, metrics in self._metrics.items():
            summary[name] = {
                'call_count': metrics.call_count,
                'error_count': metrics.error_count,
                'success_rate': metrics.success_rate,
                'average_time_ms': metrics.average_time * 1000,
                'recent_average_ms': metrics.recent_average * 1000,
                'min_time_ms': metrics.min_time * 1000 if metrics.min_time != float('inf') else 0,
                'max_time_ms': metrics.max_time * 1000,
                'total_time_ms': metrics.total_time * 1000,
            }
        return summary
    
    def _trigger_warning(self, name: str, execution_time_ms: float):
        """Trigger performance warning callbacks."""
        logger.warning(f"Performance threshold exceeded for {name}: {execution_time_ms:.2f}ms")
        for callback in self._warning_callbacks:
            try:
                callback(name, execution_time_ms)
            except Exception as e:
                logger.error(f"Error in performance warning callback: {e}")


class AsyncPerformanceMonitor:
    """Async version of performance monitor."""
    
    def __init__(self):
        self._monitor = PerformanceMonitor()
        self._async_metrics: Dict[str, deque] = {}
    
    def add_warning_callback(self, callback: Callable[[str, float], None]):
        """Add callback for performance warnings."""
        self._monitor.add_warning_callback(callback)
    
    def set_threshold(self, name: str, threshold_ms: float):
        """Set performance threshold for a metric."""
        self._monitor.set_threshold(name, threshold_ms)
    
    @contextmanager
    def measure(self, name: str):
        """Context manager to measure execution time."""
        with self._monitor.measure(name):
            yield
    
    async def measure_async(self, name: str, coro):
        """Measure async coroutine execution time."""
        start_time = time.perf_counter()
        success = True
        
        try:
            result = await coro
            return result
        except Exception:
            success = False
            raise
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            # Record metrics
            if name not in self._monitor._metrics:
                self._monitor._metrics[name] = PerformanceMetrics(name)
            
            self._monitor._metrics[name].add_execution(execution_time, success)
            
            # Check threshold
            if name in self._monitor._thresholds and execution_time > self._monitor._thresholds[name]:
                self._monitor._trigger_warning(name, execution_time * 1000)
    
    def get_metrics(self, name: str) -> Optional[PerformanceMetrics]:
        """Get metrics for a specific operation."""
        return self._monitor.get_metrics(name)
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get all metrics."""
        return self._monitor.get_all_metrics()
    
    def get_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all metrics."""
        return self._monitor.get_summary()
    
    def reset_metrics(self, name: Optional[str] = None):
        """Reset metrics."""
        self._monitor.reset_metrics(name)


class RateLimiter:
    """Rate limiter to prevent overwhelming operations."""
    
    def __init__(self, max_calls: int, time_window: float):
        """Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self._calls: deque = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to proceed (async version)."""
        async with self._lock:
            now = time.time()
            
            # Remove old calls outside the time window
            while self._calls and self._calls[0] <= now - self.time_window:
                self._calls.popleft()
            
            # Check if we can proceed
            if len(self._calls) >= self.max_calls:
                # Calculate wait time
                wait_time = self.time_window - (now - self._calls[0])
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    return await self.acquire()  # Recursive call after waiting
            
            # Record this call
            self._calls.append(now)
            return True
    
    def try_acquire(self) -> bool:
        """Try to acquire permission without waiting (sync version)."""
        now = time.time()
        
        # Remove old calls outside the time window
        while self._calls and self._calls[0] <= now - self.time_window:
            self._calls.popleft()
        
        # Check if we can proceed
        if len(self._calls) >= self.max_calls:
            return False
        
        # Record this call
        self._calls.append(now)
        return True
    
    def reset(self):
        """Reset the rate limiter."""
        self._calls.clear()
    
    @property
    def current_rate(self) -> float:
        """Get current call rate per second."""
        now = time.time()
        
        # Remove old calls
        while self._calls and self._calls[0] <= now - self.time_window:
            self._calls.popleft()
        
        return len(self._calls) / self.time_window


class OperationCache:
    """Cache for expensive operations with TTL support."""
    
    def __init__(self, max_size: int = 128, default_ttl: float = 300.0):
        """Initialize operation cache.
        
        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self._access_order: deque = deque()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str, factory_func: Optional[Callable] = None, ttl: Optional[float] = None):
        """Get value from cache or compute it."""
        async with self._lock:
            now = time.time()
            
            # Check if key exists and is not expired
            if key in self._cache:
                value, expiry_time = self._cache[key]
                if now < expiry_time:
                    # Move to end (most recently used)
                    self._access_order.remove(key)
                    self._access_order.append(key)
                    return value
                else:
                    # Expired, remove from cache
                    del self._cache[key]
                    self._access_order.remove(key)
            
            # Not in cache or expired, compute new value
            if factory_func is None:
                return None
            
            # Compute new value
            if asyncio.iscoroutinefunction(factory_func):
                value = await factory_func()
            else:
                value = factory_func()
            
            # Store in cache
            ttl = ttl or self.default_ttl
            expiry_time = now + ttl
            
            # Ensure cache size limit
            while len(self._cache) >= self.max_size:
                # Remove least recently used
                oldest_key = self._access_order.popleft()
                del self._cache[oldest_key]
            
            self._cache[key] = (value, expiry_time)
            self._access_order.append(key)
            
            return value
    
    def invalidate(self, key: str):
        """Invalidate a cached value."""
        if key in self._cache:
            del self._cache[key]
            self._access_order.remove(key)
    
    def clear(self):
        """Clear all cached values."""
        self._cache.clear()
        self._access_order.clear()
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        now = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self._cache.items()
            if now >= expiry_time
        ]
        
        for key in expired_keys:
            self.invalidate(key)
        
        return len(expired_keys)


# Global performance monitor instances
_performance_monitor = PerformanceMonitor()
_async_performance_monitor = AsyncPerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _performance_monitor

def get_async_performance_monitor() -> AsyncPerformanceMonitor:
    """Get the global async performance monitor instance."""
    return _async_performance_monitor