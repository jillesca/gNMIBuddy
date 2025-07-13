#!/usr/bin/env python3
"""
Response objects for network tools modules.
Provides structured objects for representing network information responses.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from src.gnmi.responses import (
    SuccessResponse,
    ErrorResponse,
    FeatureNotFoundResponse,
)


@dataclass
class NetworkToolsResponse:
    """
    Base class for network tools responses.

    This is a composition-based response that wraps the core response types.
    """

    device_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[ErrorResponse] = None
    feature_not_found: Optional[FeatureNotFoundResponse] = None

    @classmethod
    def from_network_response(
        cls,
        response: Union[
            SuccessResponse, ErrorResponse, FeatureNotFoundResponse
        ],
        device_name: Optional[str] = None,
    ) -> "NetworkToolsResponse":
        """Create a NetworkToolsResponse from a network response."""
        if isinstance(response, ErrorResponse):
            return cls(device_name=device_name, error=response)
        elif isinstance(response, FeatureNotFoundResponse):
            return cls(device_name=device_name, feature_not_found=response)
        else:  # SuccessResponse
            return cls(device_name=device_name, data=response.to_dict())

    def is_error(self) -> bool:
        """Check if this response represents an error."""
        return self.error is not None

    def is_feature_not_found(self) -> bool:
        """Check if this response represents a feature not found."""
        return self.feature_not_found is not None

    def is_success(self) -> bool:
        """Check if this response represents success."""
        return not self.is_error() and not self.is_feature_not_found()

    @classmethod
    def error_response(
        cls, error: ErrorResponse, device_name: Optional[str] = None
    ) -> "NetworkToolsResponse":
        """Create an error response."""
        return cls(device_name=device_name, error=error)

    @classmethod
    def success_response(
        cls, data: Dict[str, Any], device_name: Optional[str] = None
    ) -> "NetworkToolsResponse":
        """Create a success response."""
        return cls(device_name=device_name, data=data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        if self.error:
            result: Dict[str, Any] = {"error": self.error.to_dict()}
        elif self.feature_not_found:
            result = self.feature_not_found.to_dict()
        else:
            result = self.data or {}

        if self.device_name:
            result["device_name"] = self.device_name

        return result


@dataclass
class InterfaceResponse(NetworkToolsResponse):
    """
    Response object for interface information.

    Contains structured interface information optimized for consumption by other modules.

    Attributes:
        interfaces: List of interface data
        summary: Optional summary information for brief reporting
        is_single_interface: Whether this response is for a single interface
    """

    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    is_single_interface: bool = False

    @classmethod
    def single_interface(
        cls,
        interface: Optional[Dict[str, Any]],
        device_name: Optional[str] = None,
    ) -> "InterfaceResponse":
        """Create a response for a single interface."""
        return cls(
            device_name=device_name,
            interfaces=[interface] if interface else [],
            is_single_interface=True,
        )

    @classmethod
    def interface_brief(
        cls,
        interfaces: List[Dict[str, Any]],
        device_name: Optional[str] = None,
        summary: Optional[Dict[str, Any]] = None,
    ) -> "InterfaceResponse":
        """Create a response for interface brief information."""
        return cls(
            device_name=device_name,
            interfaces=(
                interfaces["interfaces"]
                if isinstance(interfaces, dict)
                else interfaces
            ),
            summary=summary,
            is_single_interface=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # Check for error or feature not found first
        if self.error:
            result: Dict[str, Any] = {"error": self.error.to_dict()}
        elif self.feature_not_found:
            result = self.feature_not_found.to_dict()
        else:
            result = {
                "interfaces": self.interfaces,
                "summary": self.summary or {},
                "is_single_interface": self.is_single_interface,
            }

        if self.device_name:
            result["device_name"] = self.device_name

        return result


@dataclass
class VpnResponse(NetworkToolsResponse):
    """
    Response object for VPN/VRF information.

    Contains structured VPN information optimized for consumption by other modules.

    Attributes:
        vrfs: List of VRF data
        summary: Optional summary information for brief reporting
        include_details: Whether detailed information is included
    """

    vrfs: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    include_details: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # Check for error or feature not found first
        if self.error:
            result: Dict[str, Any] = {"error": self.error.to_dict()}
        elif self.feature_not_found:
            result = self.feature_not_found.to_dict()
        else:
            result = {
                "vrfs": self.vrfs,
                "summary": self.summary or {},
                "include_details": self.include_details,
            }

        if self.device_name:
            result["device_name"] = self.device_name

        return result


@dataclass
class RoutingResponse(NetworkToolsResponse):
    """
    Response object for routing information.

    Contains structured routing information optimized for consumption by other modules.

    Attributes:
        protocols: List of routing protocol data
        summary: Optional summary information for brief reporting
        include_details: Whether detailed information is included
    """

    protocols: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    include_details: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # Check for error or feature not found first
        if self.error:
            result: Dict[str, Any] = {"error": self.error.to_dict()}
        elif self.feature_not_found:
            result = self.feature_not_found.to_dict()
        else:
            result = {
                "protocols": self.protocols,
                "summary": self.summary or {},
                "include_details": self.include_details,
            }

        if self.device_name:
            result["device_name"] = self.device_name

        return result


@dataclass
class MplsResponse(NetworkToolsResponse):
    """
    Response object for MPLS information.

    Contains structured MPLS information optimized for consumption by other modules.

    Attributes:
        mpls_data: MPLS configuration and operational data
        summary: Optional summary information for brief reporting
        include_details: Whether detailed information is included
    """

    mpls_data: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    include_details: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # Check for error or feature not found first
        if self.error:
            result: Dict[str, Any] = {"error": self.error.to_dict()}
        elif self.feature_not_found:
            result = self.feature_not_found.to_dict()
        else:
            result = {
                "mpls_data": self.mpls_data or {},
                "summary": self.summary or {},
                "include_details": self.include_details,
            }

        if self.device_name:
            result["device_name"] = self.device_name

        return result


@dataclass
class LogResponse(NetworkToolsResponse):
    """
    Response object for logging information.

    Contains structured log information optimized for consumption by other modules.

    Attributes:
        logs: List of log entries
        summary: Optional summary information for brief reporting
        filters_applied: Information about filters that were applied
    """

    logs: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    filters_applied: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # Check for error or feature not found first
        if self.error:
            result: Dict[str, Any] = {"error": self.error.to_dict()}
        elif self.feature_not_found:
            result = self.feature_not_found.to_dict()
        else:
            result = {
                "logs": self.logs,
                "summary": self.summary or {},
                "filters_applied": self.filters_applied or {},
            }

        if self.device_name:
            result["device_name"] = self.device_name

        return result


@dataclass
class SystemInfoResponse(NetworkToolsResponse):
    """
    Response object for system information.

    Contains structured system information optimized for consumption by other modules.

    Attributes:
        system_info: System configuration and operational data
        summary: Optional summary information for brief reporting
    """

    system_info: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # Check for error or feature not found first
        if self.error:
            result: Dict[str, Any] = {"error": self.error.to_dict()}
        elif self.feature_not_found:
            result = self.feature_not_found.to_dict()
        else:
            result = {
                "system_info": self.system_info or {},
                "summary": self.summary or {},
            }

        if self.device_name:
            result["device_name"] = self.device_name

        return result


@dataclass
class DeviceProfileResponse(NetworkToolsResponse):
    """
    Response object for device profile information.

    Contains structured device profile information optimized for consumption by other modules.

    Attributes:
        profile: Device profile data
        summary: Optional summary information for brief reporting
    """

    profile: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # Check for error or feature not found first
        if self.error:
            result: Dict[str, Any] = {"error": self.error.to_dict()}
        elif self.feature_not_found:
            result = self.feature_not_found.to_dict()
        else:
            result = {
                "profile": self.profile or {},
                "summary": self.summary or {},
            }

        if self.device_name:
            result["device_name"] = self.device_name

        return result
