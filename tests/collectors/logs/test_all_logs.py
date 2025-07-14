import os
import sys


# Adjust path to include the parent directory
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)

from src.processors.logs.filter import filter_logs


class TestShowAllLogs:
    """Test cases specifically for the show_all_logs feature."""

    def test_filter_logs_with_show_all_logs(self):
        """Test that logs are properly formatted when show_all_logs is True."""
        # Sample raw log data from device
        gnmi_data = [
            {
                "val": """
RP/0/RP0/CPU0:Apr 23 12:52:06.929 UTC: ISIS-6-ADJCHANGE : Adjacency to pe2 (GigabitEthernet0/0/0/0) (L2) Up, Adjacency to pe2 (GigabitEthernet0/0/0/0) (L2) Up
RP/0/RP0/CPU0:Apr 24 10:15:30.123 UTC: BGP-5-ADJCHANGE: neighbor 10.1.1.1 Up
RP/0/RP0/CPU0:Apr 24 11:22:45.789 UTC: MPLS-3-LDP_NEIGHBOR: LDP neighbor 192.168.1.1 is up
"""
            }
        ]

        # Call the filter_logs function with show_all_logs=True
        result = filter_logs(gnmi_data, show_all_logs=True, filter_minutes=5)

        # Verify the result structure
        assert "logs" in result
        assert "summary" in result
        assert "log_count" in result["summary"]

        # Should contain all 3 log entries
        assert result["summary"]["log_count"] == 3
        assert len(result["logs"]) == 3

        # Verify content of logs
        assert any(
            "ISIS-6-ADJCHANGE" in log["message"] for log in result["logs"]
        )
        assert any(
            "BGP-5-ADJCHANGE" in log["message"] for log in result["logs"]
        )
        assert any(
            "MPLS-3-LDP_NEIGHBOR" in log["message"] for log in result["logs"]
        )

    def test_filter_logs_with_time_filtering(self):
        """Test time filtering behavior when show_all_logs is False."""
        # Create sample log with realistic timestamp formats
        # Note: Using hardcoded timestamps instead of dynamically generated ones
        recent_log = "RP/0/RP0/CPU0:Apr 24 12:30:06.929 UTC: BGP-5-ADJCHANGE: neighbor 10.1.1.1 Up"
        old_log = "RP/0/RP0/CPU0:Apr 24 08:15:45.123 UTC: MPLS-3-LDP_NEIGHBOR: LDP neighbor 192.168.1.1 is up"

        gnmi_data = [
            {
                "val": f"""
{recent_log}
{old_log}
"""
            }
        ]

        # Mock the filter_logs_by_time function to simulate time filtering
        # This is necessary because our test might run at any time and the actual
        # filtering depends on the current time
        from unittest.mock import patch

        def mock_filter_by_time(logs, minutes, current_time=None):
            # Simulate filtering - only keep the recent log
            return recent_log

        with patch(
            "src.processors.logs.filter.filter_logs_by_time",
            side_effect=mock_filter_by_time,
        ):
            # Filter logs with 5 minutes threshold and show_all_logs=False
            result = filter_logs(
                gnmi_data, show_all_logs=False, filter_minutes=5
            )

            # Should contain only the recent log
            assert "logs" in result
            assert "summary" in result
            assert result["summary"]["log_count"] == 1
            assert len(result["logs"]) == 1
            assert "BGP-5-ADJCHANGE" in result["logs"][0]["message"]

    def test_empty_logs_handling(self):
        """Test that empty logs are handled properly."""
        gnmi_data = [{"val": ""}]

        result = filter_logs(gnmi_data, show_all_logs=True, filter_minutes=5)

        assert "logs" in result
        assert "summary" in result
        assert result["summary"]["log_count"] == 0
        assert len(result["logs"]) == 0
