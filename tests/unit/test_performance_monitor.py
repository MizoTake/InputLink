#!/usr/bin/env python3
"""Tests for performance monitoring utilities."""

import pytest
import asyncio
import time
from unittest.mock import Mock

from input_link.core.performance_monitor import (
    PerformanceMetrics, PerformanceMonitor, AsyncPerformanceMonitor,
    RateLimiter, OperationCache
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.metrics = PerformanceMetrics("test_operation")
    
    def test_initial_state(self):
        """Test initial state of metrics."""
        assert self.metrics.name == "test_operation"
        assert self.metrics.call_count == 0
        assert self.metrics.error_count == 0
        assert self.metrics.total_time == 0.0
        assert self.metrics.average_time == 0.0
        assert self.metrics.success_rate == 100.0
    
    def test_add_successful_execution(self):
        """Test adding successful execution."""
        self.metrics.add_execution(0.5, success=True)
        
        assert self.metrics.call_count == 1
        assert self.metrics.error_count == 0
        assert self.metrics.total_time == 0.5
        assert self.metrics.average_time == 0.5
        assert self.metrics.min_time == 0.5
        assert self.metrics.max_time == 0.5
        assert self.metrics.success_rate == 100.0
    
    def test_add_failed_execution(self):
        """Test adding failed execution."""
        self.metrics.add_execution(0.3, success=False)
        
        assert self.metrics.call_count == 1
        assert self.metrics.error_count == 1
        assert self.metrics.success_rate == 0.0
        # Min/max times should not be updated for failed executions
        assert self.metrics.min_time == float('inf')
        assert self.metrics.max_time == 0.0
    
    def test_multiple_executions(self):
        """Test multiple executions."""
        self.metrics.add_execution(0.1, success=True)
        self.metrics.add_execution(0.3, success=True)
        self.metrics.add_execution(0.2, success=False)
        
        assert self.metrics.call_count == 3
        assert self.metrics.error_count == 1
        assert self.metrics.total_time == 0.6
        assert self.metrics.average_time == 0.2
        assert self.metrics.min_time == 0.1
        assert self.metrics.max_time == 0.3
        assert abs(self.metrics.success_rate - 66.67) < 0.1  # 2/3 * 100
    
    def test_recent_average(self):
        """Test recent average calculation."""
        for i in range(5):
            self.metrics.add_execution(i * 0.1, success=True)
        
        # Recent average should be calculated from execution_times deque
        assert len(self.metrics.execution_times) == 5
        assert self.metrics.recent_average == 0.2  # Mean of [0.0, 0.1, 0.2, 0.3, 0.4]
    
    def test_reset_metrics(self):
        """Test resetting metrics."""
        self.metrics.add_execution(0.5, success=True)
        self.metrics.add_execution(0.3, success=False)
        
        self.metrics.reset()
        
        assert self.metrics.call_count == 0
        assert self.metrics.error_count == 0
        assert self.metrics.total_time == 0.0
        assert len(self.metrics.execution_times) == 0


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.monitor = PerformanceMonitor()
    
    def test_measure_context_manager(self):
        """Test measurement using context manager."""
        with self.monitor.measure("test_op"):
            time.sleep(0.01)  # Small delay
        
        metrics = self.monitor.get_metrics("test_op")
        assert metrics is not None
        assert metrics.call_count == 1
        assert metrics.average_time > 0.005  # Should be at least 5ms
    
    def test_measure_with_exception(self):
        """Test measurement when exception occurs."""
        with pytest.raises(ValueError):
            with self.monitor.measure("test_op"):
                raise ValueError("Test error")
        
        metrics = self.monitor.get_metrics("test_op")
        assert metrics is not None
        assert metrics.call_count == 1
        assert metrics.error_count == 1
        assert metrics.success_rate == 0.0
    
    def test_threshold_warning(self):
        """Test threshold warning trigger."""
        warnings_received = []
        
        def warning_callback(name, time_ms):
            warnings_received.append((name, time_ms))
        
        self.monitor.add_warning_callback(warning_callback)
        self.monitor.set_threshold("test_op", 5.0)  # 5ms threshold
        
        with self.monitor.measure("test_op"):
            time.sleep(0.01)  # 10ms - exceeds threshold
        
        assert len(warnings_received) == 1
        assert warnings_received[0][0] == "test_op"
        assert warnings_received[0][1] > 5.0
    
    def test_get_all_metrics(self):
        """Test getting all metrics."""
        with self.monitor.measure("op1"):
            time.sleep(0.001)
        
        with self.monitor.measure("op2"):
            time.sleep(0.002)
        
        all_metrics = self.monitor.get_all_metrics()
        assert len(all_metrics) == 2
        assert "op1" in all_metrics
        assert "op2" in all_metrics
    
    def test_get_summary(self):
        """Test getting metrics summary."""
        with self.monitor.measure("test_op"):
            time.sleep(0.001)
        
        summary = self.monitor.get_summary()
        assert "test_op" in summary
        assert "call_count" in summary["test_op"]
        assert "average_time_ms" in summary["test_op"]
        assert summary["test_op"]["call_count"] == 1
    
    def test_reset_specific_metrics(self):
        """Test resetting specific metrics."""
        with self.monitor.measure("op1"):
            pass
        with self.monitor.measure("op2"):
            pass
        
        self.monitor.reset_metrics("op1")
        
        assert self.monitor.get_metrics("op1").call_count == 0
        assert self.monitor.get_metrics("op2").call_count == 1
    
    def test_reset_all_metrics(self):
        """Test resetting all metrics."""
        with self.monitor.measure("op1"):
            pass
        with self.monitor.measure("op2"):
            pass
        
        self.monitor.reset_metrics()
        
        assert self.monitor.get_metrics("op1").call_count == 0
        assert self.monitor.get_metrics("op2").call_count == 0


class TestAsyncPerformanceMonitor:
    """Test AsyncPerformanceMonitor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.monitor = AsyncPerformanceMonitor()
    
    @pytest.mark.asyncio
    async def test_measure_async_operation(self):
        """Test measuring async operation."""
        async def test_coro():
            await asyncio.sleep(0.01)
            return "result"
        
        result = await self.monitor.measure_async("async_op", test_coro())
        
        assert result == "result"
        metrics = self.monitor.get_metrics("async_op")
        assert metrics is not None
        assert metrics.call_count == 1
        assert metrics.average_time > 0.005
    
    @pytest.mark.asyncio
    async def test_measure_async_with_exception(self):
        """Test measuring async operation that raises exception."""
        async def failing_coro():
            await asyncio.sleep(0.001)
            raise ValueError("Async error")
        
        with pytest.raises(ValueError):
            await self.monitor.measure_async("async_op", failing_coro())
        
        metrics = self.monitor.get_metrics("async_op")
        assert metrics is not None
        assert metrics.call_count == 1
        assert metrics.error_count == 1


class TestRateLimiter:
    """Test RateLimiter functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.limiter = RateLimiter(max_calls=3, time_window=1.0)
    
    @pytest.mark.asyncio
    async def test_rate_limiting_allows_calls_within_limit(self):
        """Test that calls within limit are allowed."""
        # Should allow 3 calls
        for i in range(3):
            result = await self.limiter.acquire()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limiting_blocks_excess_calls(self):
        """Test that excess calls are blocked/delayed."""
        # Fill up the limit
        for i in range(3):
            await self.limiter.acquire()
        
        # Next call should be delayed
        start_time = time.time()
        await self.limiter.acquire()
        end_time = time.time()
        
        # Should have waited at least some time
        assert end_time - start_time > 0.5  # Waited significant time
    
    def test_try_acquire_sync(self):
        """Test synchronous try_acquire method."""
        # Should allow 3 calls
        for i in range(3):
            result = self.limiter.try_acquire()
            assert result is True
        
        # 4th call should fail
        result = self.limiter.try_acquire()
        assert result is False
    
    def test_current_rate_calculation(self):
        """Test current rate calculation."""
        assert self.limiter.current_rate == 0.0
        
        # Make some calls
        for i in range(2):
            self.limiter.try_acquire()
        
        # Rate should be 2 calls per second (in 1 second window)
        assert self.limiter.current_rate == 2.0
    
    def test_rate_limiter_reset(self):
        """Test resetting rate limiter."""
        # Fill up the limit
        for i in range(3):
            self.limiter.try_acquire()
        
        assert self.limiter.try_acquire() is False
        
        self.limiter.reset()
        
        # Should allow calls again
        assert self.limiter.try_acquire() is True


class TestOperationCache:
    """Test OperationCache functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.cache = OperationCache(max_size=3, default_ttl=1.0)
    
    @pytest.mark.asyncio
    async def test_cache_miss_and_hit(self):
        """Test cache miss and subsequent hit."""
        call_count = [0]
        
        def expensive_operation():
            call_count[0] += 1
            return f"result_{call_count[0]}"
        
        # First call - cache miss
        result1 = await self.cache.get("key1", expensive_operation)
        assert result1 == "result_1"
        assert call_count[0] == 1
        
        # Second call - cache hit
        result2 = await self.cache.get("key1", expensive_operation)
        assert result2 == "result_1"  # Same result
        assert call_count[0] == 1  # Function not called again
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache expiration."""
        call_count = [0]
        
        def expensive_operation():
            call_count[0] += 1
            return f"result_{call_count[0]}"
        
        # Cache with very short TTL
        result1 = await self.cache.get("key1", expensive_operation, ttl=0.1)
        assert result1 == "result_1"
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Should call function again
        result2 = await self.cache.get("key1", expensive_operation, ttl=0.1)
        assert result2 == "result_2"
        assert call_count[0] == 2
    
    @pytest.mark.asyncio
    async def test_cache_size_limit(self):
        """Test cache size limit enforcement."""
        def make_factory(value):
            return lambda: f"result_{value}"
        
        # Fill cache to limit
        await self.cache.get("key1", make_factory(1))
        await self.cache.get("key2", make_factory(2))
        await self.cache.get("key3", make_factory(3))
        
        # Add one more - should evict oldest
        await self.cache.get("key4", make_factory(4))
        
        # key1 should be evicted (least recently used)
        call_count = [0]
        def check_eviction():
            call_count[0] += 1
            return "new_result"
        
        result = await self.cache.get("key1", check_eviction)
        assert result == "new_result"
        assert call_count[0] == 1  # Had to call function again
    
    @pytest.mark.asyncio
    async def test_async_factory_function(self):
        """Test cache with async factory function."""
        async def async_expensive_operation():
            await asyncio.sleep(0.001)
            return "async_result"
        
        result = await self.cache.get("async_key", async_expensive_operation)
        assert result == "async_result"
    
    def test_cache_invalidation(self):
        """Test manual cache invalidation."""
        # Note: Using async test would be better but keeping simple for now
        self.cache._cache["key1"] = ("value1", time.time() + 100)
        
        self.cache.invalidate("key1")
        
        assert "key1" not in self.cache._cache
    
    def test_cache_clear(self):
        """Test clearing entire cache."""
        # Add some items
        self.cache._cache["key1"] = ("value1", time.time() + 100)
        self.cache._cache["key2"] = ("value2", time.time() + 100)
        
        self.cache.clear()
        
        assert len(self.cache._cache) == 0
        assert len(self.cache._access_order) == 0
    
    def test_cleanup_expired_entries(self):
        """Test cleanup of expired entries."""
        now = time.time()
        
        # Add expired and non-expired entries
        self.cache._cache["expired1"] = ("value1", now - 1)  # Expired
        self.cache._cache["expired2"] = ("value2", now - 1)  # Expired
        self.cache._cache["valid"] = ("value3", now + 100)   # Valid
        
        cleaned_count = self.cache.cleanup_expired()
        
        assert cleaned_count == 2
        assert "expired1" not in self.cache._cache
        assert "expired2" not in self.cache._cache
        assert "valid" in self.cache._cache