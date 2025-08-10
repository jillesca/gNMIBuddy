#!/usr/bin/env python3
"""gNMI preflight helper: checks device capabilities and selects encoding.

Centralizes the orchestration of capability cache lookup/fetch and request
validation so the client remains small and focused.
"""
from __future__ import annotations


from src.schemas.models import Device
from src.gnmi.parameters import GnmiRequest
from src.gnmi.capabilities.repository import DeviceCapabilitiesRepository
from src.gnmi.capabilities.service import CapabilityService
from src.gnmi.capabilities.encoding import EncodingPolicy
from src.gnmi.capabilities.checker import (
    CapabilityChecker,
    CapabilityCheckResult,
)
from src.gnmi.capabilities.version import safe_compare
from src.gnmi.capabilities.errors import CapabilityError


def perform_preflight(
    device: Device, request: GnmiRequest
) -> CapabilityCheckResult:
    """Validate request against device capabilities using cached data.

    Fetches capabilities on-demand for the specific device if not already
    cached, then validates required models and encoding. Returns the detailed
    CapabilityCheckResult with selected_encoding and warnings.
    """
    repo = DeviceCapabilitiesRepository()
    caps = repo.get(device)
    if caps is None:
        caps = CapabilityService(repo).get_or_fetch(device)

    checker = CapabilityChecker(
        service=CapabilityService(repo),
        version_cmp=safe_compare,
        encoding_policy=EncodingPolicy(),
    )
    return checker.check_with_caps(
        caps, request.path, getattr(request, "encoding", None)
    )


def preflight_error_details(
    result: CapabilityCheckResult,
) -> tuple[str, str]:
    """Return a normalized (error_type, message) tuple for failed preflight.

    Keeps ErrorResponse creation in the client while centralizing defaulting
    and extraction logic here for readability.
    """
    err_type = result.error_type or CapabilityError.MODEL_NOT_SUPPORTED.value
    err_msg = result.error_message or "Preflight failed"
    return err_type, err_msg


def compute_effective_encoding(
    result: CapabilityCheckResult, request: GnmiRequest
) -> str:
    """Choose the encoding for this call without mutating the original request."""
    return (
        result.selected_encoding
        if result.selected_encoding
        else request.encoding
    )
