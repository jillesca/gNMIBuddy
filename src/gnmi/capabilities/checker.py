#!/usr/bin/env python3
"""Capability checker orchestration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .errors import CapabilityError
from .models import DeviceCapabilities
from .service import CapabilityService
from .inspector import RequestInspector
from .encoding import EncodingPolicy


@dataclass
class CapabilityCheckResult:
    success: bool
    warnings: List[str] = field(default_factory=list)
    selected_encoding: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def is_failure(self) -> bool:
        return not self.success


class CapabilityChecker:
    def __init__(
        self,
        service: CapabilityService,
        version_cmp: Callable[[Optional[str], Optional[str]], Optional[int]],
        encoding_policy: EncodingPolicy,
    ) -> None:
        self.service = service
        self.version_cmp = version_cmp
        self.encoding_policy = encoding_policy
        self.inspector = RequestInspector()

    def check(
        self, device, paths: List[str], requested_encoding: Optional[str]
    ) -> CapabilityCheckResult:
        caps = self.service.get_or_fetch(device)

        # Encoding selection
        selected, used_fallback = self.encoding_policy.choose_supported(
            requested_encoding, caps.encodings
        )
        if selected is None:
            return CapabilityCheckResult(
                success=False,
                error_type=CapabilityError.ENCODING_NOT_SUPPORTED.value,
                error_message=(
                    f"Requested encoding '{requested_encoding}' is not supported by device"
                ),
            )

        warnings: List[str] = []

        # Infer requirements
        requirements = self.inspector.infer_requirements(paths)
        for req in requirements:
            present, older = caps.has_model(req, self.version_cmp)
            if not present:
                min_ver = (
                    f">={req.minimum_version}" if req.minimum_version else ""
                )
                return CapabilityCheckResult(
                    success=False,
                    error_type=CapabilityError.MODEL_NOT_SUPPORTED.value,
                    error_message=(
                        f"Required model '{req.name}{min_ver}' not supported by device"
                    ),
                )
            if older:
                # Try to include the device's actual version in the warning
                device_ver = None
                for m in caps.models:
                    if m.matches(req.name):
                        device_ver = m.version
                        break
                guidance = "; some collectors may not work correctly. Consider updating the device's OpenConfig model/version."
                if device_ver:
                    warnings.append(
                        f"Model '{req.name}' is older than required (device has {device_ver} < {req.minimum_version}){guidance}"
                    )
                else:
                    warnings.append(
                        f"Model '{req.name}' is older than required (device has < {req.minimum_version}){guidance}"
                    )

        return CapabilityCheckResult(
            success=True,
            warnings=warnings,
            selected_encoding=selected,
        )

    def check_with_caps(
        self,
        caps: DeviceCapabilities,
        paths: List[str],
        requested_encoding: Optional[str],
    ) -> CapabilityCheckResult:
        """Check capabilities using a provided, already-fetched DeviceCapabilities.

        This avoids any network calls and supports a workflow where capabilities
        are prefetched during inventory initialization.
        """
        # Encoding selection
        selected, used_fallback = self.encoding_policy.choose_supported(
            requested_encoding, caps.encodings
        )
        if selected is None:
            return CapabilityCheckResult(
                success=False,
                error_type=CapabilityError.ENCODING_NOT_SUPPORTED.value,
                error_message=(
                    f"Requested encoding '{requested_encoding}' is not supported by device"
                ),
            )

        warnings: List[str] = []

        # Infer requirements
        requirements = self.inspector.infer_requirements(paths)
        for req in requirements:
            present, older = caps.has_model(req, self.version_cmp)
            if not present:
                min_ver = (
                    f">={req.minimum_version}" if req.minimum_version else ""
                )
                return CapabilityCheckResult(
                    success=False,
                    error_type=CapabilityError.MODEL_NOT_SUPPORTED.value,
                    error_message=(
                        f"Required model '{req.name}{min_ver}' not supported by device"
                    ),
                )
            if older:
                # Try to include the device's actual version in the warning
                device_ver = None
                for m in caps.models:
                    if m.matches(req.name):
                        device_ver = m.version
                        break
                guidance = "; some collectors may not work correctly. Consider updating the device's OpenConfig model/version."
                if device_ver:
                    warnings.append(
                        f"Model '{req.name}' is older than required (device has {device_ver} < {req.minimum_version}){guidance}"
                    )
                else:
                    warnings.append(
                        f"Model '{req.name}' is older than required (device has < {req.minimum_version}){guidance}"
                    )

        return CapabilityCheckResult(
            success=True,
            warnings=warnings,
            selected_encoding=selected,
        )
