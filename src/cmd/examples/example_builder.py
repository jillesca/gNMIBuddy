#!/usr/bin/env python3
"""Object-oriented example builder system for CLI commands.

This module provides a clean, fluent interface for building and managing
CLI command examples with intelligent formatting and categorization.

Public API:
    - ExampleType: Enum for categorizing examples
    - Example: Dataclass representing a single example
    - ExampleSet: Main class for managing collections of examples
    - ExampleBuilder: Factory class for common example patterns

Usage:
    >>> examples = ExampleSet("device_info")
    >>> examples.add_basic("gnmibuddy device info --device R1")
    >>> examples.add_advanced("gnmibuddy device info --device R1 --detail")
    >>> print(examples.for_help())
"""

from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Public API - explicitly define what should be imported with "from module import *"
__all__ = [
    "ExampleType",
    "Example",
    "ExampleSet",
    "ExampleBuilder",
    "CLI_RUNNER",  # Add the constant to public API
]

# Constants for common CLI patterns
CLI_RUNNER = "uv run gnmibuddy.py"
DEFAULT_DEVICE = "R1"
DEFAULT_OUTPUT_FORMATS = ["json", "yaml"]


class ExampleType(Enum):
    """Types of examples for categorization.

    Used to organize examples by their purpose and complexity level.
    """

    BASIC = "basic"
    ADVANCED = "advanced"
    ALIAS = "alias"
    BATCH = "batch"
    OUTPUT_FORMAT = "output_format"
    ERROR = "error"
    HELP = "help"
    # Error-specific types
    ERROR_MISSING_DEVICE = "error_missing_device"
    ERROR_UNEXPECTED_ARG = "error_unexpected_arg"
    ERROR_INVALID_CHOICE = "error_invalid_choice"
    ERROR_DEVICE_NOT_FOUND = "error_device_not_found"
    ERROR_INVENTORY_MISSING = "error_inventory_missing"


@dataclass
class Example:
    """Single example with metadata.

    Represents a single command example with associated metadata
    for categorization and display purposes.

    Args:
        command: The command string to execute
        description: Human-readable description of what the command does
        type: Category of the example (see ExampleType)
        tags: Additional tags for filtering and organization
    """

    command: str
    description: str = ""
    type: ExampleType = ExampleType.BASIC
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Return formatted example with optional description."""
        if self.description:
            return f"# {self.description}\n{self.command}"
        return self.command


class ExampleSet:
    """A collection of examples with intelligent combination and formatting capabilities.

    Provides a fluent interface for building, filtering, and formatting
    collections of command examples. Supports various output formats
    including help text and error messages.

    Args:
        name: Identifier for this example set
        description: Human-readable description of the example set
    """

    def __init__(self, name: str = "", description: str = "") -> None:
        self.name = name
        self.description = description
        self._examples: List[Example] = []

    # Public API - Core methods for building example sets

    def add(
        self,
        command: str,
        description: str = "",
        type: ExampleType = ExampleType.BASIC,
        tags: Optional[List[str]] = None,
    ) -> "ExampleSet":
        """Add a single example (fluent interface).

        Args:
            command: Command string to add
            description: Optional description for the command
            type: Category of the example
            tags: Optional tags for filtering

        Returns:
            Self for method chaining
        """
        self._examples.append(
            Example(
                command=command,
                description=description,
                type=type,
                tags=tags or [],
            )
        )
        return self

    def add_basic(self, command: str, description: str = "") -> "ExampleSet":
        """Add a basic usage example."""
        return self.add(command, description, ExampleType.BASIC)

    def add_advanced(
        self, command: str, description: str = ""
    ) -> "ExampleSet":
        """Add an advanced usage example."""
        return self.add(command, description, ExampleType.ADVANCED)

    def add_alias(self, command: str, description: str = "") -> "ExampleSet":
        """Add an alias example."""
        return self.add(command, description, ExampleType.ALIAS)

    def add_batch(self, command: str, description: str = "") -> "ExampleSet":
        """Add a batch operation example."""
        return self.add(command, description, ExampleType.BATCH)

    def add_output_format(
        self,
        command: str,
        description: str = "",
        available_formats: Optional[List[str]] = None,
    ) -> "ExampleSet":
        """Add an output format example following CLI best practices.

        Shows one example with the primary format and notes about available options.

        Args:
            command: Command with the primary format (e.g., "--output json")
            description: Optional description
            available_formats: List of all available formats (e.g., ["json", "yaml"])

        Returns:
            Self for method chaining
        """
        desc = self._build_format_description(description, available_formats)
        return self.add(command, desc, ExampleType.OUTPUT_FORMAT)

    # Error-specific methods
    def add_error_missing_device(
        self, command: str, description: str = ""
    ) -> "ExampleSet":
        """Add an example showing correct device usage for missing device errors."""
        return self.add(command, description, ExampleType.ERROR_MISSING_DEVICE)

    def add_error_unexpected_arg(
        self, command: str, description: str = ""
    ) -> "ExampleSet":
        """Add an example showing correct syntax for unexpected argument errors."""
        return self.add(command, description, ExampleType.ERROR_UNEXPECTED_ARG)

    def add_error_invalid_choice(
        self, command: str, description: str = ""
    ) -> "ExampleSet":
        """Add an example showing valid choices for invalid choice errors."""
        return self.add(command, description, ExampleType.ERROR_INVALID_CHOICE)

    def add_error_device_not_found(
        self, command: str, description: str = ""
    ) -> "ExampleSet":
        """Add an example for device not found errors."""
        return self.add(
            command, description, ExampleType.ERROR_DEVICE_NOT_FOUND
        )

    def add_error_inventory_missing(
        self, command: str, description: str = ""
    ) -> "ExampleSet":
        """Add an example for inventory missing errors."""
        return self.add(
            command, description, ExampleType.ERROR_INVENTORY_MISSING
        )

    def add_section(self, title: str, examples: List[str]) -> "ExampleSet":
        """Add a section of examples with a title.

        Args:
            title: Section title to display
            examples: List of command strings to add under this section

        Returns:
            Self for method chaining
        """
        if title:
            self.add(
                "", title, ExampleType.HELP
            )  # Use empty command for section headers
        for example in examples:
            if example.strip():  # Skip empty lines
                self.add(example)
        return self

    # Public API - Filtering and transformation methods

    def filter_by_type(self, *types: ExampleType) -> "ExampleSet":
        """Create a new ExampleSet with only specified types.

        Args:
            *types: ExampleType values to include

        Returns:
            New ExampleSet with filtered examples
        """
        filtered = ExampleSet(f"{self.name}_filtered", self.description)
        for example in self._examples:
            if example.type in types:
                filtered._examples.append(example)
        return filtered

    def filter_by_tags(self, *tags: str) -> "ExampleSet":
        """Create a new ExampleSet with examples matching any of the specified tags.

        Args:
            *tags: Tag strings to match

        Returns:
            New ExampleSet with filtered examples
        """
        filtered = ExampleSet(f"{self.name}_tagged", self.description)
        for example in self._examples:
            if any(tag in example.tags for tag in tags):
                filtered._examples.append(example)
        return filtered

    def basic_only(self) -> "ExampleSet":
        """Get only basic examples."""
        return self.filter_by_type(ExampleType.BASIC)

    def advanced_only(self) -> "ExampleSet":
        """Get only advanced examples."""
        return self.filter_by_type(ExampleType.ADVANCED)

    def error_examples_only(self) -> "ExampleSet":
        """Get only error-related examples."""
        return self.filter_by_type(
            ExampleType.ERROR,
            ExampleType.ERROR_MISSING_DEVICE,
            ExampleType.ERROR_UNEXPECTED_ARG,
            ExampleType.ERROR_INVALID_CHOICE,
            ExampleType.ERROR_DEVICE_NOT_FOUND,
            ExampleType.ERROR_INVENTORY_MISSING,
        )

    def missing_device_errors(self) -> "ExampleSet":
        """Get examples for missing device errors."""
        return self.filter_by_type(ExampleType.ERROR_MISSING_DEVICE)

    def unexpected_arg_errors(self) -> "ExampleSet":
        """Get examples for unexpected argument errors."""
        return self.filter_by_type(ExampleType.ERROR_UNEXPECTED_ARG)

    def invalid_choice_errors(self) -> "ExampleSet":
        """Get examples for invalid choice errors."""
        return self.filter_by_type(ExampleType.ERROR_INVALID_CHOICE)

    def device_not_found_errors(self) -> "ExampleSet":
        """Get examples for device not found errors."""
        return self.filter_by_type(ExampleType.ERROR_DEVICE_NOT_FOUND)

    def inventory_missing_errors(self) -> "ExampleSet":
        """Get examples for inventory missing errors."""
        return self.filter_by_type(ExampleType.ERROR_INVENTORY_MISSING)

    def combine(
        self, *other_sets: "ExampleSet", separator: bool = True
    ) -> "ExampleSet":
        """Combine with other ExampleSets.

        Args:
            *other_sets: Other ExampleSet instances to combine
            separator: Whether to add empty line separators between sets

        Returns:
            New ExampleSet with combined examples
        """
        combined = ExampleSet(f"combined_{self.name}")
        combined._examples.extend(self._examples)

        for other_set in other_sets:
            if separator and combined._examples:
                combined.add("", "", ExampleType.HELP)  # Empty line separator
            combined._examples.extend(other_set._examples)

        return combined

    def limit(self, count: int) -> "ExampleSet":
        """Create a new ExampleSet with limited number of examples.

        Args:
            count: Maximum number of examples to include

        Returns:
            New ExampleSet with limited examples
        """
        limited = ExampleSet(f"{self.name}_limited", self.description)
        limited._examples = self._examples[:count]
        return limited

    # Public API - Output formatting methods

    def to_list(self, include_descriptions: bool = True) -> List[str]:
        """Convert to list format (compatible with existing system).

        Args:
            include_descriptions: Whether to include description comments

        Returns:
            List of formatted example strings
        """
        result = []
        current_section = None

        for example in self._examples:
            if example.type == ExampleType.HELP and not example.command:
                # Section header or separator
                if example.description:
                    clean_description = example.description.strip()
                    result.append(f"# {clean_description}")
                    current_section = clean_description
                else:
                    result.append("")  # Empty line separator
            else:
                if (
                    include_descriptions
                    and example.description
                    and example.description.strip() != current_section
                ):
                    clean_description = example.description.strip()
                    if clean_description:  # Only add non-empty descriptions
                        result.append(f"# {clean_description}")
                result.append(example.command)

        return result

    def to_string(
        self, separator: str = "\n", include_descriptions: bool = True
    ) -> str:
        """Convert to string format.

        Args:
            separator: String to use between examples
            include_descriptions: Whether to include description comments

        Returns:
            Formatted string representation
        """
        return separator.join(self.to_list(include_descriptions))

    def for_help(self, max_examples: Optional[int] = None) -> str:
        """Format for Click help text.

        Args:
            max_examples: Maximum number of examples to show

        Returns:
            Formatted help text with proper indentation
        """
        examples = self.limit(max_examples) if max_examples else self
        lines = ["\b", "Examples:"] + [
            "  " + line for line in examples.to_list()
        ]
        return "\n".join(lines)

    def for_error(self, prefix: str = "") -> str:
        """Format for error messages.

        Args:
            prefix: Optional prefix to add to each line

        Returns:
            Formatted error message text
        """
        lines = self.to_list()
        if prefix:
            lines = [prefix + line for line in lines]
        return "\n".join(lines)

    # Special methods for Python integration

    def __len__(self) -> int:
        """Return number of examples."""
        return len(self._examples)

    def __bool__(self) -> bool:
        """Return True if examples exist."""
        return len(self._examples) > 0

    def __iter__(self):
        """Iterate over formatted example strings."""
        return iter(self.to_list())

    # Private helper methods

    def _build_format_description(
        self, description: str, available_formats: Optional[List[str]]
    ) -> str:
        """Build description text for output format examples."""
        if available_formats and len(available_formats) > 1:
            formats_str = ", ".join(available_formats)
            return (
                f"{description} (available: {formats_str})"
                if description
                else f"Available formats: {formats_str}"
            )
        return description


class ExampleBuilder:
    """Factory class for building common example patterns.

    Provides static methods for creating commonly used example patterns
    to reduce code duplication and ensure consistency.
    """

    @staticmethod
    def command_examples(
        base_command: str, device: str = DEFAULT_DEVICE
    ) -> ExampleSet:
        """Build a standard command example set.

        Args:
            base_command: Base command string (e.g., "device info")
            device: Default device name to use in examples

        Returns:
            ExampleSet with basic command example
        """
        return ExampleSet(f"{base_command}_examples").add_basic(
            f"{CLI_RUNNER} {base_command} --device {device}"
        )

    @staticmethod
    def standard_command_examples(
        command: str,
        alias: str = "",
        device: str = DEFAULT_DEVICE,
        detail_option: bool = True,
        batch_operations: bool = True,
        output_formats: bool = True,
        alias_examples: bool = True,
        available_formats: Optional[List[str]] = None,
        custom_batch_commands: Optional[List[str]] = None,
    ) -> ExampleSet:
        """Build a complete set of examples following standard CLI patterns.

        This method generates all the common example patterns that most commands follow:
        - Basic usage with --device
        - Advanced usage with --detail (if supported)
        - Output format options (if supported)
        - Batch operations with --devices and --all-devices (if supported)
        - Alias examples (if alias provided)

        Args:
            command: The command string (e.g., "device info")
            alias: The alias version (e.g., "d info")
            device: Default device name for examples
            detail_option: Whether command supports --detail flag
            batch_operations: Whether command supports batch operations
            output_formats: Whether command supports --output flag
            alias_examples: Whether to include alias examples
            available_formats: List of supported output formats
            custom_batch_commands: Custom batch command patterns to use instead of defaults

        Returns:
            ExampleSet with all applicable standard examples
        """
        base = f"{CLI_RUNNER} {command}"
        alias_base = f"{CLI_RUNNER} {alias}" if alias else ""

        examples = ExampleSet(name=f"{command.replace(' ', '_')}_examples")

        # Basic usage (always included)
        examples.add_basic(command=f"{base} --device {device}")

        # Advanced options with --detail
        if detail_option:
            examples.add_advanced(
                command=f"{base} --device {device} --detail",
                description="Advanced options",
            )

        # Output format options
        if output_formats:
            formats = available_formats or DEFAULT_OUTPUT_FORMATS
            examples.add_output_format(
                command=f"{base} --device {device} --output {formats[0]}",
                description="Output format options",
                available_formats=formats,
            )

        # Batch operations
        if batch_operations:
            if custom_batch_commands:
                for batch_cmd in custom_batch_commands:
                    examples.add_batch(command=batch_cmd)
            else:
                examples.add_batch(
                    command=f"{base} --devices R1,R2,R3",
                    description="Batch operations",
                )
                examples.add_batch(command=f"{base} --all-devices")

        # Alias examples
        if alias_examples and alias_base:
            examples.add_alias(
                command=f"{alias_base} --device {device}",
                description="Using aliases",
            )

        return examples

    @staticmethod
    def network_command_examples(
        command: str,
        device: str = DEFAULT_DEVICE,
        detail_option: bool = True,
        batch_operations: bool = True,
        output_formats: bool = True,
    ) -> ExampleSet:
        """Build network command examples with common patterns.

        Convenience method specifically for network commands that automatically
        sets up the network/n alias pattern.

        Args:
            command: The network subcommand (e.g., "interface", "routing")
            device: Default device name for examples
            detail_option: Whether command supports --detail flag
            batch_operations: Whether command supports batch operations
            output_formats: Whether command supports --output flag

        Returns:
            ExampleSet with all applicable network command examples
        """
        return ExampleBuilder.standard_command_examples(
            command=f"network {command}",
            alias=f"n {command}",
            device=device,
            detail_option=detail_option,
            batch_operations=batch_operations,
            output_formats=output_formats,
            alias_examples=True,
        )

    @staticmethod
    def simple_command_examples(
        command: str, description: str = ""
    ) -> ExampleSet:
        """Build examples for commands that don't follow device patterns.

        For commands like 'device list' that don't require --device parameter.

        Args:
            command: The command string
            description: Optional description

        Returns:
            ExampleSet with basic command example
        """
        return ExampleSet(f"{command.replace(' ', '_')}_examples").add_basic(
            command=f"{CLI_RUNNER} {command}", description=description
        )

    # Error-specific factory methods
    @staticmethod
    def missing_device_error_examples(
        command: str, group: str = "", device: str = DEFAULT_DEVICE
    ) -> ExampleSet:
        """Build examples for missing --device option errors.

        Args:
            command: The command that failed (e.g., "info")
            group: The command group (e.g., "device")
            device: Default device name for examples

        Returns:
            ExampleSet with missing device error examples
        """
        full_command = f"{group} {command}" if group else command

        examples = ExampleSet(f"{command}_missing_device_errors")

        # Basic correct usage
        examples.add_error_missing_device(
            command=f"{CLI_RUNNER} {full_command} --device {device}",
            description="Correct usage with --device flag",
        )

        # Batch operation alternatives
        examples.add_error_missing_device(
            command=f"{CLI_RUNNER} {full_command} --all-devices",
            description="Or use batch operation",
        )

        return examples

    @staticmethod
    def unexpected_argument_error_examples(
        command: str, group: str = "", device: str = DEFAULT_DEVICE
    ) -> ExampleSet:
        """Build examples for unexpected argument errors.

        Args:
            command: The command that failed (e.g., "info")
            group: The command group (e.g., "device")
            device: Default device name for examples

        Returns:
            ExampleSet with unexpected argument error examples
        """
        full_command = f"{group} {command}" if group else command

        examples = ExampleSet(f"{command}_unexpected_arg_errors")

        # Show correct usage
        examples.add_error_unexpected_arg(
            command=f"{CLI_RUNNER} {full_command} --device {device}",
            description="Correct: use --device flag",
        )

        # Show wrong usage in comment
        examples.add(
            command=f"# Wrong: {CLI_RUNNER} {full_command} {device}",
            description="Common mistake to avoid",
            type=ExampleType.ERROR_UNEXPECTED_ARG,
        )

        return examples

    @staticmethod
    def device_not_found_error_examples(
        device: str = DEFAULT_DEVICE,
    ) -> ExampleSet:
        """Build examples for device not found errors.

        Args:
            device: The device that was not found

        Returns:
            ExampleSet with device not found error examples
        """
        examples = ExampleSet("device_not_found_errors")

        # Check available devices
        examples.add_error_device_not_found(
            command=f"{CLI_RUNNER} device list",
            description="Check available devices",
        )

        # Use exact device name
        examples.add_error_device_not_found(
            command=f"{CLI_RUNNER} device info --device <exact_name>",
            description="Use exact device name from inventory",
        )

        return examples

    @staticmethod
    def inventory_missing_error_examples() -> ExampleSet:
        """Build examples for inventory missing errors.

        Returns:
            ExampleSet with inventory missing error examples
        """
        examples = ExampleSet("inventory_missing_errors")

        # Use --inventory option
        examples.add_error_inventory_missing(
            command=f"{CLI_RUNNER} --inventory path/to/devices.json device list",
            description="Use --inventory option",
        )

        # Set environment variable
        examples.add_error_inventory_missing(
            command="export NETWORK_INVENTORY=path/to/devices.json",
            description="Or set environment variable",
        )

        return examples

    @staticmethod
    def invalid_choice_error_examples(
        option: str, valid_choices: List[str], command: str = "command"
    ) -> ExampleSet:
        """Build examples for invalid choice errors.

        Args:
            option: The option that had an invalid choice (e.g., "--output")
            valid_choices: List of valid choices
            command: The command context

        Returns:
            ExampleSet with invalid choice error examples
        """
        examples = ExampleSet(f"{option}_invalid_choice_errors")

        for choice in valid_choices[:3]:  # Show first 3 valid choices
            examples.add_error_invalid_choice(
                command=f"{CLI_RUNNER} {command} {option} {choice}",
                description=f"Valid choice: {choice}",
            )

        if len(valid_choices) > 3:
            examples.add_error_invalid_choice(
                command=f"# Other valid choices: {', '.join(valid_choices[3:])}",
                description="Additional options available",
            )

        return examples
