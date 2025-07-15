#!/usr/bin/env python3
"""
Parsers for network logs.
"""

from src.processors.logs.filter import filter_logs, filter_logs_by_time

__all__ = ["filter_logs", "filter_logs_by_time"]
