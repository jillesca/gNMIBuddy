#!/usr/bin/env python3

"""
Test module to diagnose type annotation issues in NetworkTools response classes
"""

from typing import Dict
import sys

# Add src to path
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.network_tools.responses import (
    InterfaceResponse,
    MplsResponse,
    RoutingResponse,
    VpnResponse,
    LogResponse,
    NetworkToolsResponse,
)


def test_summary_field_types():
    """Test to print out details of summary field types in all response classes"""

    # Create an instance of each class to test
    classes = [
        InterfaceResponse(),
        MplsResponse(),
        RoutingResponse(),
        VpnResponse(),
        LogResponse(),
    ]

    for instance in classes:
        cls_name = instance.__class__.__name__
        print(f"\n{cls_name} summary field inspection:")

        # Get the summary field value and its type
        summary_value = getattr(instance, "summary", None)
        summary_type = (
            type(summary_value).__name__
            if summary_value is not None
            else "None"
        )
        print(f"  summary field value: {summary_value}")
        print(f"  summary field type: {summary_type}")

        # Test the to_dict method with an empty result
        try:
            test_result = {"logs": [], "interfaces": [], "data": {}}
            try:
                test_result["summary"] = instance.summary
                print(
                    f"  Setting test_result['summary'] = instance.summary: SUCCESS"
                )
            except Exception as e:
                print(
                    f"  Setting test_result['summary'] = instance.summary: FAILED - {type(e).__name__}: {str(e)}"
                )
        except Exception as e:
            print(
                f"  Error testing result assignment: {type(e).__name__}: {str(e)}"
            )

        # Check result of actual to_dict method
        try:
            result = instance.to_dict()
            print(f"  to_dict() return type: {type(result).__name__}")
            print(f"  to_dict() result: {result}")
        except Exception as e:
            print(f"  Error in to_dict(): {type(e).__name__}: {str(e)}")

        print("")


if __name__ == "__main__":
    test_summary_field_types()
