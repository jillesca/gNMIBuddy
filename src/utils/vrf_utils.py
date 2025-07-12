"""
VRF utility functions for extracting non-default VRF names from gNMI responses.
"""

from typing import List
from src.gnmi.parameters import GnmiRequest
from src.gnmi.client import get_gnmi_data
from src.gnmi.responses import GnmiError
from src.network_tools.responses import VpnResponse
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
    if hasattr(response, "data") and response.data:
        for item in response.data:
            if "val" in item:
                if item["val"].lower() not in [
                    vrf.lower() for vrf in DEFAULT_INTERNAL_VRFS
                ]:
                    vrf_names.append(item["val"])
    return vrf_names
