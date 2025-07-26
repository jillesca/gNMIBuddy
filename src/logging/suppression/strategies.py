#!/usr/bin/env python3
"""
External library suppression strategies.

This module provides different suppression strategies for various runtime
contexts (CLI, MCP, development), following the Strategy pattern.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..core.enums import SuppressionMode, LogLevel
from ..core.models import ModuleLevelConfiguration
from .external import ExternalLibrarySuppressor, SuppressionConfiguration


class SuppressionStrategy(ABC):
    """
    Abstract base class for suppression strategies.

    Follows the Strategy pattern to encapsulate different approaches
    to external library suppression based on runtime context.
    """

    @abstractmethod
    def apply_suppression(
        self, module_config: ModuleLevelConfiguration
    ) -> None:
        """
        Apply suppression strategy.

        Args:
            module_config: Module-specific configuration that may override defaults
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this strategy."""
        pass


class CLISuppressionStrategy(SuppressionStrategy):
    """
    Suppression strategy optimized for CLI usage.

    CLI tools need readable output, so this uses moderate suppression
    that still allows important warnings through.
    """

    def apply_suppression(
        self, module_config: ModuleLevelConfiguration
    ) -> None:
        """Apply CLI-optimized suppression."""
        # Create CLI-specific configuration
        cli_levels = {
            "pygnmi": LogLevel.WARNING,
            "grpc": LogLevel.WARNING,
            "urllib3": LogLevel.WARNING,
            "asyncio": LogLevel.WARNING,
            "requests": LogLevel.WARNING,
            "paramiko": LogLevel.WARNING,
        }

        # Override with any custom levels from module config
        self._apply_custom_overrides(cli_levels, module_config)

        # Create and apply suppression configuration
        config = SuppressionConfiguration(
            library_levels=cli_levels,
            environment_variables={},  # Less aggressive for CLI
        )

        ExternalLibrarySuppressor.apply_suppression(config)

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "CLI"

    def _apply_custom_overrides(
        self, default_levels: dict, module_config: ModuleLevelConfiguration
    ) -> None:
        """Apply custom module-level overrides to default levels."""
        for module_name, custom_level in module_config.levels.items():
            if module_name in default_levels:
                default_levels[module_name] = custom_level


class MCPSuppressionStrategy(SuppressionStrategy):
    """
    Suppression strategy optimized for MCP servers.

    MCP servers need clean stdout for JSON protocol, so this applies
    the most aggressive suppression available.
    """

    def apply_suppression(
        self, module_config: ModuleLevelConfiguration
    ) -> None:
        """Apply MCP-optimized suppression."""
        # Create aggressive MCP configuration
        mcp_levels = {
            "pygnmi": LogLevel.ERROR,
            "grpc": LogLevel.ERROR,
            "urllib3": LogLevel.ERROR,
            "asyncio": LogLevel.ERROR,
            "requests": LogLevel.ERROR,
            "paramiko": LogLevel.ERROR,
        }

        # Override with any custom levels from module config
        self._apply_custom_overrides(mcp_levels, module_config)

        # Create and apply suppression configuration with environment vars
        config = SuppressionConfiguration.create_default()
        config = SuppressionConfiguration(
            library_levels=mcp_levels,
            environment_variables=config.environment_variables,  # Use full env suppression
        )

        ExternalLibrarySuppressor.apply_suppression(config)

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "MCP"

    def _apply_custom_overrides(
        self, default_levels: dict, module_config: ModuleLevelConfiguration
    ) -> None:
        """Apply custom module-level overrides to default levels."""
        for module_name, custom_level in module_config.levels.items():
            if module_name in default_levels:
                default_levels[module_name] = custom_level


class DevelopmentSuppressionStrategy(SuppressionStrategy):
    """
    Suppression strategy for development/debugging.

    Allows more verbose logging from external libraries for debugging
    while still reducing the most problematic noise.
    """

    def apply_suppression(
        self, module_config: ModuleLevelConfiguration
    ) -> None:
        """Apply development-friendly suppression."""
        # Create minimal suppression for development
        dev_levels = {
            "pygnmi": LogLevel.INFO,  # More verbose for debugging
            "grpc": LogLevel.WARNING,  # Some gRPC info might be useful
            "urllib3": LogLevel.WARNING,
            "asyncio": LogLevel.WARNING,
            "requests": LogLevel.WARNING,
            "paramiko": LogLevel.WARNING,
        }

        # Override with any custom levels from module config
        self._apply_custom_overrides(dev_levels, module_config)

        # Create minimal suppression configuration
        config = SuppressionConfiguration(
            library_levels=dev_levels,
            environment_variables={},  # No environment suppression for development
        )

        # Don't apply deep suppression for development
        ExternalLibrarySuppressor._setup_python_logging_suppression(dev_levels)

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "Development"

    def _apply_custom_overrides(
        self, default_levels: dict, module_config: ModuleLevelConfiguration
    ) -> None:
        """Apply custom module-level overrides to default levels."""
        for module_name, custom_level in module_config.levels.items():
            if module_name in default_levels:
                default_levels[module_name] = custom_level


# Strategy registry
_STRATEGIES = {
    SuppressionMode.CLI: CLISuppressionStrategy(),
    SuppressionMode.MCP: MCPSuppressionStrategy(),
    SuppressionMode.DEVELOPMENT: DevelopmentSuppressionStrategy(),
}


def get_suppression_strategy(mode: SuppressionMode) -> SuppressionStrategy:
    """
    Get the appropriate suppression strategy for a given mode.

    Args:
        mode: Suppression mode enum

    Returns:
        Strategy instance for the requested mode

    Raises:
        ValueError: If mode is not supported
    """
    if mode not in _STRATEGIES:
        valid_modes = ", ".join(m.to_string() for m in _STRATEGIES.keys())
        raise ValueError(
            f"Unsupported suppression mode: {mode}. Valid modes: {valid_modes}"
        )

    return _STRATEGIES[mode]


# Convenience functions for backward compatibility
def setup_cli_suppression(
    module_config: Optional[ModuleLevelConfiguration] = None,
) -> None:
    """Setup suppression optimized for CLI usage."""
    if module_config is None:
        module_config = ModuleLevelConfiguration()

    strategy = get_suppression_strategy(SuppressionMode.CLI)
    strategy.apply_suppression(module_config)


def setup_mcp_suppression(
    module_config: Optional[ModuleLevelConfiguration] = None,
) -> None:
    """Setup suppression optimized for MCP servers."""
    if module_config is None:
        module_config = ModuleLevelConfiguration()

    strategy = get_suppression_strategy(SuppressionMode.MCP)
    strategy.apply_suppression(module_config)


def setup_development_suppression(
    module_config: Optional[ModuleLevelConfiguration] = None,
) -> None:
    """Setup suppression for development/debugging."""
    if module_config is None:
        module_config = ModuleLevelConfiguration()

    strategy = get_suppression_strategy(SuppressionMode.DEVELOPMENT)
    strategy.apply_suppression(module_config)
