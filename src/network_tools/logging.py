#!/usr/bin/env python3
"""
Logging functions module.
Provides functions for retrieving logging information from network devices using gNMI.
"""

import logging
from typing import Optional
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import GnmiError
from src.inventory.models import Device
from src.network_tools.responses import LogResponse
from src.parsers.logs.filter import filter_logs


logger = logging.getLogger(__name__)


def get_logging_information(
    device: Device,
    keywords: Optional[str] = None,
    minutes: Optional[int] = 5,
    show_all_logs: bool = False,
) -> LogResponse:
    """
    Get logging information from a network device.

    Args:
        device: Device object containing device information
        keywords: Optional keywords to filter logs
        minutes: Number of minutes to filter logs (default: 5 minutes)
        show_all_logs: If True, return all logs without time filtering (default: False)

    Returns:
        LogResponse object containing logs or error information
    """
    # Prepare filter information for inclusion in the response
    filter_info = {
        "keywords": keywords,
        "filter_minutes": minutes if not show_all_logs else None,
        "show_all_logs": show_all_logs,
    }

    log_filter = (
        "(-[1-5]-|ISIS|BGP|ADJCHANGE|LINK-3|LINEPROTO|MPLS|VRF|VPN|CONFIG-3)"
    )

    if keywords:
        log_filter = f"(-[1-5]-|{keywords}) | utility egrep -v logged"

    log_query = f"show logging | utility egrep '{log_filter}' | utility egrep -v logged "

    # Create a GnmiRequest with the appropriate parameters for logs
    log_request = GnmiRequest(xpath=[log_query], encoding="ascii")

    response = get_gnmi_data(device=device, request=log_request)

    # logger.debug(f"Raw log response: {response}")

    if response.is_error():
        logger.error(
            f"Failed to get logs from {device.name}: {response.error}"
        )
        return LogResponse.error_response(
            response.error, device_name=device.name
        )

    try:
        # Process the logs through the filter
        filtered_logs = filter_logs(response.to_dict(), show_all_logs, minutes)

        if "error" in filtered_logs:
            return LogResponse.error_response(
                GnmiError(
                    type="LOG_PROCESSING_ERROR", message=filtered_logs["error"]
                ),
                device_name=device.name,
            )

        # Create a response with the filtered logs
        return LogResponse.from_logs(
            filtered_logs, device_name=device.name, filter_info=filter_info
        )
    except Exception as e:
        logger.error(f"Error processing logs from {device.name}: {str(e)}")
        return LogResponse.error_response(
            GnmiError(
                type="LOG_PROCESSING_ERROR",
                message=f"Error processing logs: {str(e)}",
            ),
            device_name=device.name,
        )
