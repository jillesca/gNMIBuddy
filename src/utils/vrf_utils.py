"""
VRF utility functions for extracting non-default VRF names from gNMI responses.
"""

from typing import List
from src.gnmi.parameters import GnmiRequest
from src.gnmi.client import get_gnmi_data
from src.gnmi.responses import ErrorResponse, SuccessResponse
from src.inventory.models import Device

DEFAULT_INTERNAL_VRFS = ["default", "**iid"]


def get_non_default_vrf_names(device: Device) -> List[str]:
    """
    Get non-default VRF names from a network device.
    Returns a list of VRF names (strings) that are not in DEFAULT_INTERNAL_VRFS.
    """
    vrf_names_request = GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/state/name",
        ],
    )
    response = get_gnmi_data(device, vrf_names_request)
    vrf_names = []

    # Only process if we have a successful response (not an error)
    if not isinstance(response, ErrorResponse) and isinstance(
        response, SuccessResponse
    ):
        # Work directly with response data
        if response.data:
            response_data = response.data
        elif response.raw_data:
            response_data = response.raw_data.get("response", [])
        else:
            response_data = []

        if isinstance(response_data, list):
            for item in response_data:
                if isinstance(item, dict) and "val" in item:
                    val = item.get("val")
                    if (
                        val
                        and isinstance(val, str)
                        and val.lower()
                        not in [vrf.lower() for vrf in DEFAULT_INTERNAL_VRFS]
                    ):
                        vrf_names.append(val)
    return vrf_names
