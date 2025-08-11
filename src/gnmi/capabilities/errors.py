#!/usr/bin/env python3
"""Error types for capability checks."""
from __future__ import annotations

from enum import Enum


class CapabilityError(Enum):
    MODEL_NOT_SUPPORTED = "MODEL_NOT_SUPPORTED"
    ENCODING_NOT_SUPPORTED = "ENCODING_NOT_SUPPORTED"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


__all__ = ["CapabilityError"]
