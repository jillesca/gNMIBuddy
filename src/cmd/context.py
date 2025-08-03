#!/usr/bin/env python3
"""Command context objects for dependency injection in Click-based CLI"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from src.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CLIContext:
    """Main CLI context object for dependency injection"""

    # Global options
    log_level: Optional[str] = None
    module_log_levels: Optional[str] = None
    structured_logging: bool = False
    quiet_external: bool = True
    device: Optional[str] = None
    all_devices: bool = False
    max_workers: int = 5
    inventory: Optional[str] = None
    env_file: Optional[str] = None
    settings: Optional[Any] = None  # Will hold GNMIBuddySettings instance

    # Internal state
    _initialized: bool = False
    _logger_configured: bool = False

    def __post_init__(self):
        """Initialize the context after creation"""
        if not self._initialized:
            self._configure_logging()
            self._initialized = True

    def _configure_logging(self):
        """Configure logging based on context settings"""
        if self._logger_configured:
            return

        from src.logging import LoggingConfigurator

        # Parse module-specific log levels
        module_levels = {}
        if self.module_log_levels:
            try:
                for item in self.module_log_levels.split(","):
                    if "=" in item:
                        module, level = item.strip().split("=", 1)
                        module_levels[module.strip()] = level.strip()
            except ValueError:
                logger.warning(
                    "Invalid module-log-levels format. Use 'module1=debug,module2=warning'"
                )

        LoggingConfigurator.configure(
            global_level=self.log_level or "info",
            module_levels=module_levels,
            enable_structured=self.structured_logging,
        )

        self._logger_configured = True

    def validate_device_options(self, command_name: str) -> bool:
        """Validate device-related options for commands that need them"""
        needs_device = command_name not in ["list-commands", "list"]

        if not needs_device:
            return True

        has_device = bool(self.device)
        has_all_devices = self.all_devices

        if not (has_device or has_all_devices):
            logger.error(
                "Either --device or --all-devices is required for command: %s",
                command_name,
            )
            return False

        if has_device and has_all_devices:
            logger.error("Cannot specify both --device and --all-devices")
            return False

        return True


class ServiceRegistry:
    """Registry for services used by commands"""

    def __init__(self):
        self._services = {}

    def register(self, name: str, service: Any):
        """Register a service"""
        self._services[name] = service

    def get(self, name: str) -> Any:
        """Get a registered service"""
        return self._services.get(name)

    def has(self, name: str) -> bool:
        """Check if a service is registered"""
        return name in self._services


# Global service registry instance
service_registry = ServiceRegistry()
