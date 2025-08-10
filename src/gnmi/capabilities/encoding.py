#!/usr/bin/env python3
"""Encoding normalization and selection policy."""
from __future__ import annotations

from typing import List, Optional, Tuple


class EncodingPolicy:
    """Canonicalize encodings and choose supported fallbacks."""

    CANONICAL = {
        "JSON_IETF": "json_ietf",
        "JSON": "json",
        "ASCII": "ascii",
        # lower-case variants
        "json_ietf": "json_ietf",
        "json": "json",
        "ascii": "ascii",
    }

    def normalize(self, encoding: Optional[str]) -> Optional[str]:
        if encoding is None:
            return None
        return self.CANONICAL.get(
            encoding, self.CANONICAL.get(encoding.upper())
        )

    def choose_supported(
        self, requested: Optional[str], supported: List[str]
    ) -> Tuple[Optional[str], bool]:
        """Return (selected_encoding, used_fallback)."""
        norm_supported = {self.normalize(e) for e in supported}

        req = self.normalize(requested) if requested else None
        if req is None:
            # No request -> prefer best available
            for candidate in ("json_ietf", "json", "ascii"):
                if candidate in norm_supported:
                    return candidate, False
            return None, False

        if req in norm_supported:
            return req, False

        # fallback order: be conservative and only allow fallback to ASCII
        # This matches expected behavior in tests where json_ietf -> json is NOT allowed
        fallbacks = {
            "json_ietf": ["ascii"],
            "json": ["ascii"],
            "ascii": [],
        }
        for candidate in fallbacks.get(req, []):
            if candidate in norm_supported:
                return candidate, True
        return None, False
