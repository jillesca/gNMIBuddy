#!/usr/bin/env python3
"""Domain models for gNMI device capabilities.

Pure data objects (no external side-effects) to represent OpenConfig models,
requirements, and device capability sets. Avoid using dicts to encapsulate
behavior—use classes with clear methods and representations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple
from .encoding import GnmiEncoding


@dataclass(frozen=True)
class ModelIdentifier:
    """Represents a supported YANG model on the device."""

    name: str
    version: Optional[str] = None
    organization: Optional[str] = None

    def normalized_version(self) -> Optional[str]:
        """Return a normalized string form of version if present.

        Normalization is delegated to a higher-level component; this method just
        returns the raw version string (kept for interface clarity/extension).
        """
        return self.version

    def matches(self, name: str) -> bool:
        """Check if this model identifier matches by name (case-sensitive)."""
        return self.name == name

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ModelIdentifier(name={self.name!r}, version={self.version!r}, "
            f"organization={self.organization!r})"
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        ver = f"@{self.version}" if self.version else ""
        return f"{self.name}{ver}"


@dataclass(frozen=True)
class ModelRequirement:
    """Represents a requirement for a YANG model with an optional min version."""

    name: str
    minimum_version: Optional[str] = None

    def requires_version(self) -> bool:
        return bool(self.minimum_version)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"ModelRequirement(name={self.name!r}, minimum_version={self.minimum_version!r})"

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.minimum_version:
            return f"{self.name}>={self.minimum_version}"
        return self.name


@dataclass
class DeviceCapabilities:
    """Device capability set returned by Capabilities RPC.

    Attributes:
        models: list of ModelIdentifier supported by the device
        encodings: list of supported encodings (already normalized if needed)
        gnmi_version: optional gNMI version string
    """

    models: List[ModelIdentifier]
    encodings: List[GnmiEncoding]
    gnmi_version: Optional[str] = None

    def has_model(
        self,
        req: ModelRequirement,
        version_cmp: Callable[[Optional[str], Optional[str]], Optional[int]],
    ) -> Tuple[bool, bool]:
        """Check if a required model is present and if it's older than minimum.

        Returns a tuple (present, older_than_min):
          - present: True if a model with the required name exists on device
          - older_than_min: True if present but version < minimum_version

        version_cmp should return -1, 0, 1 for a<b, a==b, a>b respectively,
        or None if comparison is not possible.
        """
        present = False
        older_than_min = False

        for model in self.models:
            if not model.matches(req.name):
                continue
            present = True

            if req.requires_version():
                cmp = version_cmp(model.version, req.minimum_version)
                if cmp is None:
                    # Unknown comparison; treat as not older to avoid false failures
                    older_than_min = False
                else:
                    older_than_min = cmp < 0
            break

        return present, older_than_min

    def supports_encoding(self, encoding: Optional[GnmiEncoding]) -> bool:
        """Return True if the requested enum encoding is supported by device."""
        if encoding is None:
            return True
        return encoding in set(self.encodings)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"DeviceCapabilities(models={self.models!r}, encodings={self.encodings!r}, "
            f"gnmi_version={self.gnmi_version!r})"
        )

    def __str__(self) -> str:  # pragma: no cover - trivial
        models_str = ", ".join(str(m) for m in self.models)
        encs = ", ".join(str(e) for e in self.encodings)
        return f"models=[{models_str}] encodings=[{encs}] gnmi={self.gnmi_version or '-'}"
