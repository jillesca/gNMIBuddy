#!/usr/bin/env python3
"""Network command implementations"""

from .routing import network_routing
from .interface import network_interface
from .mpls import network_mpls
from .vpn import network_vpn

__all__ = [
    "network_routing",
    "network_interface",
    "network_mpls",
    "network_vpn",
]
