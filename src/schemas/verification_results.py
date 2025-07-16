#!/usr/bin/env python3
"""
Verification results schemas for OpenConfig capability verification.

This module provides structured data models for representing OpenConfig
model verification results, supporting both single model and multi-model
verification operations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from ..schemas.openconfig_models import OpenConfigModel


class VerificationStatus(Enum):
    """
    Enumeration for verification status values.

    Provides type safety and clear status representation for OpenConfig
    model verification results.
    """

    SUPPORTED = "supported"
    VERSION_WARNING = "version_warning"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass
class ModelVerificationResult:
    """
    Result of verifying a single OpenConfig model against a device.

    Attributes:
        model: The OpenConfig model that was verified
        status: The verification status
        found_version: The version found on the device (None if not found)
        required_version: The minimum required version for this model
        warning_message: Optional warning message for version issues
        error_message: Optional error message for failures
    """

    model: OpenConfigModel
    status: VerificationStatus
    found_version: Optional[str] = None
    required_version: str = ""
    warning_message: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ModelVerificationResult to dictionary representation.

        Returns:
            Dictionary containing all result fields with enum values converted to strings
        """
        return {
            "model": self.model.value,
            "status": self.status.value,
            "found_version": self.found_version,
            "required_version": self.required_version,
            "warning_message": self.warning_message,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVerificationResult":
        """
        Create ModelVerificationResult from dictionary representation.

        Args:
            data: Dictionary containing result fields

        Returns:
            ModelVerificationResult instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            model = OpenConfigModel(data["model"])
            status = VerificationStatus(data["status"])

            return cls(
                model=model,
                status=status,
                found_version=data.get("found_version"),
                required_version=data.get("required_version", ""),
                warning_message=data.get("warning_message"),
                error_message=data.get("error_message"),
            )
        except (KeyError, ValueError) as e:
            raise ValueError(
                f"Invalid ModelVerificationResult data: {e}"
            ) from e


@dataclass
class MultiModelVerificationResult:
    """
    Result of verifying multiple OpenConfig models against a device.

    Attributes:
        overall_status: Overall verification status across all models
        model_results: Dictionary mapping each model to its verification result
    """

    overall_status: VerificationStatus
    model_results: Dict[OpenConfigModel, ModelVerificationResult] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert MultiModelVerificationResult to dictionary representation.

        Returns:
            Dictionary containing overall status and all model results
        """
        return {
            "overall_status": self.overall_status.value,
            "model_results": {
                model.value: result.to_dict()
                for model, result in self.model_results.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultiModelVerificationResult":
        """
        Create MultiModelVerificationResult from dictionary representation.

        Args:
            data: Dictionary containing overall status and model results

        Returns:
            MultiModelVerificationResult instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            overall_status = VerificationStatus(data["overall_status"])
            model_results = {}

            for model_str, result_data in data.get(
                "model_results", {}
            ).items():
                model = OpenConfigModel(model_str)
                model_results[model] = ModelVerificationResult.from_dict(
                    result_data
                )

            return cls(
                overall_status=overall_status,
                model_results=model_results,
            )
        except (KeyError, ValueError) as e:
            raise ValueError(
                f"Invalid MultiModelVerificationResult data: {e}"
            ) from e

    def get_result_for_model(
        self, model: OpenConfigModel
    ) -> Optional[ModelVerificationResult]:
        """
        Get the verification result for a specific model.

        Args:
            model: The OpenConfig model to get results for

        Returns:
            ModelVerificationResult if found, None otherwise
        """
        return self.model_results.get(model)

    def is_model_supported(self, model: OpenConfigModel) -> bool:
        """
        Check if a specific model is supported (status is SUPPORTED or VERSION_WARNING).

        Args:
            model: The OpenConfig model to check

        Returns:
            True if model is supported, False otherwise
        """
        result = self.get_result_for_model(model)
        if not result:
            return False
        return result.status in (
            VerificationStatus.SUPPORTED,
            VerificationStatus.VERSION_WARNING,
        )

    def has_warnings(self) -> bool:
        """
        Check if any model has version warnings.

        Returns:
            True if any model has version warnings, False otherwise
        """
        return any(
            result.status == VerificationStatus.VERSION_WARNING
            for result in self.model_results.values()
        )

    def has_errors(self) -> bool:
        """
        Check if any model has errors.

        Returns:
            True if any model has errors, False otherwise
        """
        return any(
            result.status
            in (VerificationStatus.NOT_FOUND, VerificationStatus.ERROR)
            for result in self.model_results.values()
        )

    def get_supported_models(
        self,
    ) -> Dict[OpenConfigModel, ModelVerificationResult]:
        """
        Get all models that are supported (SUPPORTED or VERSION_WARNING status).

        Returns:
            Dictionary of supported models and their results
        """
        return {
            model: result
            for model, result in self.model_results.items()
            if result.status
            in (
                VerificationStatus.SUPPORTED,
                VerificationStatus.VERSION_WARNING,
            )
        }

    def get_unsupported_models(
        self,
    ) -> Dict[OpenConfigModel, ModelVerificationResult]:
        """
        Get all models that are not supported (NOT_FOUND or ERROR status).

        Returns:
            Dictionary of unsupported models and their results
        """
        return {
            model: result
            for model, result in self.model_results.items()
            if result.status
            in (VerificationStatus.NOT_FOUND, VerificationStatus.ERROR)
        }
