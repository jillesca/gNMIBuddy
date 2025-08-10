#!/usr/bin/env python3
"""Capability service using gNMI Capabilities RPC with caching."""
from __future__ import annotations

from typing import List, Dict, Any

from pygnmi.client import gNMIclient

from src.schemas.models import Device
from .models import DeviceCapabilities, ModelIdentifier
from .repository import DeviceCapabilitiesRepository


class CapabilityService:
    def __init__(self, repo: DeviceCapabilitiesRepository) -> None:
        self.repo = repo

    def get_or_fetch(self, device: Device) -> DeviceCapabilities:
        cached = self.repo.get(device)
        if cached:
            return cached
        caps = self._fetch(device)
        self.repo.set(device, caps)
        return caps

    def _fetch(self, device: Device) -> DeviceCapabilities:
        # Build connection params locally to avoid circular import with gnmi.client
        params = {
            "target": (device.ip_address, device.port),
            "username": device.username,
            "password": device.password,
            "insecure": device.insecure,
            "path_cert": device.path_cert,
            "path_key": device.path_key,
            "path_root": device.path_root,
            "override": device.override,
            "skip_verify": device.skip_verify,
            "gnmi_timeout": device.gnmi_timeout,
            "grpc_options": device.grpc_options,
            "show_diff": device.show_diff,
        }
        models: List[ModelIdentifier] = []
        encodings: List[str] = []
        gnmi_version: str | None = None

        def normalize_encoding(e: str | None) -> str | None:
            if e is None:
                return None
            m = {
                "JSON_IETF": "json_ietf",
                "JSON": "json",
                "ASCII": "ascii",
            }
            return m.get(e, m.get(e.upper(), e.lower()))

        with gNMIclient(**params) as client:  # type: ignore[arg-type]
            resp: Dict[str, Any] = client.capabilities() or {}
            # Expected keys in pygnmi response
            for m in resp.get("supported_models", []) or []:
                models.append(
                    ModelIdentifier(
                        name=m.get("name", ""),
                        version=m.get("version"),
                        organization=m.get("organization"),
                    )
                )
            for e in resp.get("supported_encodings", []) or []:
                ne = normalize_encoding(e)
                if ne:
                    encodings.append(ne)
            gnmi_version = resp.get("gNMI_version")

        return DeviceCapabilities(
            models=models, encodings=encodings, gnmi_version=gnmi_version
        )
