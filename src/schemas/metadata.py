#!/usr/bin/env python3
"""
Metadata schemas for network operations.

Contains structured metadata objects used to encapsulate additional
information about operation results.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class VpnInfoMetadata:
    """
    Metadata for VPN/VRF information operations.

    Encapsulates contextual information about VRF discovery and processing.
    """

    message: str
    total_vrfs_on_device: Optional[int] = None
    vrfs_returned: Optional[int] = None
    vrf_filter_applied: Optional[bool] = None
    vrf_filter: Optional[str] = None
    include_details: Optional[bool] = None
    excluded_internal_vrfs: Optional[List[str]] = None


@dataclass
class TopologyNeighborsMetadata:
    """
    Metadata for topology neighbors operations.

    Encapsulates contextual information about device topology and neighbor discovery.
    """

    message: str
    device_in_topology: bool
    neighbor_count: Optional[int] = None
    isolation_reason: Optional[str] = None
