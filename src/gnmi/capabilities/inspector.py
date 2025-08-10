#!/usr/bin/env python3
"""Infer model requirements from request paths."""
from __future__ import annotations

from typing import List

from .models import ModelRequirement


class RequestInspector:
    """Infers required OpenConfig models from paths."""

    MAPPING = {
        "openconfig-system": "0.17.1",
        "openconfig-interfaces": "4.0.0",
        "openconfig-network-instance": "1.3.0",
    }

    def infer_requirements(self, paths: List[str]) -> List[ModelRequirement]:
        seen = {}
        for p in paths or []:
            if ":" in p:
                module, _rest = p.split(":", 1)
            else:
                # Allow forms like "openconfig-system/system" (no colon)
                module = p.split("/")[0]
            module = module.strip()
            if module in self.MAPPING and module not in seen:
                seen[module] = ModelRequirement(
                    name=module, minimum_version=self.MAPPING[module]
                )
        return list(seen.values())
