#!/usr/bin/env python3
"""
Parameter objects for gNMI requests.
Provides structured objects for representing gNMI request parameters.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GnmiRequest:
    """
    Parameter object for gNMI request parameters.

    Encapsulates all parameters needed for a gNMI get request in a single object,
    following the "Introduce Parameter Object" refactoring pattern to improve code
    clarity and maintainability.

    Attributes:
        xpath: List of XPath strings to retrieve
        prefix: Prefix for the gNMI request (optional)
        encoding: Encoding type for the request (defaults to "json_ietf")
        datatype: Data type to retrieve (defaults to "all")
        extended_params: Additional parameters for future extensions
    """

    xpath: List[str]
    prefix: Optional[str] = None
    encoding: str = "json_ietf"
    datatype: str = "all"
    extended_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the request to a dictionary suitable for the gNMI client.
        """
        result = {
            "path": self.xpath,
            "prefix": self.prefix,
            "encoding": self.encoding,
            "datatype": self.datatype,
        }

        result.update(self.extended_params)

        return result
