#!/usr/bin/env python3
"""
Parameter objects for gNMI requests.
Provides structured objects for representing gNMI request parameters.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas.openconfig_models import OpenConfigModel

from ..logging.config import get_logger

logger = get_logger(__name__)


@dataclass
class VerificationOptions:
    """
    Options for capability verification behavior.

    Attributes:
        strict_mode: Whether to fail on any model verification failure
        cache_results: Whether to cache verification results
        ttl_minutes: Time-to-live for cached results in minutes
        required_models: Override auto-detection with specific models
    """

    strict_mode: bool = True
    cache_results: bool = True
    ttl_minutes: Optional[int] = None
    required_models: Optional[Set["OpenConfigModel"]] = None


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
        encoding: Encoding type for the request (defaults to "json_ietf")
        datatype: Data type to retrieve (defaults to "all")
        verification_options: Options for capability verification behavior
    """

    path: List[str]
    prefix: Optional[str] = None
    encoding: str = "json_ietf"
    datatype: str = "all"
    verification_options: Optional[VerificationOptions] = None

    def __post_init__(self):
        """Initialize default verification options if not provided."""
        if self.verification_options is None:
            self.verification_options = VerificationOptions()
            logger.debug(
                "Default verification options initialized",
                extra={
                    "strict_mode": self.verification_options.strict_mode,
                    "cache_results": self.verification_options.cache_results,
                },
            )

        logger.debug(
            "GnmiRequest initialized",
            extra={
                "path_count": len(self.path),
                "paths": self.path,
                "encoding": self.encoding,
                "datatype": self.datatype,
                "has_prefix": self.prefix is not None,
            },
        )

    def _as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with smart None filtering."""
        result = asdict(self)
        # Remove verification_options from dict for gNMI compatibility
        if "verification_options" in result:
            del result["verification_options"]
        return result

    def keys(self):
        """Return keys for mapping interface (enables ** unpacking)."""
        return self._as_dict().keys()

    def __getitem__(self, key):
        """Return item for mapping interface (enables ** unpacking)."""
        return self._as_dict()[key]

    def get_required_models(self) -> Set["OpenConfigModel"]:
        """
        Determine which OpenConfig models are required for this request.

        Analyzes the paths in this request to determine which OpenConfig models
        are needed to fulfill the request. This is used by the capability
        verification system to ensure devices support required models.

        Returns:
            Set of OpenConfigModel enums required for this request
        """
        # Check if models are explicitly overridden
        if (
            self.verification_options
            and self.verification_options.required_models is not None
        ):
            logger.debug(
                "Using explicitly provided required models",
                extra={
                    "model_count": len(
                        self.verification_options.required_models
                    ),
                    "models": [
                        m.value
                        for m in self.verification_options.required_models
                    ],
                },
            )
            return self.verification_options.required_models

        # Import here to avoid circular imports
        from ..utils.path_analyzer import extract_models_from_paths

        logger.debug(
            "Analyzing paths to determine required models",
            extra={
                "path_count": len(self.path),
                "paths": self.path,
            },
        )

        models = extract_models_from_paths(self.path)

        logger.debug(
            "Required models determined from path analysis",
            extra={
                "model_count": len(models),
                "models": [m.value for m in models],
            },
        )

        return models

    def requires_model(self, model: "OpenConfigModel") -> bool:
        """
        Check if this request requires a specific OpenConfig model.

        Args:
            model: OpenConfig model to check for

        Returns:
            True if the request requires the specified model, False otherwise
        """
        required_models = self.get_required_models()
        result = model in required_models

        logger.debug(
            "Checking if request requires specific model",
            extra={
                "model": model.value,
                "required": result,
                "total_required_models": len(required_models),
            },
        )

        return result

    def get_model_names(self) -> Set[str]:
        """
        Get the names of all OpenConfig models required by this request.

        Returns:
            Set of model name strings (e.g., {"openconfig-system", "openconfig-interfaces"})
        """
        models = self.get_required_models()
        model_names = {model.value for model in models}

        logger.debug(
            "Retrieved model names for request",
            extra={
                "model_count": len(model_names),
                "model_names": list(model_names),
            },
        )

        return model_names

    def get_verification_cache_key(self, device_name: str) -> str:
        """
        Generate a cache key for verification results.

        Args:
            device_name: Name of the device

        Returns:
            Cache key string for this request's verification results
        """
        models = sorted([model.value for model in self.get_required_models()])
        cache_key = f"{device_name}:{':'.join(models)}"

        logger.debug(
            "Generated verification cache key",
            extra={
                "device_name": device_name,
                "cache_key": cache_key,
                "model_count": len(models),
            },
        )

        return cache_key

    def with_verification_options(self, **kwargs) -> "GnmiRequest":
        """
        Create a new GnmiRequest with updated verification options.

        Args:
            **kwargs: Verification option updates

        Returns:
            New GnmiRequest with updated verification options

        Example:
            new_request = request.with_verification_options(
                strict_mode=False,
                cache_results=True
            )
        """
        logger.debug(
            "Creating GnmiRequest with updated verification options",
            extra={
                "updates": list(kwargs.keys()),
                "original_strict_mode": (
                    self.verification_options.strict_mode
                    if self.verification_options
                    else None
                ),
                "original_cache_results": (
                    self.verification_options.cache_results
                    if self.verification_options
                    else None
                ),
            },
        )

        # Create a copy of current verification options
        current_options = self.verification_options or VerificationOptions()

        # Update with new values
        updated_options = VerificationOptions(
            strict_mode=kwargs.get("strict_mode", current_options.strict_mode),
            cache_results=kwargs.get(
                "cache_results", current_options.cache_results
            ),
            ttl_minutes=kwargs.get("ttl_minutes", current_options.ttl_minutes),
            required_models=kwargs.get(
                "required_models", current_options.required_models
            ),
        )

        # Create new request with updated options
        new_request = GnmiRequest(
            path=self.path,
            prefix=self.prefix,
            encoding=self.encoding,
            datatype=self.datatype,
            verification_options=updated_options,
        )

        logger.debug(
            "Created new GnmiRequest with updated verification options",
            extra={
                "new_strict_mode": updated_options.strict_mode,
                "new_cache_results": updated_options.cache_results,
                "new_ttl_minutes": updated_options.ttl_minutes,
                "has_required_models": updated_options.required_models
                is not None,
            },
        )

        return new_request
