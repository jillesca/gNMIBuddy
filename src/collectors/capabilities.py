#!/usr/bin/env python3
"""
Collector for device gNMI Capabilities.

Provides a function to retrieve and normalize device capabilities
using the CapabilityService and return a NetworkOperationResult
that the CLI can format consistently.
"""
from typing import Any, Dict, List

from src.schemas.models import Device
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
)
from src.gnmi.capabilities.repository import DeviceCapabilitiesRepository
from src.gnmi.capabilities.service import CapabilityService
from src.logging import get_logger

logger = get_logger(__name__)


def _serialize_models(models) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in models or []:
        out.append(
            {
                "name": getattr(m, "name", None),
                "version": getattr(m, "version", None),
                "organization": getattr(m, "organization", None),
            }
        )
    return out


def get_device_capabilities(device: Device) -> NetworkOperationResult:
    """
    Retrieve device gNMI capabilities.

    Args:
        device: Target device

    Returns:
        NetworkOperationResult with capabilities data or error
    """
    logger.debug("Fetching capabilities for device %s", device.name)

    try:
        repo = DeviceCapabilitiesRepository()
        service = CapabilityService(repo)
        caps = service.get_or_fetch(device)

        data: Dict[str, Any] = {
            "gnmi_version": caps.gnmi_version,
            "supported_encodings": list(caps.encodings or []),
            "supported_models": _serialize_models(caps.models),
        }

        logger.info(
            "Capabilities retrieved for %s: %d models, %d encodings",
            device.name,
            len(caps.models or []),
            len(caps.encodings or []),
        )

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=getattr(device.nos, "value", str(device.nos)),
            operation_type="capabilities",
            status=OperationStatus.SUCCESS,
            data=data,
        )

    except Exception as e:
        logger.error("Error fetching capabilities from %s: %s", device.name, e)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=getattr(device.nos, "value", str(device.nos)),
            operation_type="capabilities",
            status=OperationStatus.FAILED,
            error_response=ErrorResponse(
                type="CAPABILITIES_ERROR", message=str(e)
            ),
        )
