#!/usr/bin/env python3
"""
Provides functions for retrieving MPLS information from network devices using gNMI.
"""

from src.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    OperationStatus,
    NetworkOperationResult,
)
from src.schemas.models import Device
from src.processors.protocols.mpls.mpls_processor import (
    process_mpls_data,
    generate_mpls_summary,
)
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.logging import get_logger, log_operation

logger = get_logger(__name__)


def mpls_request():
    return GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/mpls",
        ],
    )


def get_mpls_info(
    device: Device, include_details: bool = False
) -> NetworkOperationResult:
    """
    Get MPLS information from a network device.

    Args:
        device: Device object from inventory
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        NetworkOperationResult: Response object containing structured MPLS information
    """
    logger.debug(
        "Getting MPLS info from device %s, include_details: %s",
        device.name,
        include_details,
    )

    response = get_gnmi_data(device, mpls_request())
    logger.debug(
        "gNMI response type: %s, status: %s",
        type(response).__name__,
        getattr(response, "status", "N/A"),
    )

    if isinstance(response, ErrorResponse):
        logger.debug(
            "ErrorResponse details - type: %s, message: %s",
            response.type,
            response.message,
        )
        logger.error("Error retrieving MPLS information: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="mpls_info",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    try:
        # Work directly with response data
        if isinstance(response, SuccessResponse):
            raw_data = response.data
            logger.debug(
                "SuccessResponse data length: %d",
                len(raw_data) if raw_data else 0,
            )
            mpls_data = process_mpls_data(raw_data)
        else:
            logger.debug("No SuccessResponse, processing empty data")
            mpls_data = process_mpls_data([])

        logger.debug(
            "Processed MPLS data keys: %s",
            str(list(mpls_data.keys()) if mpls_data else []),
        )

        summary = generate_mpls_summary(mpls_data)
        logger.debug("Generated MPLS summary type: %s", type(summary).__name__)

        # Add summary to the mpls_data for consistent return format
        mpls_data["summary"] = summary

        final_result = NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="mpls_info",
            status=OperationStatus.SUCCESS,
            data={
                "mpls_data": mpls_data,
                "summary": (
                    summary
                    if isinstance(summary, dict)
                    else {"summary": summary}
                ),
            },
            metadata={"include_details": include_details},
        )

        logger.info("MPLS data successfully processed for %s", device.name)
        logger.debug(
            "Final NetworkOperationResult - status: %s, data keys: %s",
            final_result.status,
            str(list(final_result.data.keys())),
        )

        return final_result

    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error parsing MPLS data: %s", str(e))
        logger.debug("Exception details: %s", str(e), exc_info=True)
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing MPLS data: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="mpls_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )
