#!/usr/bin/env python3
"""
Device profile module.
Provides functions for retrieving device role/profile information from network devices using gNMI.
"""

from src.schemas.responses import (
    ErrorResponse,
    OperationStatus,
    NetworkOperationResult,
    FeatureNotFoundResponse,
)
from src.schemas.models import Device
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.utils.vrf_utils import get_non_default_vrf_names
from src.processors.deviceprofile_processor import DeviceProfileProcessor
from src.logging.config import get_logger, log_operation

logger = get_logger(__name__)


def deviceprofile_request():
    return GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp/global/afi-safis/afi-safi[name=*]/state",
            "openconfig-network-instance:network-instances/network-instance[name=*]/mpls/global/interface-attributes/interface[interface-id=*]/state",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/global/state",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp/neighbors/neighbor[neighbor-address=*]/route-reflector/state",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/global/segment-routing/state/enabled",
        ],
    )


def get_device_profile(device: Device) -> NetworkOperationResult:
    logger.debug("Getting device profile for device %s", device.name)

    response = get_gnmi_data(device, deviceprofile_request())
    logger.debug(
        "gNMI response type: %s, status: %s",
        type(response).__name__,
        getattr(response, "status", "N/A"),
    )

    if isinstance(response, ErrorResponse):
        logger.debug(
            "ErrorResponse details - type: %s, message: %s",
            response.type,
            response.message,
        )
        logger.error(
            "Error retrieving device profile from %s: %s",
            device.name,
            response.message,
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="device_profile",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    if isinstance(response, FeatureNotFoundResponse):
        logger.debug(
            "FeatureNotFoundResponse - feature: %s, message: %s",
            response.feature_name,
            response.message,
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="device_profile",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=response,
        )

    logger.debug("Getting VPN/BGP info for device profile analysis")
    # Get VPN info and BGP AFI-SAFI state for non-default VPNs
    vpn_info, vpn_bgp_afi_safi_states = _get_vpn_bgp_info(device)
    logger.debug(
        "VPN info - VRF count: %d, BGP states count: %d",
        len(vpn_info.get("vpn_names", [])),
        len(vpn_bgp_afi_safi_states),
    )

    parser = DeviceProfileProcessor()
    try:
        parsed_data = parser.process_data(
            response.data, vpn_info, vpn_bgp_afi_safi_states
        )

        device_role = parsed_data.get("role", "unknown")
        if device_role == "unknown":
            logger.warning(
                "Unable to determine clear role for device %s - insufficient protocol data",
                device.name,
            )
        else:
            logger.info(
                "Device %s identified as role: %s", device.name, device_role
            )
        logger.debug(
            "Device profile features: %s",
            str(list(parsed_data.keys())),
        )

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="device_profile",
            status=OperationStatus.SUCCESS,
            data={"profile": parsed_data},
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error parsing device profile: %s", str(e))
        logger.debug("Exception details: %s", str(e), exc_info=True)
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing device profile: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="device_profile",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )


def _get_vpn_bgp_info(device: Device):
    """
    Return (vpn_info, vpn_bgp_afi_safi_states) for non-default VPNs on the device.
    """
    logger.debug("Getting VPN BGP info for device %s", device.name)

    vpn_names = get_non_default_vrf_names(device)
    logger.debug("Found VPN names: %s", str(vpn_names))

    vpn_info = {"vpn_names": vpn_names or []}

    vpn_bgp_afi_safi_states = []
    if vpn_names:
        logger.debug(
            "Querying BGP AFI-SAFI states for %d VPNs", len(vpn_names)
        )
        for vpn in vpn_names:
            logger.debug("Querying VPN %s BGP AFI-SAFI state", vpn)
            path_query = f"openconfig-network-instance:network-instances/network-instance[name={vpn}]/protocols/protocol/bgp/global/afi-safis/afi-safi[afi-safi-name=*]/state"
            vpn_req = GnmiRequest(path=[path_query])
            vpn_resp = get_gnmi_data(device, vpn_req)

            if not isinstance(vpn_resp, ErrorResponse) and not isinstance(
                vpn_resp, FeatureNotFoundResponse
            ):
                if vpn_resp.data:
                    logger.debug(
                        "VPN %s: found %d BGP AFI-SAFI states",
                        vpn,
                        len(vpn_resp.data),
                    )
                    vpn_bgp_afi_safi_states.extend(vpn_resp.data)
                else:
                    logger.debug("VPN %s: no BGP AFI-SAFI data", vpn)
            else:
                if isinstance(vpn_resp, ErrorResponse):
                    logger.warning(
                        "Failed to get BGP data for VPN %s on %s: %s",
                        vpn,
                        device.name,
                        vpn_resp.message,
                    )
                logger.debug("VPN %s: error or feature not found", vpn)

    logger.debug(
        "Total VPN BGP AFI-SAFI states collected: %d",
        len(vpn_bgp_afi_safi_states),
    )
    return vpn_info, vpn_bgp_afi_safi_states
