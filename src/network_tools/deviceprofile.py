#!/usr/bin/env python3
"""
Device profile module.
Provides functions for retrieving device role/profile information from network devices using gNMI.
"""

import logging
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import (
    ErrorResponse,
    FeatureNotFoundResponse,
)
from src.inventory.models import Device
from src.parsers.deviceprofile_parser import DeviceProfileParser
from src.network_tools.responses import DeviceProfileResponse
from src.utils.vrf_utils import get_non_default_vrf_names

logger = logging.getLogger(__name__)


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


def get_device_profile(device: Device):
    response = get_gnmi_data(device, deviceprofile_request())

    if isinstance(response, ErrorResponse):
        return DeviceProfileResponse(device_name=device.name, error=response)

    if isinstance(response, FeatureNotFoundResponse):
        return DeviceProfileResponse(
            device_name=device.name, feature_not_found=response
        )

    response_dict = response.to_dict()

    # Get VPN info and BGP AFI-SAFI state for non-default VPNs
    vpn_info, vpn_bgp_afi_safi_states = _get_vpn_bgp_info(device)
    response_dict["vpn_info"] = vpn_info
    response_dict["vpn_bgp_afi_safi_states"] = vpn_bgp_afi_safi_states

    parser = DeviceProfileParser()
    try:
        parsed_data = parser.parse(response_dict)
        return DeviceProfileResponse(
            device_name=device.name,
            profile=parsed_data,
        )
    except Exception as e:
        logger.error("Error parsing device profile: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing device profile: {str(e)}",
        )
        return DeviceProfileResponse(
            device_name=device.name, error=error_response
        )


def _get_vpn_bgp_info(device: Device):
    """
    Return (vpn_info, vpn_bgp_afi_safi_states) for non-default VPNs on the device.
    """
    vpn_names = get_non_default_vrf_names(device)
    vpn_info = {"vpn_names": vpn_names or []}

    vpn_bgp_afi_safi_states = []
    if vpn_names:
        for vpn in vpn_names:
            path_query = f"openconfig-network-instance:network-instances/network-instance[name={vpn}]/protocols/protocol/bgp/global/afi-safis/afi-safi[afi-safi-name=*]/state"
            vpn_req = GnmiRequest(path=[path_query])
            vpn_resp = get_gnmi_data(device, vpn_req)
            if not isinstance(vpn_resp, ErrorResponse) and not isinstance(
                vpn_resp, FeatureNotFoundResponse
            ):
                vpn_data = vpn_resp.to_dict()
                if vpn_data:
                    vpn_bgp_afi_safi_states.extend(vpn_data)
    return vpn_info, vpn_bgp_afi_safi_states
