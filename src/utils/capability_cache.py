#!/usr/bin/env python3
"""
Capability cache for gNMIBuddy.

Provides in-memory caching for device capability verification results
to avoid repeated capability requests during the same session.
"""

import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from src.logging.config import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """
    Cache entry for capability verification results.

    Attributes:
        device_name: Name of the device
        is_verified: Whether the device capabilities were successfully verified
        verification_result: The detailed verification result
        timestamp: When the verification was performed
        expires_at: When the cache entry expires (optional)
    """

    device_name: str
    is_verified: bool
    verification_result: Any
    timestamp: datetime
    expires_at: Optional[datetime] = None


class CapabilityCache:
    """
    Thread-safe in-memory cache for device capability verification results.

    This cache stores verification results to avoid repeated capability requests
    during the same session. The cache is designed to be lightweight and
    session-scoped (no persistence across application restarts).
    """

    def __init__(self, default_ttl_minutes: int = 60):
        """
        Initialize the capability cache.

        Args:
            default_ttl_minutes: Default time-to-live for cache entries in minutes
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._default_ttl = timedelta(minutes=default_ttl_minutes)
        logger.debug(
            f"Initialized capability cache with TTL: {default_ttl_minutes} minutes"
        )

    def is_device_verified(self, device_name: str) -> bool:
        """
        Check if a device has been verified and the result is still valid.

        Args:
            device_name: Name of the device to check

        Returns:
            True if the device has been verified and cache is still valid, False otherwise
        """
        with self._lock:
            entry = self._cache.get(device_name)
            if entry is None:
                logger.debug(f"No cache entry found for device: {device_name}")
                return False

            # Check if entry has expired
            if entry.expires_at and datetime.now() > entry.expires_at:
                logger.debug(f"Cache entry expired for device: {device_name}")
                del self._cache[device_name]
                return False

            logger.debug(
                f"Cache hit for device: {device_name}, verified: {entry.is_verified}"
            )
            return entry.is_verified

    def get_verification_result(self, device_name: str) -> Optional[Any]:
        """
        Get the cached verification result for a device.

        Args:
            device_name: Name of the device

        Returns:
            The cached verification result if available and valid, None otherwise
        """
        with self._lock:
            entry = self._cache.get(device_name)
            if entry is None:
                return None

            # Check if entry has expired
            if entry.expires_at and datetime.now() > entry.expires_at:
                del self._cache[device_name]
                return None

            return entry.verification_result

    def cache_verification_result(
        self,
        device_name: str,
        is_verified: bool,
        verification_result: Any = None,
        ttl_minutes: Optional[int] = None,
    ) -> None:
        """
        Cache a verification result for a device.

        Args:
            device_name: Name of the device
            is_verified: Whether the device was successfully verified
            verification_result: The detailed verification result to cache
            ttl_minutes: Time-to-live for this entry in minutes (uses default if None)
        """
        with self._lock:
            now = datetime.now()
            ttl = (
                timedelta(minutes=ttl_minutes)
                if ttl_minutes
                else self._default_ttl
            )
            expires_at = now + ttl

            entry = CacheEntry(
                device_name=device_name,
                is_verified=is_verified,
                verification_result=verification_result,
                timestamp=now,
                expires_at=expires_at,
            )

            self._cache[device_name] = entry
            logger.debug(
                f"Cached verification result for device: {device_name}, "
                f"verified: {is_verified}, expires: {expires_at}"
            )

    def invalidate_cache(self, device_name: Optional[str] = None) -> None:
        """
        Invalidate cache entries.

        Args:
            device_name: Name of the device to invalidate. If None, invalidates all entries.
        """
        with self._lock:
            if device_name is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Invalidated all cache entries ({count} entries)")
            else:
                if device_name in self._cache:
                    del self._cache[device_name]
                    logger.debug(
                        f"Invalidated cache entry for device: {device_name}"
                    )
                else:
                    logger.debug(
                        f"No cache entry to invalidate for device: {device_name}"
                    )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring and debugging.

        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            now = datetime.now()
            valid_entries = 0
            expired_entries = 0
            verified_devices = 0

            for entry in self._cache.values():
                if entry.expires_at and now > entry.expires_at:
                    expired_entries += 1
                else:
                    valid_entries += 1
                    if entry.is_verified:
                        verified_devices += 1

            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_entries,
                "expired_entries": expired_entries,
                "verified_devices": verified_devices,
                "cache_hit_rate": (
                    f"{(valid_entries / len(self._cache) * 100):.1f}%"
                    if self._cache
                    else "0%"
                ),
            }

    def cleanup_expired_entries(self) -> int:
        """
        Remove expired entries from the cache.

        Returns:
            Number of expired entries removed
        """
        with self._lock:
            now = datetime.now()
            expired_keys = []

            for device_name, entry in self._cache.items():
                if entry.expires_at and now > entry.expires_at:
                    expired_keys.append(device_name)

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(
                    f"Cleaned up {len(expired_keys)} expired cache entries"
                )

            return len(expired_keys)


# Global cache instance
_global_cache = CapabilityCache()


def is_device_verified(device_name: str) -> bool:
    """
    Check if a device has been verified using the global cache.

    Args:
        device_name: Name of the device to check

    Returns:
        True if the device has been verified, False otherwise
    """
    return _global_cache.is_device_verified(device_name)


def get_verification_result(device_name: str) -> Optional[Any]:
    """
    Get the cached verification result for a device using the global cache.

    Args:
        device_name: Name of the device

    Returns:
        The cached verification result if available, None otherwise
    """
    return _global_cache.get_verification_result(device_name)


def cache_verification_result(
    device_name: str,
    is_verified: bool,
    verification_result: Any = None,
    ttl_minutes: Optional[int] = None,
) -> None:
    """
    Cache a verification result using the global cache.

    Args:
        device_name: Name of the device
        is_verified: Whether the device was successfully verified
        verification_result: The detailed verification result to cache
        ttl_minutes: Time-to-live for this entry in minutes
    """
    _global_cache.cache_verification_result(
        device_name, is_verified, verification_result, ttl_minutes
    )


def invalidate_cache(device_name: Optional[str] = None) -> None:
    """
    Invalidate cache entries using the global cache.

    Args:
        device_name: Name of the device to invalidate. If None, invalidates all entries.
    """
    _global_cache.invalidate_cache(device_name)


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics using the global cache.

    Returns:
        Dictionary containing cache statistics
    """
    return _global_cache.get_cache_stats()


def cleanup_expired_entries() -> int:
    """
    Remove expired entries from the global cache.

    Returns:
        Number of expired entries removed
    """
    return _global_cache.cleanup_expired_entries()
