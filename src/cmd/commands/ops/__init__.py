#!/usr/bin/env python3
"""Operations command implementations"""

from .logs import ops_logs
from .test_all import ops_test_all

__all__ = [
    "ops_logs",
    "ops_test_all",
]
