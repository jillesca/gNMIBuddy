#!/usr/bin/env python3
"""In-memory repository for caching device capabilities."""
from __future__ import annotations

from typing import Dict, Optional
from src.schemas.models import Device
from .models import DeviceCapabilities


class DeviceCapabilitiesRepository:
    """Simple in-memory cache keyed by a stable device key.

    Designed to behave like a process-wide shared cache so that different
    components see the same capabilities once loaded.
    """

    # Shared cache across all instances
    _cache: Dict[str, DeviceCapabilities] = {}

    def __init__(self) -> None:  # do not reset the shared cache
        pass

    @staticmethod
    def make_key(device: Device) -> str:
        nos = getattr(device, "nos", "unknown")
        ip = getattr(device, "ip_address", "")
        port = getattr(device, "port", 0)
        return f"{nos}:{ip}:{port}"

    def get(self, device: Device) -> Optional[DeviceCapabilities]:
        return self._cache.get(self.make_key(device))

    def set(self, device: Device, caps: DeviceCapabilities) -> None:
        self._cache[self.make_key(device)] = caps

    def has(self, device: Device) -> bool:
        return self.make_key(device) in self._cache

    def clear(self) -> None:
        self._cache.clear()
