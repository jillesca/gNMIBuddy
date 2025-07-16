#!/usr/bin/env python3
"""
Capability cache for gNMIBuddy.

Provides in-memory caching for device capability verification results
to avoid repeated capability requests during the same session.
"""

import threading
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from src.schemas.openconfig_models import OpenConfigModel
from src.schemas.verification_results import ModelVerificationResult
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


@dataclass
class ModelCacheEntry:
    """
    Cache entry for model-specific verification results.

    Attributes:
        device_name: Name of the device
        model: OpenConfig model that was verified
        verification_result: The detailed verification result for this model
        timestamp: When the verification was performed
        expires_at: When the cache entry expires (optional)
    """

    device_name: str
    model: OpenConfigModel
    verification_result: ModelVerificationResult
    timestamp: datetime
    expires_at: Optional[datetime] = None


class CapabilityCache:
    """
    Thread-safe in-memory cache for device capability verification results.

    This cache stores verification results to avoid repeated capability requests
    during the same session. The cache is designed to be lightweight and
    session-scoped (no persistence across application restarts).

    Supports both legacy device-level caching and new model-specific caching.
    """

    def __init__(self, default_ttl_minutes: int = 60):
        """
        Initialize the capability cache.

        Args:
            default_ttl_minutes: Default time-to-live for cache entries in minutes
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._model_cache: Dict[
            Tuple[str, OpenConfigModel], ModelCacheEntry
        ] = {}
        self._lock = threading.RLock()
        self._default_ttl = timedelta(minutes=default_ttl_minutes)
        logger.debug(
            f"Initialized capability cache with TTL: {default_ttl_minutes} minutes"
        )

    def get_model_verification_result(
        self, device_name: str, model: OpenConfigModel
    ) -> Optional[ModelVerificationResult]:
        """
        Get the cached verification result for a specific device-model combination.

        Args:
            device_name: Name of the device
            model: OpenConfig model to check

        Returns:
            ModelVerificationResult if available and valid, None otherwise
        """
        with self._lock:
            cache_key = (device_name, model)
            entry = self._model_cache.get(cache_key)

            if entry is None:
                logger.debug(
                    f"No cache entry found for device: {device_name}, model: {model.value}"
                )
                return None

            # Check if entry has expired
            if entry.expires_at and datetime.now() > entry.expires_at:
                logger.debug(
                    f"Cache entry expired for device: {device_name}, model: {model.value}"
                )
                del self._model_cache[cache_key]
                return None

            logger.debug(
                f"Cache hit for device: {device_name}, model: {model.value}, "
                f"status: {entry.verification_result.status.value}"
            )
            return entry.verification_result

    def cache_model_verification_result(
        self,
        device_name: str,
        model: OpenConfigModel,
        result: ModelVerificationResult,
        ttl_minutes: Optional[int] = None,
    ) -> None:
        """
        Cache a verification result for a specific device-model combination.

        Args:
            device_name: Name of the device
            model: OpenConfig model
            result: Verification result to cache
            ttl_minutes: Time-to-live in minutes (uses default if None)
        """
        with self._lock:
            cache_key = (device_name, model)
            timestamp = datetime.now()
            ttl = (
                timedelta(minutes=ttl_minutes)
                if ttl_minutes
                else self._default_ttl
            )
            expires_at = timestamp + ttl

            entry = ModelCacheEntry(
                device_name=device_name,
                model=model,
                verification_result=result,
                timestamp=timestamp,
                expires_at=expires_at,
            )

            self._model_cache[cache_key] = entry
            logger.debug(
                f"Cached verification result for device: {device_name}, "
                f"model: {model.value}, status: {result.status.value}, "
                f"expires: {expires_at}"
            )

    def invalidate_model_cache(
        self,
        device_name: Optional[str] = None,
        model: Optional[OpenConfigModel] = None,
    ) -> None:
        """
        Invalidate model-specific cache entries.

        Args:
            device_name: If provided, invalidate entries for this device only
            model: If provided, invalidate entries for this model only
        """
        with self._lock:
            if device_name is None and model is None:
                # Clear all model cache entries
                self._model_cache.clear()
                logger.info("Cleared all model cache entries")
                return

            keys_to_remove = []
            for cache_key in self._model_cache.keys():
                entry_device, entry_model = cache_key

                should_remove = True
                if device_name is not None and entry_device != device_name:
                    should_remove = False
                if model is not None and entry_model != model:
                    should_remove = False

                if should_remove:
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                del self._model_cache[key]
                logger.debug(
                    f"Invalidated cache entry for device: {key[0]}, model: {key[1].value}"
                )

    def get_model_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the model cache.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            stats = {
                "total_entries": len(self._model_cache),
                "entries_by_model": {},
                "entries_by_device": {},
                "expired_entries": 0,
            }

            now = datetime.now()
            for (device_name, model), entry in self._model_cache.items():
                # Count by model
                model_name = model.value
                if model_name not in stats["entries_by_model"]:
                    stats["entries_by_model"][model_name] = 0
                stats["entries_by_model"][model_name] += 1

                # Count by device
                if device_name not in stats["entries_by_device"]:
                    stats["entries_by_device"][device_name] = 0
                stats["entries_by_device"][device_name] += 1

                # Count expired entries
                if entry.expires_at and now > entry.expires_at:
                    stats["expired_entries"] += 1

            return stats

    # Legacy methods for backward compatibility
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
        verification_result: Any,
        ttl_minutes: Optional[int] = None,
    ) -> None:
        """
        Cache a verification result for a device.

        Args:
            device_name: Name of the device
            is_verified: Whether the device was successfully verified
            verification_result: The detailed verification result
            ttl_minutes: Time-to-live in minutes (uses default if None)
        """
        with self._lock:
            timestamp = datetime.now()
            ttl = (
                timedelta(minutes=ttl_minutes)
                if ttl_minutes
                else self._default_ttl
            )
            expires_at = timestamp + ttl

            entry = CacheEntry(
                device_name=device_name,
                is_verified=is_verified,
                verification_result=verification_result,
                timestamp=timestamp,
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
            device_name: If provided, invalidate only this device's cache entry.
                        If None, invalidate all cache entries.
        """
        with self._lock:
            if device_name is None:
                self._cache.clear()
                logger.info("Cleared all cache entries")
            else:
                if device_name in self._cache:
                    del self._cache[device_name]
                    logger.debug(
                        f"Invalidated cache entry for device: {device_name}"
                    )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.

        Returns:
            Dictionary with cache statistics including entry count,
            device list, and expired entries
        """
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = 0
            verified_devices = 0
            total_verified = 0

            now = datetime.now()
            for entry in self._cache.values():
                if entry.is_verified:
                    total_verified += 1

                if entry.expires_at and now > entry.expires_at:
                    expired_entries += 1
                elif entry.is_verified:
                    verified_devices += 1

            valid_entries = total_entries - expired_entries
            cache_hit_rate = "0%"
            if total_entries > 0:
                hit_rate = (total_verified / total_entries) * 100
                cache_hit_rate = f"{hit_rate:.1f}%"

            stats = {
                "total_entries": total_entries,
                "devices": list(self._cache.keys()),
                "expired_entries": expired_entries,
                "valid_entries": valid_entries,
                "verified_devices": verified_devices,
                "cache_hit_rate": cache_hit_rate,
            }

            return stats

    def cleanup_expired_entries(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            The number of expired entries that were removed from the cache
        """
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry.expires_at and now > entry.expires_at
            ]
            for key in expired_keys:
                del self._cache[key]
                logger.debug("Removed expired cache entry for device: %s", key)

            return len(expired_keys)


# Global cache instance
_cache_instance = CapabilityCache()


# Module-level functions for backward compatibility
def is_device_verified(device_name: str) -> bool:
    """Check if a device has been verified (legacy function)."""
    return _cache_instance.is_device_verified(device_name)


def get_verification_result(device_name: str) -> Optional[Any]:
    """Get the cached verification result for a device (legacy function)."""
    return _cache_instance.get_verification_result(device_name)


def cache_verification_result(
    device_name: str,
    is_verified: bool,
    verification_result: Any,
    ttl_minutes: Optional[int] = None,
) -> None:
    """Cache a verification result for a device (legacy function)."""
    _cache_instance.cache_verification_result(
        device_name, is_verified, verification_result, ttl_minutes
    )


def invalidate_cache(device_name: Optional[str] = None) -> None:
    """Invalidate cache entries (legacy function)."""
    _cache_instance.invalidate_cache(device_name)


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about the cache (legacy function)."""
    return _cache_instance.get_cache_stats()


# New module-level functions for model-specific caching
def get_model_verification_result(
    device_name: str, model: OpenConfigModel
) -> Optional[ModelVerificationResult]:
    """Get the cached verification result for a specific device-model combination."""
    return _cache_instance.get_model_verification_result(device_name, model)


def cache_model_verification_result(
    device_name: str,
    model: OpenConfigModel,
    result: ModelVerificationResult,
    ttl_minutes: Optional[int] = None,
) -> None:
    """Cache a verification result for a specific device-model combination."""
    _cache_instance.cache_model_verification_result(
        device_name, model, result, ttl_minutes
    )


def invalidate_model_cache(
    device_name: Optional[str] = None, model: Optional[OpenConfigModel] = None
) -> None:
    """Invalidate model-specific cache entries."""
    _cache_instance.invalidate_model_cache(device_name, model)


def get_model_cache_stats() -> Dict[str, Any]:
    """Get statistics about the model cache."""
    return _cache_instance.get_model_cache_stats()


def cleanup_expired_entries() -> int:
    """Clean up expired cache entries (legacy function)."""
    return _cache_instance.cleanup_expired_entries()
