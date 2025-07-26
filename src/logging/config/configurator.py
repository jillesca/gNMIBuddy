#!/usr/bin/env python3
"""
Main logging configurator.

This module contains the LoggingConfigurator class which is responsible
for configuring the Python logging system based on the configuration
data structures.
"""

import logging
import sys
from typing import Dict, Optional

from ..core.models import LoggingConfiguration
from ..core.enums import LogLevel, SuppressionMode
from ..core.logger_names import LoggerNames
from ..core.formatter import OTelFormatter, HumanReadableFormatter
from .environment import EnvironmentConfigReader
from .file_utils import LogFilePathGenerator


class LoggingConfigurator:
    """
    Main logging system configurator.

    Handles the actual configuration of Python's logging system
    based on LoggingConfiguration data structures. Maintains state
    to avoid unnecessary reconfiguration.
    """

    _configured = False
    _current_config: Optional[LoggingConfiguration] = None
    _module_level_cache: Dict[str, LogLevel] = {}

    @classmethod
    def configure(
        cls,
        global_level: Optional[str] = None,
        module_levels: Optional[Dict[str, str]] = None,
        enable_structured: bool = False,
        enable_file_output: bool = True,
        log_file: Optional[str] = None,
        enable_external_suppression: bool = True,
        external_suppression_mode: str = "cli",
    ) -> logging.Logger:
        """
        Configure the logging system with the given parameters.

        Args:
            global_level: Global logging level (debug, info, warning, error)
            module_levels: Dict mapping module names to specific log levels
            enable_structured: Whether to use structured JSON logging
            enable_file_output: Whether to log to file
            log_file: Custom log file path
            enable_external_suppression: Whether to suppress external library noise
            external_suppression_mode: Type of suppression ("cli", "mcp", "development")

        Returns:
            Configured root application logger

        Raises:
            ValueError: If configuration parameters are invalid
        """
        # Read environment configuration
        env_config = EnvironmentConfigReader.read_configuration()

        # Create complete configuration object
        try:
            config = LoggingConfiguration.from_environment_and_params(
                env_config=env_config,
                global_level=global_level,
                module_levels=module_levels,
                enable_structured=enable_structured,
                enable_file_output=enable_file_output,
                log_file=log_file,
                enable_external_suppression=enable_external_suppression,
                external_suppression_mode=external_suppression_mode,
            )
        except ValueError as e:
            raise ValueError(f"Invalid logging configuration: {e}") from e

        # Check if reconfiguration is needed
        if (
            cls._configured
            and cls._current_config
            and config.equals_for_caching(cls._current_config)
        ):
            return logging.getLogger(LoggerNames.APP_ROOT)

        # Apply the configuration
        cls._apply_configuration(config)
        cls._current_config = config
        cls._configured = True

        # Get and log initial message
        app_logger = logging.getLogger(LoggerNames.APP_ROOT)
        log_file_info = str(config.log_file) if config.log_file else "disabled"

        app_logger.debug(
            "Logging configured with file: %s",
            log_file_info,
            extra={
                "global_level": config.global_level.to_string(),
                "structured": config.enable_structured,
                "file_output": config.enable_file_output,
                "suppression_mode": config.external_suppression_mode.to_string(),
            },
        )

        return app_logger

    @classmethod
    def _apply_configuration(cls, config: LoggingConfiguration) -> None:
        """Apply the logging configuration to Python's logging system."""
        # Setup external suppression first (if enabled)
        if config.enable_external_suppression:
            cls._setup_external_suppression(config)

        # Clear any existing configuration
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Create and configure handlers
        handlers = cls._create_handlers(config)

        # Configure root logger
        root_logger.setLevel(LogLevel.DEBUG)  # Let handlers filter
        for handler in handlers:
            root_logger.addHandler(handler)

        # Set module-specific levels
        cls._apply_module_levels(config.module_levels)

    @classmethod
    def _create_handlers(
        cls, config: LoggingConfiguration
    ) -> list[logging.Handler]:
        """Create logging handlers based on configuration."""
        handlers = []

        # Choose formatter
        if config.enable_structured:
            formatter = OTelFormatter()
        else:
            formatter = HumanReadableFormatter()

        # Console handler
        console_handler = cls._create_console_handler(config, formatter)
        handlers.append(console_handler)

        # File handler (if enabled)
        if config.enable_file_output:
            file_handler = cls._create_file_handler(config, formatter)
            handlers.append(file_handler)

        return handlers

    @classmethod
    def _create_console_handler(
        cls, config: LoggingConfiguration, formatter: logging.Formatter
    ) -> logging.StreamHandler:
        """Create console handler with appropriate stream based on mode."""
        # For MCP servers, use stderr to keep stdout clean for protocol
        if config.external_suppression_mode == SuppressionMode.MCP:
            console_handler = logging.StreamHandler(sys.stderr)
        else:
            console_handler = logging.StreamHandler(sys.stdout)

        console_handler.setFormatter(formatter)
        console_handler.setLevel(config.global_level)
        return console_handler

    @classmethod
    def _create_file_handler(
        cls, config: LoggingConfiguration, formatter: logging.Formatter
    ) -> logging.FileHandler:
        """Create file handler with appropriate log file path."""
        if config.log_file:
            log_file_path = config.log_file
        else:
            # Generate sequential log file name
            log_file_path = LogFilePathGenerator.get_next_log_file_path()

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(LogLevel.DEBUG)  # File gets everything
        return file_handler

    @classmethod
    def _setup_external_suppression(cls, config: LoggingConfiguration) -> None:
        """Setup external library suppression based on configuration."""
        from ..suppression.strategies import get_suppression_strategy

        strategy = get_suppression_strategy(config.external_suppression_mode)
        strategy.apply_suppression(config.module_levels)

    @classmethod
    def _apply_module_levels(cls, module_config) -> None:
        """Apply module-specific log levels."""
        cls._module_level_cache.clear()

        for module_name, level in module_config.levels.items():
            cls._module_level_cache[module_name] = level
            logger = logging.getLogger(module_name)
            logger.setLevel(level)

    @classmethod
    def set_module_level(cls, module_name: str, level) -> None:
        """
        Dynamically change the log level for a specific module.

        Args:
            module_name: Name of the module logger
            level: New log level (string or LogLevel enum or int)
        """
        # Convert to LogLevel if needed
        if isinstance(level, str):
            level = LogLevel.from_string(level)
        elif isinstance(level, int):
            level = LogLevel(level)

        # Update cache and logger
        cls._module_level_cache[module_name] = level
        logger = logging.getLogger(module_name)
        logger.setLevel(level)

    @classmethod
    def get_module_levels(cls) -> Dict[str, str]:
        """
        Get current module-specific log levels.

        Returns:
            Dictionary mapping module names to level strings
        """
        return {
            module: level.to_string()
            for module, level in cls._module_level_cache.items()
        }

    @classmethod
    def get_current_configuration(cls) -> Optional[LoggingConfiguration]:
        """Get the current logging configuration."""
        return cls._current_config

    @classmethod
    def is_configured(cls) -> bool:
        """Check if logging has been configured."""
        return cls._configured

    @classmethod
    def reset_configuration(cls) -> None:
        """Reset configuration state (useful for testing)."""
        cls._configured = False
        cls._current_config = None
        cls._module_level_cache.clear()
