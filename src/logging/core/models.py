#!/usr/bin/env python3
"""
Data models for logging configuration.

This module defines data classes that encapsulate logging configuration
instead of using dictionaries, following OOP principles for better
type safety and data encapsulation.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from pathlib import Path

from .enums import LogLevel, SuppressionMode


@dataclass(frozen=True)
class ModuleLevelConfiguration:
    """
    Configuration for module-specific log levels.

    Encapsulates the mapping of module names to their specific log levels,
    replacing the plain dictionary approach with a proper data structure.
    """

    levels: Dict[str, LogLevel] = field(default_factory=dict)

    @classmethod
    def from_string_dict(
        cls, string_levels: Dict[str, str]
    ) -> "ModuleLevelConfiguration":
        """
        Create configuration from string dictionary.

        Args:
            string_levels: Dictionary mapping module names to level strings

        Returns:
            ModuleLevelConfiguration with parsed LogLevel enums

        Raises:
            ValueError: If any level string is invalid
        """
        parsed_levels = {}
        for module_name, level_str in string_levels.items():
            try:
                parsed_levels[module_name] = LogLevel.from_string(level_str)
            except ValueError as e:
                raise ValueError(
                    f"Invalid log level for module '{module_name}': {e}"
                ) from e

        return cls(levels=parsed_levels)

    def to_string_dict(self) -> Dict[str, str]:
        """Convert to dictionary with string level values."""
        return {
            module: level.to_string() for module, level in self.levels.items()
        }

    def get_level_for_module(self, module_name: str) -> Optional[LogLevel]:
        """Get log level for a specific module."""
        return self.levels.get(module_name)

    def merge_with(
        self, other: "ModuleLevelConfiguration"
    ) -> "ModuleLevelConfiguration":
        """
        Merge with another configuration, with other taking precedence.

        Args:
            other: Configuration to merge with (takes precedence)

        Returns:
            New merged configuration
        """
        merged_levels = self.levels.copy()
        merged_levels.update(other.levels)
        return ModuleLevelConfiguration(levels=merged_levels)


@dataclass
class LoggingConfiguration:
    """
    Complete logging configuration data structure.

    Encapsulates all logging configuration parameters in a single,
    well-typed data structure that replaces scattered parameters
    and dictionary-based configuration.
    """

    # Core configuration
    global_level: LogLevel = LogLevel.INFO
    module_levels: ModuleLevelConfiguration = field(
        default_factory=ModuleLevelConfiguration
    )

    # Output configuration
    enable_structured: bool = False
    enable_file_output: bool = True
    log_file: Optional[Path] = None

    # External library suppression
    enable_external_suppression: bool = True
    external_suppression_mode: SuppressionMode = SuppressionMode.CLI

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.log_file is not None:
            self.log_file = Path(self.log_file)

    @classmethod
    def from_environment_and_params(
        cls,
        env_config: Dict[str, Any],
        global_level: Optional[str] = None,
        module_levels: Optional[Dict[str, str]] = None,
        enable_structured: bool = False,
        enable_file_output: bool = True,
        log_file: Optional[str] = None,
        enable_external_suppression: bool = True,
        external_suppression_mode: str = "cli",
    ) -> "LoggingConfiguration":
        """
        Create configuration from environment variables and parameters.

        Args:
            env_config: Environment configuration dictionary
            **kwargs: Explicit parameters that override environment

        Returns:
            Complete logging configuration

        Raises:
            ValueError: If any configuration value is invalid
        """
        # Use environment as defaults, explicit params override
        resolved_global_level = global_level or env_config.get(
            "global_level", "info"
        )
        resolved_enable_structured = enable_structured or env_config.get(
            "enable_structured", False
        )
        resolved_log_file = log_file or env_config.get("log_file")
        resolved_suppression_mode = (
            external_suppression_mode
            or env_config.get("external_suppression_mode", "cli")
        )

        # Merge module levels: environment first, then explicit
        env_module_levels = env_config.get("module_levels", {})
        merged_module_levels = env_module_levels.copy()
        if module_levels:
            merged_module_levels.update(module_levels)

        # Parse and validate
        try:
            parsed_global_level = LogLevel.from_string(resolved_global_level)
            parsed_module_config = ModuleLevelConfiguration.from_string_dict(
                merged_module_levels
            )
            parsed_suppression_mode = SuppressionMode.from_string(
                resolved_suppression_mode
            )
        except ValueError as e:
            raise ValueError(f"Invalid logging configuration: {e}") from e

        return cls(
            global_level=parsed_global_level,
            module_levels=parsed_module_config,
            enable_structured=resolved_enable_structured,
            enable_file_output=enable_file_output,
            log_file=Path(resolved_log_file) if resolved_log_file else None,
            enable_external_suppression=enable_external_suppression,
            external_suppression_mode=parsed_suppression_mode,
        )

    def equals_for_caching(self, other: "LoggingConfiguration") -> bool:
        """
        Check if configurations are equal for caching purposes.

        Used to determine if logging needs to be reconfigured.
        """
        if not isinstance(other, LoggingConfiguration):
            return False

        return (
            self.global_level == other.global_level
            and self.module_levels.levels == other.module_levels.levels
            and self.enable_structured == other.enable_structured
            and self.enable_file_output == other.enable_file_output
            and self.log_file == other.log_file
            and self.enable_external_suppression
            == other.enable_external_suppression
            and self.external_suppression_mode
            == other.external_suppression_mode
        )
