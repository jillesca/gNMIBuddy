"""
Pytest configuration file for tests.
"""

import sys
import os

# Add src to the path so imports work
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# Disable capability verification during tests
os.environ["GNMIBUDDY_DISABLE_CAPABILITY_VERIFICATION"] = "1"
