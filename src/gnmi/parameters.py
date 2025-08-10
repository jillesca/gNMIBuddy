#!/usr/bin/env python3
"""
Parameter objects for gNMI requests.
Provides structured objects for representing gNMI request parameters.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

# Thin import for type hints and inference helper
from src.gnmi.capabilities.inspector import RequestInspector
from src.gnmi.capabilities.encoding import GnmiEncoding
from src.gnmi.capabilities.models import ModelRequirement


@dataclass
class GnmiRequest:
    """
    Parameter object for gNMI request parameters.

    Encapsulates all parameters needed for a gNMI get request in a single object,
    following the "Introduce Parameter Object" refactoring pattern to improve code
    clarity and maintainability. Implements mapping interface to allow direct usage with **kwargs.

    Attributes:
        path: List of gNMI path strings to retrieve
        prefix: Prefix for the gNMI request (optional)
        encoding: Encoding type for the request (GnmiEncoding; defaults to JSON_IETF)
        datatype: Data type to retrieve (defaults to "all")
    """

    path: List[str]
    prefix: Optional[str] = None
    encoding: GnmiEncoding = GnmiEncoding.JSON_IETF
    datatype: str = "all"

    def _as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with smart None filtering."""
        return asdict(self)

    def keys(self):
        """Return keys for mapping interface (enables ** unpacking)."""
        return self._as_dict().keys()

    def __getitem__(self, key):
        """Return item for mapping interface (enables ** unpacking)."""
        return self._as_dict()[key]

    def infer_models(self) -> List[ModelRequirement]:
        """Infer required models from request paths using RequestInspector."""
        inspector = RequestInspector()
        return inspector.infer_requirements(self.path)
