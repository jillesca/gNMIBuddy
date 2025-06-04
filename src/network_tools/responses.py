#!/usr/bin/env python3
"""
Response objects for network tools modules.
Provides structured objects for representing network information responses.
"""


from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, cast
from src.gnmi.responses import (
    GnmiResponse,
    GnmiError,
    GnmiFeatureNotFoundResponse,
)


@dataclass
class NetworkToolsResponse(GnmiResponse):
    """
    Base class for network tools responses.

    This extends the GnmiResponse with features specific to network tools data.
    """

    device_name: Optional[str] = None

    @classmethod
    def from_gnmi_response(
        cls, response: GnmiResponse, device_name: Optional[str] = None
    ) -> "NetworkToolsResponse":
        """Create a NetworkToolsResponse from a GnmiResponse."""
        # Regular error handling - keep is_error() check for backward compatibility
        if response.is_error():
            return cls(
                success=False, error=response.error, device_name=device_name
            )

        # Special handling for GnmiFeatureNotFoundResponse
        if isinstance(response, GnmiFeatureNotFoundResponse):
            # Pass through the feature_not_found response directly without wrapping in error
            result = cls(success=True, device_name=device_name)
            result.raw_data = {
                "feature_not_found": response.to_dict()["feature_not_found"]
            }
            return result

        return cls(
            success=True, raw_data=response.raw_data, device_name=device_name
        )

    @classmethod
    def error_response(
        cls,
        error: Union[GnmiError, Dict[str, Any], GnmiFeatureNotFoundResponse],
        device_name: Optional[str] = None,
    ) -> "NetworkToolsResponse":
        """
        Create an error response with the given error details.

        This overrides the parent class method to include device_name.

        Args:
            error: Either a GnmiError object, a dictionary with error details,
                  or a GnmiFeatureNotFoundResponse
            device_name: Optional name of the device that generated the error

        Returns:
            A NetworkToolsResponse indicating an error condition or feature not found
        """
        # Handle feature not found responses
        if isinstance(error, GnmiFeatureNotFoundResponse):
            result = cls(success=True, device_name=device_name)
            result.raw_data = error.to_dict()
            return result

        # Convert dictionary to GnmiError if needed
        if isinstance(error, dict):
            # Check if this is a feature not found dict
            if "feature_not_found" in error:
                result = cls(success=True, device_name=device_name)
                result.raw_data = error
                return result
            error = GnmiError.from_dict(error)

        return cls(success=False, error=error, device_name=device_name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # If we have a feature_not_found response in raw_data, pass it through without wrapping in error
        if (
            self.raw_data
            and isinstance(self.raw_data, dict)
            and "feature_not_found" in self.raw_data
        ):
            return self.raw_data

        if self.is_error():
            return {"error": self.error.to_dict() if self.error else {}}

        result = {}
        if self.device_name:
            result["device_name"] = self.device_name
        # Include raw_data if present and not empty
        if self.raw_data:
            result.update(self.raw_data)
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
        cls, interface_data: Dict[str, Any], device_name: Optional[str] = None
    ) -> "InterfaceResponse":
        """Create a response for a single interface."""
        if "error" in interface_data:
            return cast(
                "InterfaceResponse",
                cls.error_response(interface_data["error"]),
            )

        # Extract interface data from the parsed result
        interface = interface_data.get("interface", {})

        return cls(
            success=True,
            device_name=device_name,
            interfaces=[interface] if interface else [],
            is_single_interface=True,
        )

    @classmethod
    def interface_brief(
        cls, interfaces_data: Dict[str, Any], device_name: Optional[str] = None
    ) -> "InterfaceResponse":
        """Create a response for a interface brief listing."""
        if "error" in interfaces_data:
            return cast(
                "InterfaceResponse",
                cls.error_response(interfaces_data["error"]),
            )

        interfaces = interfaces_data.get("interfaces", [])
        summary = interfaces_data.get("summary", {})

        return cls(
            success=True,
            device_name=device_name,
            interfaces=interfaces,
            summary=summary,
            is_single_interface=False,
        )

    def is_empty(self) -> bool:
        """Check if the response contains no interfaces."""
        return len(self.interfaces) == 0

    def interface_count(self) -> int:
        """Get the number of interfaces in the response."""
        return len(self.interfaces)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        if self.is_error():
            return {"error": self.error.to_dict() if self.error else {}}

        # For single interface, return the interface data directly
        if self.is_single_interface and self.interfaces:
            return {"interface": self.interfaces[0]}
        else:
            # For interface brief, include both interfaces list and summary
            result: Dict[str, Any] = {"interfaces": self.interfaces}
            if self.summary is not None:
                result["summary"] = self.summary
            return result

    @classmethod
    def error_response(
        cls,
        error: Union[GnmiError, Dict[str, Any], GnmiFeatureNotFoundResponse],
        device_name: Optional[str] = None,
    ) -> "InterfaceResponse":
        """
        Create an error response with the given error details for InterfaceResponse.
        """
        # Handle feature not found responses
        if isinstance(error, GnmiFeatureNotFoundResponse):
            result = cls(success=True, device_name=device_name)
            result.raw_data = error.to_dict()
            return result
        # Convert dictionary to GnmiError if needed
        if isinstance(error, dict):
            if "feature_not_found" in error:
                result = cls(success=True, device_name=device_name)
                result.raw_data = error
                return result
            error = GnmiError.from_dict(error)
        return cls(success=False, error=error, device_name=device_name)


@dataclass
class MplsResponse(NetworkToolsResponse):
    """
    Response object for MPLS information.

    Contains structured MPLS data including LSPs, LDP info, and segment routing.

    Attributes:
        mpls_data: Complete parsed MPLS data structure
        summary: Summary information
        include_details: Whether to include detailed data in output
    """

    mpls_data: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[Dict[str, Any]] = None
    include_details: bool = False

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        device_name: Optional[str] = None,
        include_details: bool = False,
    ) -> "MplsResponse":
        """Create an MplsResponse from a dictionary."""
        if "error" in data:
            return cast("MplsResponse", cls.error_response(data["error"]))

        return cls(
            success=True,
            device_name=device_name,
            mpls_data=data,
            summary=data.get("summary"),
            include_details=include_details,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # First check if we have feature_not_found in raw_data
        if (
            self.raw_data
            and isinstance(self.raw_data, dict)
            and "feature_not_found" in self.raw_data
        ):
            return self.raw_data

        if self.is_error():
            return {"error": self.error.to_dict() if self.error else {}}

        # Return different formats based on include_details flag
        if self.include_details:
            # Return the mpls_data which already includes the summary
            return {"data": self.mpls_data}
        else:
            return {"summary": self.summary}


@dataclass
class RoutingResponse(NetworkToolsResponse):
    """
    Response object for routing information.

    Contains structured routing data including routing tables and protocol information.

    Attributes:
        protocols: Information about routing protocols
        summary: Optional summary information
        include_details: Whether to include detailed data in output
    """

    routes: List[Dict[str, Any]] = field(default_factory=list)
    protocols: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[Dict[str, Any]] = None
    include_details: bool = False

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        device_name: Optional[str] = None,
        include_details: bool = False,
    ) -> "RoutingResponse":
        """Create a RoutingResponse from a dictionary."""
        if "error" in data:
            return cast("RoutingResponse", cls.error_response(data["error"]))

        return cls(
            success=True,
            device_name=device_name,
            routes=data.get("routes", []),
            protocols=data.get("protocols", {}),
            summary=data.get("summary"),
            include_details=include_details,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # First check if we have feature_not_found in raw_data
        if (
            self.raw_data
            and isinstance(self.raw_data, dict)
            and "feature_not_found" in self.raw_data
        ):
            return self.raw_data

        if self.is_error():
            return {"error": self.error.to_dict() if self.error else {}}

        if self.include_details:
            return {
                "data": {"routes": self.routes, "protocols": self.protocols},
                "summary": self.summary,
            }
        else:
            return {"summary": self.summary}


@dataclass
class VpnResponse(NetworkToolsResponse):
    """
    Response object for VPN information.

    Contains structured VPN data including VRFs, imported/exported routes, and route targets.

    Attributes:
        vrfs: List of VRF information
        summary: Summary information
        include_details: Whether to include detailed data in output
    """

    vrfs: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    include_details: bool = False

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        device_name: Optional[str] = None,
        include_details: bool = False,
    ) -> "VpnResponse":
        """Create a VpnResponse from a dictionary."""
        if "error" in data:
            return cast("VpnResponse", cls.error_response(data["error"]))

        return cls(
            success=True,
            device_name=device_name,
            vrfs=data.get("vrfs", []),
            summary=data.get("summary"),
            include_details=include_details,
        )

    def vrf_count(self) -> int:
        """Get the number of VRFs in the response."""
        return len(self.vrfs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # First check if we have feature_not_found in raw_data
        if (
            self.raw_data
            and isinstance(self.raw_data, dict)
            and "feature_not_found" in self.raw_data
        ):
            return self.raw_data

        if self.is_error():
            return {"error": self.error.to_dict() if self.error else {}}

        if self.include_details:
            return {"data": self.vrfs, "summary": self.summary}
        else:
            return {"summary": self.summary}


@dataclass
class LogResponse(NetworkToolsResponse):
    """
    Response object for logging information.

    Contains structured log data retrieved from network devices.

    Attributes:
        logs: List of log entries
        summary: Optional summary information
        filter_info: Information about the filters applied
    """

    logs: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    filter_info: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_logs(
        cls,
        logs_data: Dict[str, Any],
        device_name: Optional[str] = None,
        filter_info: Optional[Dict[str, Any]] = None,
    ) -> "LogResponse":
        """Create a LogResponse from filtered logs data."""
        if "error" in logs_data:
            return cast("LogResponse", cls.error_response(logs_data["error"]))

        logs = logs_data.get("logs", [])
        summary = logs_data.get("summary", {})

        return cls(
            success=True,
            device_name=device_name,
            logs=logs,
            summary=summary,
            filter_info=filter_info or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        # First check if we have feature_not_found in raw_data
        if (
            self.raw_data
            and isinstance(self.raw_data, dict)
            and "feature_not_found" in self.raw_data
        ):
            return self.raw_data

        if self.is_error():
            return {"error": self.error.to_dict() if self.error else {}}

        result: Dict[str, Any] = {"logs": self.logs}

        if self.summary:
            result["summary"] = self.summary

        if self.filter_info:
            result["filter_info"] = self.filter_info

        return result


@dataclass
class SystemInfoResponse(NetworkToolsResponse):
    """
    Response object for system information.

    Contains structured system information optimized for consumption by other modules.

    Attributes:
        system_info: Parsed system information as a dictionary
        summary: Optional summary information (for consistency)
    """

    system_info: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        device_name: Optional[str] = None,
    ) -> "SystemInfoResponse":
        if "error" in data:
            return cast(
                "SystemInfoResponse",
                cls.error_response(data["error"], device_name=device_name),
            )
        if "feature_not_found" in data:
            return cast(
                "SystemInfoResponse",
                cls.error_response(
                    {"feature_not_found": data["feature_not_found"]},
                    device_name=device_name,
                ),
            )
        return cls(success=True, device_name=device_name, system_info=data)

    def to_dict(self) -> Dict[str, Any]:
        if (
            self.raw_data
            and isinstance(self.raw_data, dict)
            and "feature_not_found" in self.raw_data
        ):
            return self.raw_data
        if self.is_error():
            return {"error": self.error.to_dict() if self.error else {}}
        # Return the parsed system info as the top-level dict
        return self.system_info if self.system_info is not None else {}
