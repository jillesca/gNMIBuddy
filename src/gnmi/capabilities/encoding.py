#!/usr/bin/env python3
"""Encoding normalization and selection policy with Enum support."""
from __future__ import annotations

from enum import Enum
from typing import Optional, Tuple, Union, Sequence


class GnmiEncoding(Enum):
    JSON_IETF = "json_ietf"
    JSON = "json"
    ASCII = "ascii"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value

    @classmethod
    def from_any(
        cls, value: Optional[Union[str, "GnmiEncoding"]]
    ) -> Optional["GnmiEncoding"]:
        """Parse various inputs to a GnmiEncoding enum.

        - If enum is provided, return it.
        - If string is provided, case-normalize and map to enum.
        - Otherwise return None.
        """
        if value is None:
            return None
        if isinstance(value, GnmiEncoding):
            return value
        s = str(value).strip().lower()
        if s == "json_ietf":
            return GnmiEncoding.JSON_IETF
        if s == "json":
            return GnmiEncoding.JSON
        if s == "ascii":
            return GnmiEncoding.ASCII
        return None


class EncodingPolicy:
    """Normalize inputs to enums and choose supported fallbacks (as enums)."""

    def normalize(
        self, encoding: Optional[Union[str, GnmiEncoding]]
    ) -> Optional[GnmiEncoding]:
        return GnmiEncoding.from_any(encoding)

    def choose_supported(
        self,
        requested: Optional[Union[str, GnmiEncoding]],
        supported: Sequence[Union[str, GnmiEncoding]],
    ) -> Tuple[Optional[GnmiEncoding], bool]:
        """Return (selected_encoding_enum, used_fallback)."""
        sup: set[GnmiEncoding] = {
            e for e in (self.normalize(x) for x in supported) if e is not None
        }

        req = self.normalize(requested) if requested is not None else None
        if req is None:
            # No request -> prefer best available
            for candidate in (
                GnmiEncoding.JSON_IETF,
                GnmiEncoding.JSON,
                GnmiEncoding.ASCII,
            ):
                if candidate in sup:
                    return candidate, False
            return None, False

        if req in sup:
            return req, False

        # Conservative fallback policy: only allow fallback to ASCII
        fallbacks: dict[GnmiEncoding, tuple[GnmiEncoding, ...]] = {
            GnmiEncoding.JSON_IETF: (GnmiEncoding.ASCII,),
            GnmiEncoding.JSON: (GnmiEncoding.ASCII,),
            GnmiEncoding.ASCII: (),
        }
        for cand in fallbacks.get(req, ()):
            if cand in sup:
                return cand, True
        return None, False
