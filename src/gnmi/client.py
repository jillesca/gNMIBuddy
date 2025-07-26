#!/usr/bin/env python3
"""
gNMI client module for interacting with network devices via gNMI.

This module provides the main interface for gNMI operations with automatic
retry handling, proper error management, and structured response parsing.
"""
import os
import sys
import grpc
from pygnmi.client import gNMIclient

# Add parent directory to path when running as standalone for development
if __name__ == "__main__":
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

from src.schemas.models import Device
from src.inventory.file_handler import parse_json_file
from src.gnmi.parameters import GnmiRequest
from src.schemas.responses import (
    SuccessResponse,
    ErrorResponse,
    NetworkResponse,
)
from src.gnmi.error_handlers import (
    handle_timeout_error,
    handle_rpc_error,
    handle_connection_refused,
    handle_generic_error,
)
from src.gnmi.retry_handler import with_retry
from src.gnmi.response_parser import parse_gnmi_response, ParsedGnmiResponse
from src.logging.config import get_logger

logger = get_logger(__name__)


class GnmiConnectionManager:
    """Manages gNMI connection parameters and client creation."""

    @staticmethod
    def create_connection_params(device: Device) -> dict:
        """
        Create gNMI connection parameters from device configuration.

        Args:
            device: Device object containing connection information

        Returns:
            Dictionary of gNMI connection parameters
        """
        logger.debug(
            "Creating gNMI connection params for device %s (%s:%d)",
            device.name,
            device.ip_address,
            device.port,
        )

        params = {
            "target": (device.ip_address, device.port),
            "username": device.username,
            "password": device.password,
            "insecure": device.insecure,
            "path_cert": device.path_cert,
            "path_key": device.path_key,
            "path_root": device.path_root,
            "override": device.override,
            "skip_verify": device.skip_verify,
            "gnmi_timeout": device.gnmi_timeout,
            "grpc_options": device.grpc_options,
            "show_diff": device.show_diff,
        }

        logger.debug(
            "Connection params created - target: %s, username: %s, insecure: %s, timeout: %s",
            params["target"],
            params["username"],
            params["insecure"],
            params["gnmi_timeout"],
        )

        return params


class GnmiRequestExecutor:
    """Executes gNMI requests without retry logic."""

    def __init__(self):
        self.connection_manager = GnmiConnectionManager()

    def execute_request(
        self, device: Device, request: GnmiRequest
    ) -> NetworkResponse:
        """
        Execute a single gNMI request.

        Args:
            device: Device to connect to
            request: gNMI request parameters

        Returns:
            NetworkResponse from the request

        Raises:
            Exception: Any exception from the gNMI operation
        """
        logger.debug("Executing gNMI request for device %s", device.name)
        logger.debug("Request paths: %s", str(request.path))
        logger.debug(
            "Request encoding: %s", getattr(request, "encoding", "default")
        )

        connection_params = self.connection_manager.create_connection_params(
            device
        )

        logger.debug("Establishing gNMI connection to %s", device.name)
        try:
            with gNMIclient(**connection_params) as gnmi_client:
                logger.debug("gNMI client connected, executing get request")

                # Execute the gNMI get request
                request_params = request._as_dict()
                raw_response = gnmi_client.get(**request_params)

                # Log the raw response for debugging
                logger.debug("Raw gNMI response received from %s", device.name)
                logger.debug(
                    "Raw response type: %s", type(raw_response).__name__
                )
                logger.debug("Raw response content: %s", str(raw_response))

                # Parse the response
                logger.debug(
                    "Parsing gNMI response for device %s", device.name
                )
                parsed_data = parse_gnmi_response(raw_response)
                logger.debug(
                    "Response parsing completed - has_data: %s",
                    parsed_data.has_data if parsed_data else False,
                )

                # Create network response
                network_response = self._create_network_response(parsed_data)
                logger.debug(
                    "Created NetworkResponse - type: %s",
                    type(network_response).__name__,
                )

                return network_response

        except Exception as e:
            logger.debug("Exception during gNMI request execution: %s", str(e))
            raise  # Re-raise for error handler to process

    @staticmethod
    def _create_network_response(
        parsed_data: ParsedGnmiResponse,
    ) -> NetworkResponse:
        """
        Create a NetworkResponse from parsed gNMI data.

        Args:
            parsed_data: ParsedGnmiResponse object containing parsed response data

        Returns:
            Appropriate NetworkResponse
        """
        logger.debug("Creating NetworkResponse from parsed data")
        logger.debug("Parsed data exists: %s", parsed_data is not None)

        if parsed_data and parsed_data.has_data:
            logger.debug(
                "Parsed data has content, extracting first notification"
            )
            first_notification = parsed_data.first_notification

            if first_notification and first_notification.has_data:
                data = first_notification.updates
                timestamp = first_notification.timestamp

                logger.debug(
                    "SuccessResponse created - data items: %d, timestamp: %s",
                    len(data) if data else 0,
                    timestamp,
                )

                return SuccessResponse(data=data, timestamp=timestamp)
            else:
                logger.debug("First notification has no data")
        else:
            logger.debug("Parsed data is empty or has no content")

        logger.debug("Creating ErrorResponse for no data")
        return ErrorResponse(
            type="NO_DATA", message="No data returned from device"
        )


class GnmiErrorHandler:
    """Handles gNMI-specific exceptions using existing error handlers."""

    @staticmethod
    def handle_exception(device: Device, error: Exception) -> NetworkResponse:
        """
        Handle gNMI exceptions using appropriate error handlers.

        Args:
            device: Device object
            error: Exception that occurred

        Returns:
            Appropriate error response
        """
        logger.debug(
            "Handling gNMI exception for device %s: %s",
            device.name,
            type(error).__name__,
        )
        logger.debug("Exception details: %s", str(error))

        if isinstance(error, grpc.FutureTimeoutError):
            logger.debug("Handling timeout error")
            return handle_timeout_error(device)
        elif isinstance(error, grpc.RpcError):
            logger.debug(
                "Handling RPC error - code: %s",
                getattr(error, "code", "unknown"),
            )
            return handle_rpc_error(device, error)
        elif isinstance(error, ConnectionRefusedError):
            logger.debug("Handling connection refused error")
            return handle_connection_refused(device)
        else:
            logger.debug("Handling generic error: %s", type(error).__name__)
            return handle_generic_error(device, error)


def get_gnmi_data(
    device: Device,
    request: GnmiRequest,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> NetworkResponse:
    """
    Get data from a gNMI target with automatic retry for rate limiting.

    This is the main entry point for gNMI operations. It automatically handles
    rate limiting with exponential backoff and provides structured error handling.

    Args:
        device: Device object containing connection information
        request: GnmiRequest object containing the request parameters
        max_retries: Maximum number of retry attempts for rate limited requests
        base_delay: Base delay in seconds for exponential backoff

    Returns:
        NetworkResponse containing either success data or error information
    """
    logger.debug(
        "Starting gNMI operation for device '%s' with %d max retries",
        device.name,
        max_retries,
    )
    logger.debug(
        "Request details - paths: %d, encoding: %s",
        len(request.path) if request.path else 0,
        getattr(request, "encoding", "default"),
    )

    executor = GnmiRequestExecutor()
    error_handler = GnmiErrorHandler()

    def execute_operation() -> NetworkResponse:
        """Inner function for retry mechanism."""
        logger.debug(
            "Executing gNMI operation attempt for device %s", device.name
        )
        try:
            result = executor.execute_request(device, request)
            logger.debug(
                "gNMI operation completed successfully for device %s",
                device.name,
            )
            return result
        except Exception as error:
            logger.debug(
                "gNMI operation failed for device %s, handling error",
                device.name,
            )
            return error_handler.handle_exception(device, error)

    try:
        logger.debug("Starting retry mechanism for device %s", device.name)
        # Use retry handler for rate limiting protection
        final_result = with_retry(
            operation=execute_operation,
            device=device,
            max_retries=max_retries,
            base_delay=base_delay,
        )

        logger.debug(
            "gNMI operation completed for device %s - result type: %s",
            device.name,
            type(final_result).__name__,
        )

        return final_result

    except Exception as error:
        # Final fallback for any unexpected errors
        logger.error(
            "Unexpected error in gNMI operation for device '%s': %s",
            device.name,
            str(error),
        )
        logger.debug(
            "Final fallback error handling for device %s", device.name
        )
        return error_handler.handle_exception(device, error)


# Development and testing code
if __name__ == "__main__":
    from pprint import pprint as pp
    from src.logging.config import configure_logging
    from src.schemas.responses import OperationStatus

    # Configure detailed logging for development
    configure_logging("DEBUG")
    logger = get_logger(__name__)

    logger.info("Starting gNMI client development testing...")

    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Path to sandbox.json (one level up from the gnmi directory)
        json_file_path = os.path.join(
            os.path.dirname(script_dir), "hosts.json"
        )

        logger.info("Loading device inventory from: %s", json_file_path)

        # Parse the JSON file to get device information
        devices = parse_json_file(json_file_path)
        if not devices:
            logger.error("No devices found in inventory file")
            exit(1)

        device = Device(**devices[0])
        logger.info(
            "Testing with device: %s (%s:%d)",
            device.name,
            device.ip_address,
            device.port,
        )

        # Creating a GnmiRequest for an example query
        request = GnmiRequest(
            path=[
                "openconfig-interfaces:interfaces/interface[name=*]/state/admin-status",
                "openconfig-interfaces:interfaces/interface[name=*]/state/oper-status",
            ],
            encoding="json_ietf",
        )

        logger.info("Executing gNMI request...")
        logger.debug("Request paths: %s", request.path)

        # Execute the request
        result = get_gnmi_data(device, request)

        # Display results
        print("\n" + "=" * 60)
        print("gNMI REQUEST RESULTS")
        print("=" * 60)

        print(f"\nDevice: {device.name}")
        print(f"Status: {result.status.value}")

        if result.status == OperationStatus.SUCCESS:
            print(f"Operation: {result.operation_type}")
            print(f"Data items: {len(result.data) if result.data else 0}")
            print(f"\nResponse data:")
            pp(result.data)

            if hasattr(result, "metadata") and result.metadata:
                print(f"\nMetadata:")
                pp(result.metadata)
        else:
            print(
                f"Error Type: {result.error_response.type if result.error_response else 'Unknown'}"
            )
            print(
                f"Error Message: {result.error_response.message if result.error_response else 'No message'}"
            )

            if result.feature_not_found_response:
                print(
                    f"Feature: {result.feature_not_found_response.feature_name}"
                )
                print(
                    f"Feature Message: {result.feature_not_found_response.message}"
                )

        print("\n" + "=" * 60)
        logger.info("Development testing completed successfully")

    except FileNotFoundError as e:
        logger.error("Inventory file not found: %s", e)
        print(f"\nERROR: Could not find inventory file at {json_file_path}")
        print(
            "Please ensure you have a valid inventory file or update the path."
        )
        exit(1)

    except Exception as e:
        logger.error("Development testing failed: %s", e)
        print(f"\nERROR: Development testing failed: {e}")
        pp(e)
        exit(1)
