#!/usr/bin/env python3
"""Shared constants for gNMI capabilities.

Defines the set of OpenConfig models that gNMI Buddy requires or cares about
across the codebase, with their minimum acceptable versions. Centralizing this
mapping avoids duplication and makes it easy to update requirements.
"""
from __future__ import annotations

from typing import Dict

# Map of OpenConfig module name -> minimum required version
# Keep values as strings to allow semantic/loose comparison elsewhere.
REQUIRED_OPENCONFIG_MODELS: Dict[str, str] = {
    "openconfig-system": "0.17.1",
    "openconfig-interfaces": "3.0.0",
    "openconfig-network-instance": "1.3.0",
}

__all__ = ["REQUIRED_OPENCONFIG_MODELS"]
