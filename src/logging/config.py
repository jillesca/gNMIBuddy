#!/usr/bin/env python3
"""
Logging configuration module for network tools application.
Provides centralized logging configuration following OpenTelemetry best practices.
"""
import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Optional, Any, Union

from .external_suppression import (
    ExternalLibrarySuppressor,
    setup_cli_suppression,
)


# Application-specific logger names for easy filtering
class LoggerNames:
    """Standard logger names for the application following OTel conventions."""

    APP_ROOT = "gnmibuddy"

    # Core modules
    API = f"{APP_ROOT}.api"
    CLI = f"{APP_ROOT}.cli"
    MCP = f"{APP_ROOT}.mcp"

    # Data collection modules
    COLLECTORS = f"{APP_ROOT}.collectors"
    INTERFACES = f"{COLLECTORS}.interfaces"
    ROUTING = f"{COLLECTORS}.routing"
    MPLS = f"{COLLECTORS}.mpls"
    VPN = f"{COLLECTORS}.vpn"
    LOGS = f"{COLLECTORS}.logs"
    SYSTEM = f"{COLLECTORS}.system"
    TOPOLOGY = f"{COLLECTORS}.topology"
    PROFILE = f"{COLLECTORS}.profile"

    # Infrastructure modules
    GNMI = f"{APP_ROOT}.gnmi"
    INVENTORY = f"{APP_ROOT}.inventory"
    PROCESSORS = f"{APP_ROOT}.processors"
    SERVICES = f"{APP_ROOT}.services"
    UTILS = f"{APP_ROOT}.utils"

    # External modules we want to control
    PYGNMI = "pygnmi"
    GRPC = "grpc"


class OTelFormatter(logging.Formatter):
    """
    Custom formatter that follows OpenTelemetry logging conventions.
    Includes structured fields that can be easily parsed by observability tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Add OTel standard fields
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": getattr(record, "module", record.name.split(".")[-1]),
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add trace context if available (for future OTel integration)
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = getattr(record, "trace_id")
        if hasattr(record, "span_id"):
            log_data["span_id"] = getattr(record, "span_id")

        # Add custom fields
        if hasattr(record, "device_name"):
            log_data["device_name"] = getattr(record, "device_name")
        if hasattr(record, "operation"):
            log_data["operation"] = getattr(record, "operation")
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = getattr(record, "duration_ms")

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class LoggingConfig:
    """Centralized logging configuration with module-specific control."""

    _configured = False
    _module_levels: Dict[str, int] = {}
    _last_config: Dict[str, Any] = {}

    @classmethod
    def configure(
        cls,
        global_level: Optional[str] = None,
        module_levels: Optional[Dict[str, str]] = None,
        enable_structured: bool = False,
        enable_file_output: bool = True,
        log_file: Optional[str] = None,
        enable_external_suppression: bool = True,
        external_suppression_mode: str = "cli",  # "cli", "mcp", "development"
    ) -> logging.Logger:
        """
        Configure application logging with OTel best practices.

        Args:
            global_level: Global logging level (debug, info, warning, error)
            module_levels: Dict mapping module names to specific log levels
            enable_structured: Whether to use structured JSON logging
            enable_file_output: Whether to log to file
            log_file: Custom log file path
            enable_external_suppression: Whether to suppress external library noise
            external_suppression_mode: Type of suppression ("cli", "mcp", "development")
        """
        # Check if configuration has changed
        current_config = {
            "global_level": global_level,
            "module_levels": module_levels,
            "enable_structured": enable_structured,
            "enable_file_output": enable_file_output,
            "log_file": log_file,
            "enable_external_suppression": enable_external_suppression,
            "external_suppression_mode": external_suppression_mode,
        }

        if cls._configured and cls._last_config == current_config:
            return logging.getLogger(LoggerNames.APP_ROOT)

        # Store the new configuration
        cls._last_config = current_config.copy()

        # Apply external library suppression early (before other logging config)
        if enable_external_suppression:
            cls._setup_external_suppression(
                external_suppression_mode, module_levels
            )

        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }

        # Set global level
        global_log_level = level_map.get(
            global_level.lower() if global_level else "info", logging.INFO
        )

        # Clear any existing configuration
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Create formatters
        if enable_structured:
            formatter = OTelFormatter()
        else:
            # Human-readable format with OTel-friendly structure
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)-4d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        # Create handlers
        handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(global_log_level)
        handlers.append(console_handler)

        # File handler
        if enable_file_output:
            if not log_file:
                log_dir = os.path.join(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(os.path.abspath(__file__))
                        )
                    ),
                    "logs",
                )
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, "gnmibuddy.log")

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)  # File gets everything
            handlers.append(file_handler)

        # Configure root logger
        root_logger.setLevel(logging.DEBUG)  # Let handlers filter
        for handler in handlers:
            root_logger.addHandler(handler)

        # Set module-specific levels (after external suppression)
        cls._set_module_levels(module_levels or {}, level_map)

        cls._configured = True

        app_logger = logging.getLogger(LoggerNames.APP_ROOT)
        app_logger.debug(
            "Logging configured",
            extra={
                "global_level": global_level or "info",
                "structured": enable_structured,
                "file_output": enable_file_output,
                "log_file": log_file,
                "external_suppression": enable_external_suppression,
                "suppression_mode": external_suppression_mode,
            },
        )

        return app_logger

    @classmethod
    def _setup_external_suppression(
        cls, mode: str, module_levels: Optional[Dict[str, str]] = None
    ) -> None:
        """Setup external library suppression based on mode."""

        # Get any custom external library levels from module_levels
        external_custom_levels = {}
        if module_levels:
            for (
                lib_name
            ) in ExternalLibrarySuppressor.get_default_suppressions().keys():
                if lib_name in module_levels:
                    external_custom_levels[lib_name] = module_levels[lib_name]

        # Apply suppression based on mode
        if mode == "mcp":
            from .external_suppression import setup_mcp_suppression

            setup_mcp_suppression()
        elif mode == "development":
            from .external_suppression import setup_development_suppression

            setup_development_suppression()
        else:  # Default to "cli"
            from .external_suppression import setup_cli_suppression

            setup_cli_suppression()

        # Apply any custom levels for external libraries
        if external_custom_levels:
            ExternalLibrarySuppressor.setup_python_logging_suppression(
                custom_levels=external_custom_levels, include_defaults=False
            )

    @classmethod
    def _set_module_levels(
        cls, module_levels: Dict[str, str], level_map: Dict[str, int]
    ):
        """Set specific logging levels for different modules."""
        cls._module_levels = {}

        for module_name, level_str in module_levels.items():
            level = level_map.get(level_str.lower())
            if level:
                cls._module_levels[module_name] = level
                logger = logging.getLogger(module_name)
                logger.setLevel(level)

    @classmethod
    def set_module_level(cls, module_name: str, level: Union[str, int]):
        """Dynamically change the log level for a specific module."""
        if isinstance(level, str):
            level_map = {
                "debug": logging.DEBUG,
                "info": logging.INFO,
                "warning": logging.WARNING,
                "error": logging.ERROR,
            }
            level = level_map.get(level.lower(), logging.INFO)

        cls._module_levels[module_name] = level
        logger = logging.getLogger(module_name)
        logger.setLevel(level)

    @classmethod
    def get_module_levels(cls) -> Dict[str, str]:
        """Get current module-specific log levels."""
        level_names = {
            logging.DEBUG: "debug",
            logging.INFO: "info",
            logging.WARNING: "warning",
            logging.ERROR: "error",
        }
        return {
            module: level_names.get(level, "unknown")
            for module, level in cls._module_levels.items()
        }


def configure_logging(
    log_level: Optional[str] = None,
    module_levels: Optional[Dict[str, str]] = None,
    structured: bool = False,
    external_suppression_mode: str = "cli",
) -> logging.Logger:
    """
    Configure the application's logging with OTel best practices.

    Args:
        log_level: Global logging level (debug, info, warning, error)
        module_levels: Dict mapping module names to specific log levels
        structured: Whether to use structured JSON logging
        external_suppression_mode: Type of external library suppression

    Returns:
        Configured root application logger
    """
    return LoggingConfig.configure(
        global_level=log_level,
        module_levels=module_levels,
        enable_structured=structured,
        external_suppression_mode=external_suppression_mode,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module with proper naming convention.

    Args:
        name: The module name (typically __name__)

    Returns:
        A configured logger instance
    """
    # Convert Python module names to our logger naming convention
    if name.startswith("src."):
        # Convert src.collectors.interfaces -> gnmibuddy.collectors.interfaces
        name = name.replace("src.", LoggerNames.APP_ROOT + ".", 1)
    elif name.startswith("__main__"):
        name = LoggerNames.APP_ROOT
    elif not name.startswith(LoggerNames.APP_ROOT):
        # For modules outside our app, keep their original name
        pass

    return logging.getLogger(name)


def log_operation(operation_name: str, device_name: Optional[str] = None):
    """
    Decorator to log function execution with OTel-compatible operation tracking.

    Args:
        operation_name: Name of the operation being performed
        device_name: Optional device name for context
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = datetime.now()

            # Extract device name from args if not provided
            actual_device_name = device_name
            if not actual_device_name and args:
                # Look for device parameter
                for arg in args:
                    if hasattr(arg, "name"):
                        actual_device_name = arg.name
                        break

            extra = {
                "operation": operation_name,
                "function": func.__name__,
            }
            if actual_device_name:
                extra["device_name"] = actual_device_name

            logger.debug("Starting %s", operation_name, extra=extra)

            try:
                result = func(*args, **kwargs)

                duration = (datetime.now() - start_time).total_seconds() * 1000
                extra["duration_ms"] = round(duration, 2)

                logger.debug("Completed %s", operation_name, extra=extra)
                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                extra["duration_ms"] = round(duration, 2)
                extra["error"] = str(e)

                logger.error(
                    "Failed %s", operation_name, extra=extra, exc_info=True
                )
                raise

        return wrapper

    return decorator
