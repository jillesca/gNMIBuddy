#!/usr/bin/env python3
"""
Standard logger names for gNMIBuddy application.

This module defines the hierarchical logger naming convention following
OpenTelemetry best practices. All logger names are centralized here to
ensure consistency and prevent typos.

The naming follows the pattern: gnmibuddy.<component>.<subcomponent>
This allows for easy filtering and hierarchical log level control.
"""


class LoggerNames:
    """
    Standard logger names for the application following OTel conventions.

    Provides a centralized registry of all logger names used throughout
    the application, ensuring consistency and enabling hierarchical
    log level control.
    """

    # Root application logger
    APP_ROOT = "gnmibuddy"

    # Core application components
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

    @classmethod
    def get_all_application_loggers(cls) -> list[str]:
        """
        Get all application-specific logger names.

        Returns:
            List of all gnmibuddy.* logger names (excludes external libraries)
        """
        return [
            cls.APP_ROOT,
            cls.API,
            cls.CLI,
            cls.MCP,
            cls.COLLECTORS,
            cls.INTERFACES,
            cls.ROUTING,
            cls.MPLS,
            cls.VPN,
            cls.LOGS,
            cls.SYSTEM,
            cls.TOPOLOGY,
            cls.PROFILE,
            cls.GNMI,
            cls.INVENTORY,
            cls.PROCESSORS,
            cls.SERVICES,
            cls.UTILS,
        ]

    @classmethod
    def get_external_library_loggers(cls) -> list[str]:
        """
        Get external library logger names that we want to control.

        Returns:
            List of external library logger names
        """
        return [
            cls.PYGNMI,
            cls.GRPC,
        ]

    @classmethod
    def is_application_logger(cls, logger_name: str) -> bool:
        """
        Check if a logger name belongs to the application.

        Args:
            logger_name: Logger name to check

        Returns:
            True if logger is part of the application hierarchy
        """
        return logger_name.startswith(cls.APP_ROOT)

    @classmethod
    def is_external_logger(cls, logger_name: str) -> bool:
        """
        Check if a logger name belongs to an external library.

        Args:
            logger_name: Logger name to check

        Returns:
            True if logger is from an external library we control
        """
        external_prefixes = cls.get_external_library_loggers()
        return any(
            logger_name.startswith(prefix) for prefix in external_prefixes
        )
