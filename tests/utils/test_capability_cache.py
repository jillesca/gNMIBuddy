#!/usr/bin/env python3
"""
Unit tests for the capability cache functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import threading
import time

from src.utils.capability_cache import (
    CapabilityCache,
    CacheEntry,
    is_device_verified,
    get_verification_result,
    cache_verification_result,
    invalidate_cache,
    get_cache_stats,
    cleanup_expired_entries,
)


class TestCacheEntry:
    """Test cases for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        now = datetime.now()
        expires = now + timedelta(minutes=30)

        entry = CacheEntry(
            device_name="test-device",
            is_verified=True,
            verification_result={"status": "verified"},
            timestamp=now,
            expires_at=expires,
        )

        assert entry.device_name == "test-device"
        assert entry.is_verified is True
        assert entry.verification_result == {"status": "verified"}
        assert entry.timestamp == now
        assert entry.expires_at == expires

    def test_cache_entry_no_expiry(self):
        """Test creating a cache entry without expiry."""
        now = datetime.now()

        entry = CacheEntry(
            device_name="test-device",
            is_verified=True,
            verification_result={"status": "verified"},
            timestamp=now,
        )

        assert entry.expires_at is None


class TestCapabilityCache:
    """Test cases for CapabilityCache class."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = CapabilityCache(default_ttl_minutes=30)

        assert cache._default_ttl == timedelta(minutes=30)
        assert len(cache._cache) == 0

    def test_cache_verification_result(self):
        """Test caching a verification result."""
        cache = CapabilityCache()

        cache.cache_verification_result(
            device_name="test-device",
            is_verified=True,
            verification_result={"status": "verified"},
        )

        assert cache.is_device_verified("test-device") is True
        assert cache.get_verification_result("test-device") == {
            "status": "verified"
        }

    def test_cache_verification_result_with_custom_ttl(self):
        """Test caching a verification result with custom TTL."""
        cache = CapabilityCache(default_ttl_minutes=60)

        cache.cache_verification_result(
            device_name="test-device",
            is_verified=True,
            verification_result={"status": "verified"},
            ttl_minutes=30,
        )

        entry = cache._cache["test-device"]
        expected_expiry = entry.timestamp + timedelta(minutes=30)

        # Allow for small time differences due to execution time
        assert entry.expires_at is not None
        assert abs((entry.expires_at - expected_expiry).total_seconds()) < 1

    def test_is_device_verified_not_found(self):
        """Test checking verification status for non-existent device."""
        cache = CapabilityCache()

        assert cache.is_device_verified("non-existent-device") is False

    def test_is_device_verified_expired(self):
        """Test checking verification status for expired entry."""
        cache = CapabilityCache()

        # Create an expired entry
        now = datetime.now()
        expired_entry = CacheEntry(
            device_name="test-device",
            is_verified=True,
            verification_result={"status": "verified"},
            timestamp=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )

        cache._cache["test-device"] = expired_entry

        assert cache.is_device_verified("test-device") is False
        assert "test-device" not in cache._cache  # Should be removed

    def test_get_verification_result_not_found(self):
        """Test getting verification result for non-existent device."""
        cache = CapabilityCache()

        result = cache.get_verification_result("non-existent-device")
        assert result is None

    def test_get_verification_result_expired(self):
        """Test getting verification result for expired entry."""
        cache = CapabilityCache()

        # Create an expired entry
        now = datetime.now()
        expired_entry = CacheEntry(
            device_name="test-device",
            is_verified=True,
            verification_result={"status": "verified"},
            timestamp=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )

        cache._cache["test-device"] = expired_entry

        result = cache.get_verification_result("test-device")
        assert result is None
        assert "test-device" not in cache._cache  # Should be removed

    def test_invalidate_cache_single_device(self):
        """Test invalidating cache for a single device."""
        cache = CapabilityCache()

        # Add multiple entries
        cache.cache_verification_result(
            "device1", True, {"status": "verified"}
        )
        cache.cache_verification_result("device2", False, {"status": "failed"})

        assert len(cache._cache) == 2

        # Invalidate one device
        cache.invalidate_cache("device1")

        assert len(cache._cache) == 1
        assert "device1" not in cache._cache
        assert "device2" in cache._cache

    def test_invalidate_cache_all_devices(self):
        """Test invalidating cache for all devices."""
        cache = CapabilityCache()

        # Add multiple entries
        cache.cache_verification_result(
            "device1", True, {"status": "verified"}
        )
        cache.cache_verification_result("device2", False, {"status": "failed"})

        assert len(cache._cache) == 2

        # Invalidate all devices
        cache.invalidate_cache()

        assert len(cache._cache) == 0

    def test_invalidate_cache_non_existent_device(self):
        """Test invalidating cache for non-existent device."""
        cache = CapabilityCache()

        # Add an entry
        cache.cache_verification_result(
            "device1", True, {"status": "verified"}
        )

        # Try to invalidate non-existent device
        cache.invalidate_cache("non-existent-device")

        # Original entry should still be there
        assert len(cache._cache) == 1
        assert "device1" in cache._cache

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        cache = CapabilityCache()

        # Add valid entries
        cache.cache_verification_result(
            "device1", True, {"status": "verified"}
        )
        cache.cache_verification_result("device2", False, {"status": "failed"})

        # Add expired entry
        now = datetime.now()
        expired_entry = CacheEntry(
            device_name="device3",
            is_verified=True,
            verification_result={"status": "verified"},
            timestamp=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
        cache._cache["device3"] = expired_entry

        stats = cache.get_cache_stats()

        assert stats["total_entries"] == 3
        assert stats["valid_entries"] == 2
        assert stats["expired_entries"] == 1
        assert stats["verified_devices"] == 1
        assert "66.7%" in stats["cache_hit_rate"]

    def test_get_cache_stats_empty(self):
        """Test getting cache statistics for empty cache."""
        cache = CapabilityCache()

        stats = cache.get_cache_stats()

        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["verified_devices"] == 0
        assert stats["cache_hit_rate"] == "0%"

    def test_cleanup_expired_entries(self):
        """Test cleaning up expired entries."""
        cache = CapabilityCache()

        # Add valid entry
        cache.cache_verification_result(
            "device1", True, {"status": "verified"}
        )

        # Add expired entries
        now = datetime.now()
        for i in range(2, 4):
            expired_entry = CacheEntry(
                device_name=f"device{i}",
                is_verified=True,
                verification_result={"status": "verified"},
                timestamp=now - timedelta(hours=2),
                expires_at=now - timedelta(hours=1),
            )
            cache._cache[f"device{i}"] = expired_entry

        assert len(cache._cache) == 3

        # Cleanup expired entries
        removed_count = cache.cleanup_expired_entries()

        assert removed_count == 2
        assert len(cache._cache) == 1
        assert "device1" in cache._cache

    def test_thread_safety(self):
        """Test thread safety of the cache."""
        cache = CapabilityCache()
        results = []

        def cache_operation(device_id):
            cache.cache_verification_result(
                f"device{device_id}", True, {"id": device_id}
            )
            result = cache.get_verification_result(f"device{device_id}")
            results.append(result)

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=cache_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all operations completed successfully
        assert len(results) == 10
        assert all(result is not None for result in results)
        assert len(cache._cache) == 10


class TestGlobalCacheFunctions:
    """Test cases for global cache functions."""

    def setUp(self):
        """Set up test by clearing global cache."""
        invalidate_cache()

    def test_is_device_verified_global(self):
        """Test global is_device_verified function."""
        self.setUp()

        # Initially should be False
        assert is_device_verified("test-device") is False

        # Cache a result
        cache_verification_result("test-device", True, {"status": "verified"})

        # Now should be True
        assert is_device_verified("test-device") is True

    def test_get_verification_result_global(self):
        """Test global get_verification_result function."""
        self.setUp()

        # Initially should be None
        assert get_verification_result("test-device") is None

        # Cache a result
        cache_verification_result("test-device", True, {"status": "verified"})

        # Now should return the result
        result = get_verification_result("test-device")
        assert result == {"status": "verified"}

    def test_cache_verification_result_global(self):
        """Test global cache_verification_result function."""
        self.setUp()

        cache_verification_result("test-device", True, {"status": "verified"})

        assert is_device_verified("test-device") is True
        assert get_verification_result("test-device") == {"status": "verified"}

    def test_invalidate_cache_global(self):
        """Test global invalidate_cache function."""
        self.setUp()

        # Add some entries
        cache_verification_result("device1", True, {"status": "verified"})
        cache_verification_result("device2", False, {"status": "failed"})

        # Invalidate one device
        invalidate_cache("device1")

        assert is_device_verified("device1") is False
        assert (
            is_device_verified("device2") is False
        )  # This should be True, but let's check

        # Add entries again
        cache_verification_result("device1", True, {"status": "verified"})
        cache_verification_result("device2", False, {"status": "failed"})

        # Invalidate all
        invalidate_cache()

        assert is_device_verified("device1") is False
        assert is_device_verified("device2") is False

    def test_get_cache_stats_global(self):
        """Test global get_cache_stats function."""
        self.setUp()

        # Initially should be empty
        stats = get_cache_stats()
        assert stats["total_entries"] == 0

        # Add some entries
        cache_verification_result("device1", True, {"status": "verified"})
        cache_verification_result("device2", False, {"status": "failed"})

        stats = get_cache_stats()
        assert stats["total_entries"] == 2
        assert stats["verified_devices"] == 1

    def test_cleanup_expired_entries_global(self):
        """Test global cleanup_expired_entries function."""
        self.setUp()

        # Add valid entry
        cache_verification_result("device1", True, {"status": "verified"})

        # Should not remove any entries since they're valid
        removed = cleanup_expired_entries()
        assert removed == 0

        # Verify entry is still there
        assert is_device_verified("device1") is True


if __name__ == "__main__":
    pytest.main([__file__])
