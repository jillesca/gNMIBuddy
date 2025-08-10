#!/usr/bin/env python3
"""Version normalization and comparison utilities.

Provides a small NormalizedVersion class that can parse common version
formats and supports comparisons. Comparison precedence:
  semantic versions (highest fidelity) > date-like > raw lexicographic.
If parsing fails for both sides, comparisons return None.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import re


SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")
DATE_RE = re.compile(r"^(\d{4})[-/](\d{2})[-/](\d{2})$")


@dataclass(frozen=True)
class NormalizedVersion:
    """Normalized representation of a version string.

    Attributes:
        raw: original string
        kind: one of 'semver', 'date', or 'raw'
        parts_int: parsed tuple for semver/date, else None
        part_raw: raw string for 'raw' kind, else None
    """

    raw: str
    kind: str
    parts_int: Optional[Tuple[int, ...]]
    part_raw: Optional[str]

    def __lt__(self, other: "NormalizedVersion") -> bool:
        self._ensure_comparable(other)
        if self.kind in ("semver", "date"):
            assert self.parts_int is not None and other.parts_int is not None
            return self.parts_int < other.parts_int
        # raw
        assert self.part_raw is not None and other.part_raw is not None
        return self.part_raw < other.part_raw

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NormalizedVersion):
            return False
        if self.kind != other.kind:
            return False
        if self.kind in ("semver", "date"):
            return self.parts_int == other.parts_int
        return self.part_raw == other.part_raw

    def _ensure_comparable(self, other: "NormalizedVersion") -> None:
        if self.kind != other.kind:
            # Different kinds shouldn't be directly compared
            raise TypeError("Cannot compare versions of different kinds")

    @staticmethod
    def from_string(s: str) -> "NormalizedVersion":
        s = s.strip()
        m = SEMVER_RE.match(s)
        if m:
            major, minor, patch = map(int, m.groups())
            return NormalizedVersion(
                raw=s,
                kind="semver",
                parts_int=(major, minor, patch),
                part_raw=None,
            )
        m = DATE_RE.match(s)
        if m:
            year, month, day = map(int, m.groups())
            return NormalizedVersion(
                raw=s, kind="date", parts_int=(year, month, day), part_raw=None
            )
        # fallback to raw lexicographic
        return NormalizedVersion(raw=s, kind="raw", parts_int=None, part_raw=s)


def safe_compare(a: Optional[str], b: Optional[str]) -> Optional[int]:
    """Safely compare two version strings.

    Returns:
      -1 if a < b, 0 if a == b, 1 if a > b.
      None if either is None or if kinds differ making comparison ambiguous.

    Rules:
      - If both parse as semver, compare numerically
      - Else if both parse as dates, compare by date
      - Else if both fall back to raw, compare lexicographically
      - If kinds differ, return None
    """
    if a is None or b is None:
        return None

    va = NormalizedVersion.from_string(a)
    vb = NormalizedVersion.from_string(b)

    if va.kind != vb.kind:
        return None

    if va.kind in ("semver", "date"):
        assert va.parts_int is not None and vb.parts_int is not None
        if va.parts_int < vb.parts_int:
            return -1
        if va.parts_int > vb.parts_int:
            return 1
    else:
        assert va.part_raw is not None and vb.part_raw is not None
        if va.part_raw < vb.part_raw:
            return -1
        if va.part_raw > vb.part_raw:
            return 1
    return 0
