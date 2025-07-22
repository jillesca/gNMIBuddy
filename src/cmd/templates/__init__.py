#!/usr/bin/env python3
"""CLI templates package for organized template management"""

from .error_templates import ErrorTemplates
from .help_templates import HelpTemplates
from .usage_templates import UsageTemplates

__all__ = [
    "ErrorTemplates",
    "HelpTemplates",
    "UsageTemplates",
]
