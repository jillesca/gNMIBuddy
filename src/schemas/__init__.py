#!/usr/bin/env python3
"""
Schemas module for shared data models and response contracts.

This module contains the core data structures and response models used
throughout the gNMIBuddy application. These schemas serve as contracts
between different parts of the system.
"""

# Device and inventory models
from .models import Device, DeviceListResult, DeviceErrorResult

# Response models for network operations
from .responses import (
    ErrorResponse,
    SuccessResponse,
    NetworkResponse,
    NetworkOperationResult,
    FeatureNotFoundResponse,
)

__all__ = [
    # Device models
    "Device",
    "DeviceListResult",
    "DeviceErrorResult",
    # Response models
    "ErrorResponse",
    "NetworkResponse",
    "SuccessResponse",
    "NetworkOperationResult",
    "FeatureNotFoundResponse",
]
