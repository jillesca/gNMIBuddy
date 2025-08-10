#!/usr/bin/env python3
"""
Collector for device gNMI Capabilities.

Provides a function to retrieve and normalize device capabilities
using the CapabilityService and return a NetworkOperationResult
that the CLI can format consistently.
"""
from typing import Any, Dict, List, Optional

from src.schemas.models import Device
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
)
from src.gnmi.capabilities.repository import DeviceCapabilitiesRepository
from src.gnmi.capabilities.service import CapabilityService
from src.gnmi.capabilities.inspector import RequestInspector
from src.gnmi.capabilities.version import safe_compare
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


def get_device_capabilities(
    device: Device, show_all_models: bool = False
) -> NetworkOperationResult:
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

        if show_all_models:
            # Full raw-ish output
            data: Dict[str, Any] = {
                "gnmi_version": caps.gnmi_version,
                "supported_encodings": list(caps.encodings or []),
                "supported_models": _serialize_models(caps.models),
            }
        else:
            # Focused view: only models the tool cares about + status
            inspector = RequestInspector()
            # Build requirements from known mapping without needing user paths
            required = [
                # Use MAPPING items to build ModelRequirement list
                # Ensures CLI validation matches preflight logic
                *(
                    inspector.infer_requirements([f"{name}:/"])
                    for name in inspector.MAPPING.keys()
                )
            ]
            # Flatten the list of lists
            flat_required = [r for sub in required for r in sub]

            # Determine device status for each required model
            focused: List[Dict[str, Optional[str]]] = []
            for req in flat_required:
                # Find device's model version for this requirement
                device_ver: Optional[str] = None
                for m in caps.models:
                    if m.name == req.name:
                        device_ver = m.version
                        break

                status: str
                if device_ver is None:
                    status = "not_supported"
                else:
                    cmp = safe_compare(device_ver, req.minimum_version)
                    if cmp is None or req.minimum_version is None:
                        status = "unknown"
                    elif cmp < 0:
                        status = "older"
                    else:
                        status = "ok"

                # Build a clear, user-facing message for each status
                if status == "ok":
                    msg = (
                        "Model present and meets the required minimum version"
                    )
                elif status == "older":
                    msg = (
                        f"Model present but older than required (device has {device_ver or 'unknown'} < {req.minimum_version}); "
                        "some collectors may not work correctly. Consider updating the device's OpenConfig model/version."
                    )
                elif status == "not_supported":
                    msg = "Model not supported on device"
                else:
                    msg = "Model version comparison unknown"

                focused.append(
                    {
                        "name": req.name,
                        "required_min_version": req.minimum_version,
                        "device_version": device_ver,
                        "status": status,
                        "message": msg,
                    }
                )

            data = {
                "gnmi_version": caps.gnmi_version,
                "encodings": list(caps.encodings or []),
                "required_models": focused,
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
