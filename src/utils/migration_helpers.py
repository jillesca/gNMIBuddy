#!/usr/bin/env python3
"""
Migration helpers for OpenConfig capability verification refactoring.

Provides utilities to help migrate collectors from the old verification system
to the new smart verification system.
"""

import inspect
from typing import Any, Callable, Dict, List, Set

from ..schemas.openconfig_models import OpenConfigModel
from ..schemas.responses import NetworkOperationResult
from ..decorators.smart_capability_verification import verify_required_models

# Temporarily use standard logging to avoid circular import
import logging

logger = logging.getLogger(__name__)


def validate_collector_migration(collector_func: Callable) -> Dict[str, Any]:
    """
    Validate that a collector migration is correct.

    Args:
        collector_func: The collector function to validate

    Returns:
        Dictionary with validation results
    """
    validation_result = {
        "function_name": collector_func.__name__,
        "is_valid": True,
        "issues": [],
        "warnings": [],
        "recommendations": [],
    }

    # Check if function has the new decorator
    decorators = _get_function_decorators(collector_func)

    has_old_decorator = any(
        "verify_capabilities" in str(dec) for dec in decorators
    )
    has_new_decorator = any(
        "verify_required_models" in str(dec) for dec in decorators
    )

    if has_old_decorator and has_new_decorator:
        validation_result["is_valid"] = False
        validation_result["issues"].append(
            "Function has both old (@verify_capabilities) and new (@verify_required_models) decorators"
        )
    elif has_old_decorator:
        validation_result["warnings"].append(
            "Function still uses old @verify_capabilities decorator"
        )
        validation_result["recommendations"].append(
            "Replace @verify_capabilities() with @verify_required_models()"
        )
    elif not has_new_decorator:
        # Check if function needs verification by analyzing its code
        needs_verification = _analyze_function_needs_verification(
            collector_func
        )
        if needs_verification:
            validation_result["warnings"].append(
                "Function appears to need verification but has no decorator"
            )
            validation_result["recommendations"].append(
                "Add @verify_required_models() decorator"
            )

    # Check function signature
    sig = inspect.signature(collector_func)
    if "device" not in sig.parameters:
        validation_result["is_valid"] = False
        validation_result["issues"].append(
            "Function must have a 'device' parameter"
        )

    # Check return type annotation
    if sig.return_annotation != NetworkOperationResult:
        validation_result["warnings"].append(
            "Function should return NetworkOperationResult"
        )

    return validation_result


def get_collector_model_requirements(
    collector_func: Callable,
) -> Dict[str, Any]:
    """
    Analyze a collector function to determine its model requirements.

    Args:
        collector_func: The collector function to analyze

    Returns:
        Dictionary with model requirement analysis
    """
    analysis_result = {
        "function_name": collector_func.__name__,
        "required_models": set(),
        "detected_paths": [],
        "confidence": "unknown",
    }

    # Analyze function source code to find gNMI paths
    try:
        source = inspect.getsource(collector_func)
        analysis_result["detected_paths"] = _extract_gnmi_paths_from_source(
            source
        )
        analysis_result["required_models"] = _determine_models_from_paths(
            analysis_result["detected_paths"]
        )
        analysis_result["confidence"] = (
            "high" if analysis_result["required_models"] else "low"
        )
    except (OSError, ValueError) as e:
        logger.warning(
            "Could not analyze function %s: %s", collector_func.__name__, e
        )
        analysis_result["confidence"] = "unknown"

    return analysis_result


def check_backward_compatibility() -> Dict[str, Any]:
    """
    Check that the old verification system still works for backward compatibility.

    Returns:
        Dictionary with compatibility check results
    """
    compatibility_result = {
        "is_compatible": True,
        "issues": [],
        "warnings": [],
        "tested_components": [],
    }

    # Check if old decorator still exists and works
    try:
        from ..decorators.capability_verification import (
            verify_capabilities,
        )  # noqa: F401

        compatibility_result["tested_components"].append(
            "old_decorator_import"
        )
    except ImportError as e:
        compatibility_result["is_compatible"] = False
        compatibility_result["issues"].append(
            f"Old decorator import failed: {e}"
        )

    # Check if old verification service still exists
    try:
        from ..services.capability_verification import (
            verify_openconfig_network_instance,
        )  # noqa: F401

        compatibility_result["tested_components"].append(
            "old_verification_service"
        )
    except ImportError as e:
        compatibility_result["is_compatible"] = False
        compatibility_result["issues"].append(
            f"Old verification service import failed: {e}"
        )

    # Check if old cache functions still exist
    try:
        from ..utils.capability_cache import (  # noqa: F401
            is_device_verified,
            cache_verification_result,
            get_verification_result,
        )

        compatibility_result["tested_components"].append("old_cache_functions")
    except ImportError as e:
        compatibility_result["warnings"].append(
            f"Old cache functions import failed: {e}"
        )

    return compatibility_result


def migrate_collector_decorator(collector_func: Callable) -> Callable:
    """
    Programmatically migrate a collector function from old to new decorator.

    Args:
        collector_func: The collector function to migrate

    Returns:
        The migrated function with new decorator
    """
    # Remove old decorator if present
    if hasattr(collector_func, "__wrapped__"):
        # If function was decorated, try to get the original
        original_func = collector_func.__wrapped__
    else:
        original_func = collector_func

    # Apply new decorator
    migrated_func = verify_required_models()(original_func)

    # Copy metadata
    migrated_func.__name__ = original_func.__name__
    migrated_func.__doc__ = original_func.__doc__
    migrated_func.__module__ = original_func.__module__

    logger.info(
        "Migrated function %s to new decorator", original_func.__name__
    )

    return migrated_func


def _get_function_decorators(func: Callable) -> List[str]:
    """Extract decorators from a function."""
    decorators = []

    # Check if function has __wrapped__ attribute (indicating it was decorated)
    if hasattr(func, "__wrapped__"):
        decorators.append("decorated")

    # Try to get source and parse decorators
    try:
        source = inspect.getsource(func)
        lines = source.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("@"):
                decorators.append(line)
    except (OSError, ValueError):
        pass

    return decorators


def _analyze_function_needs_verification(func: Callable) -> bool:
    """Analyze if a function needs capability verification."""
    try:
        source = inspect.getsource(func)

        # Check for gNMI-related patterns
        gnmi_patterns = [
            "get_gnmi_data",
            "GnmiRequest",
            "openconfig-",
            "network-instance",
            "interfaces",
            "system",
        ]

        return any(pattern in source for pattern in gnmi_patterns)
    except (OSError, ValueError):
        return False


def _extract_gnmi_paths_from_source(source: str) -> List[str]:
    """Extract gNMI paths from function source code."""
    paths = []

    # Look for path patterns in the source
    import re

    # Match paths in GnmiRequest
    path_patterns = [
        r'"(openconfig-[^"]+)"',  # Quoted paths
        r"'(openconfig-[^']+)'",  # Single quoted paths
    ]

    for pattern in path_patterns:
        matches = re.findall(pattern, source)
        paths.extend(matches)

    return paths


def _determine_models_from_paths(paths: List[str]) -> Set[OpenConfigModel]:
    """Determine required models from gNMI paths."""
    models = set()

    for path in paths:
        if "openconfig-system" in path:
            models.add(OpenConfigModel.SYSTEM)
        elif "openconfig-interfaces" in path:
            models.add(OpenConfigModel.INTERFACES)
        elif "openconfig-network-instance" in path:
            models.add(OpenConfigModel.NETWORK_INSTANCE)

    return models


def generate_migration_report(collectors: List[Callable]) -> Dict[str, Any]:
    """
    Generate a comprehensive migration report for multiple collectors.

    Args:
        collectors: List of collector functions to analyze

    Returns:
        Dictionary with migration report
    """
    report = {
        "total_collectors": len(collectors),
        "migrated_collectors": 0,
        "needs_migration": 0,
        "has_issues": 0,
        "details": [],
    }

    for collector in collectors:
        validation = validate_collector_migration(collector)
        analysis = get_collector_model_requirements(collector)

        collector_report = {
            "function_name": collector.__name__,
            "validation": validation,
            "analysis": analysis,
            "migration_status": "unknown",
        }

        # Determine migration status
        if validation["is_valid"] and not validation["warnings"]:
            collector_report["migration_status"] = "migrated"
            report["migrated_collectors"] += 1
        elif validation["warnings"]:
            collector_report["migration_status"] = "needs_migration"
            report["needs_migration"] += 1
        else:
            collector_report["migration_status"] = "has_issues"
            report["has_issues"] += 1

        report["details"].append(collector_report)

    return report
