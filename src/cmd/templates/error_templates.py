#!/usr/bin/env python3
"""Error message templates for CLI with OOP organization"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class TemplateData:
    """Base class for template data"""

    pass


@dataclass
class UnexpectedArgumentData(TemplateData):
    """Data for unexpected argument error template"""

    unexpected_arg: str
    command: str
    group: str = ""

    @property
    def full_command(self) -> str:
        """Get full command string"""
        if self.group:
            return f"{self.group} {self.command}"
        return self.command


@dataclass
class MissingOptionData(TemplateData):
    """Data for missing option error template"""

    option: str
    command: str
    group: str = ""


@dataclass
class InvalidChoiceData(TemplateData):
    """Data for invalid choice error template"""

    option: str
    value: str
    choices: list
    command: str = ""


@dataclass
class DeviceNotFoundData(TemplateData):
    """Data for device not found error template"""

    device: str
    suggestions: Optional[List[str]] = None
    available_devices: Optional[List[str]] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.available_devices is None:
            self.available_devices = []


@dataclass
class InventoryErrorData(TemplateData):
    """Data for inventory error template"""

    inventory_example: str = ""
    env_example: str = ""


class ErrorTemplates:
    """Centralized error message templates using OOP principles"""

    # Base template for unexpected arguments (consolidated from the three similar ones)
    UNEXPECTED_ARGUMENT_TEMPLATE = """❌ Command Error
═══════════════════════════════════════════════════════════

Unexpected argument: '{unexpected_arg}'

💡 How to fix this:
{fix_instructions}

📝 The device name must be specified with the --device flag.

📖 Examples:
{examples}"""

    # Consolidated fix instruction template (replaces the three separate ones)
    UNEXPECTED_ARGUMENT_FIX_TEMPLATE = """  Use: gnmibuddy {full_command} --device {arg}
  Not: gnmibuddy {full_command} {arg}"""

    GENERIC_UNEXPECTED_ARGUMENT_FIX_TEMPLATE = """  The command '{command}' doesn't accept positional arguments.
  Try using an option like --device {arg}"""

    UNKNOWN_COMMAND_TEMPLATE = """Error: Unknown command '{command}'"""

    MISSING_DEVICE_OPTION_TEMPLATE = """Error: Missing required option '{option}' for command '{command}'

The --device option specifies which device to query.
{examples}

To see available devices, run:
  uv run gnmibuddy.py device list"""

    MISSING_INTERFACE_OPTION_TEMPLATE = """Error: Missing required option '{option}' for command '{command}'

The --name option specifies the interface name.
{examples}"""

    MISSING_OPTION_GENERIC_TEMPLATE = """Error: Missing required option '{option}' for command '{command}'

Run 'uv run gnmibuddy.py ... {command} --help' for usage information."""

    INVALID_CHOICE_TEMPLATE = """Error: Invalid value '{value}' for option '{option}'

Valid choices for {option}:
  {choices}"""

    DEVICE_NOT_FOUND_TEMPLATE = """Error: Device '{device}' not found in inventory

Available devices:
{available_devices}"""

    DEVICE_NOT_FOUND_NO_DEVICES_TEMPLATE = """Error: Device '{device}' not found in inventory

No devices found in inventory.
Check your inventory file or use --inventory to specify the path."""

    INVALID_OPTION_VALUE_TEMPLATE = """❌ Invalid Option Value
═══════════════════════════════════════════════════════════

Invalid value '{invalid_value}' for option '{option_name}'

💡 Run the command with --help to see valid options."""

    COMMAND_NO_ARGUMENTS_TEMPLATE = """❌ Command Error
═══════════════════════════════════════════════════════════

The command '{command_name}' doesn't accept arguments.

💡 How to fix this:
  Use: gnmibuddy {full_command}

📖 If you need to specify options, use flags like --device, --output, etc."""

    @classmethod
    def format_unexpected_argument_error(
        cls, data: UnexpectedArgumentData, examples: str = ""
    ) -> str:
        """Format unexpected argument error with consolidated template"""

        # Generate fix instructions using the consolidated template
        if data.group and data.command:
            fix_instructions = cls.UNEXPECTED_ARGUMENT_FIX_TEMPLATE.format(
                full_command=data.full_command, arg=data.unexpected_arg
            )
        else:
            fix_instructions = (
                cls.GENERIC_UNEXPECTED_ARGUMENT_FIX_TEMPLATE.format(
                    command=data.command, arg=data.unexpected_arg
                )
            )

        # Use provided examples or generate fallback
        if not examples:
            examples = f"  uv run gnmibuddy.py {data.full_command} --device R1"

        return cls.UNEXPECTED_ARGUMENT_TEMPLATE.format(
            unexpected_arg=data.unexpected_arg,
            fix_instructions=fix_instructions,
            examples=examples,
        )

    @classmethod
    def format_missing_option_error(
        cls, data: MissingOptionData, examples: str = ""
    ) -> str:
        """Format missing option error"""
        if data.option == "--device":
            return cls.MISSING_DEVICE_OPTION_TEMPLATE.format(
                option=data.option,
                command=data.command,
                examples=examples
                or "Use: gnmibuddy <group> <command> --device <device_name>",
            )
        elif data.option == "--name":
            return cls.MISSING_INTERFACE_OPTION_TEMPLATE.format(
                option=data.option,
                command=data.command,
                examples=examples
                or "Use: gnmibuddy network interface --device R1 --name GigE0/0/0/1",
            )
        else:
            return cls.MISSING_OPTION_GENERIC_TEMPLATE.format(
                option=data.option, command=data.command
            )

    @classmethod
    def format_invalid_choice_error(
        cls, data: InvalidChoiceData, suggestions: Optional[List[str]] = None
    ) -> str:
        """Format invalid choice error"""
        choices_text = ", ".join(data.choices)

        return cls.INVALID_CHOICE_TEMPLATE.format(
            value=data.value,
            option=data.option,
            choices=choices_text,
        )

    @classmethod
    def format_device_not_found_error(cls, data: DeviceNotFoundData) -> str:
        """Format device not found error"""
        if not data.available_devices:
            return cls.DEVICE_NOT_FOUND_NO_DEVICES_TEMPLATE.format(
                device=data.device
            )

        available_devices_text = "\n".join(
            f"  {d}" for d in data.available_devices[:10]
        )

        if len(data.available_devices) > 10:
            available_devices_text += (
                f"\n  ... and {len(data.available_devices) - 10} more"
            )

        return cls.DEVICE_NOT_FOUND_TEMPLATE.format(
            device=data.device,
            available_devices=available_devices_text,
        )

    @classmethod
    def format_unknown_command_error(cls, command: str) -> str:
        """Format unknown command error"""

        return cls.UNKNOWN_COMMAND_TEMPLATE.format(command=command)
