#!/usr/bin/env python3
"""Error handling logic with contextual error messages"""

from typing import List
import difflib
from src.cmd.schemas import CommandGroup
from src.cmd.schemas.commands import command_registry
from src.cmd.templates.error_templates import ErrorTemplates
from src.logging.config import get_logger

logger = get_logger(__name__)


class CLIErrorHandler:
    """Centralized error handling with intelligent suggestions and examples"""

    def __init__(self):
        self.command_registry = command_registry

    def handle_unknown_command(
        self, command: str, context: str = "root"
    ) -> str:
        """Handle unknown command errors with context-aware suggestions

        Args:
            command: The unknown command that was entered
            context: The context where the error occurred ("root" or group name)

        Returns:
            Formatted error message with suggestions
        """
        if context == "root":
            # Unknown group at root level
            all_groups = CommandGroup.get_all_names_and_aliases()
            suggestions = self._find_similar_items(command, all_groups)

            return ErrorTemplates.format_unknown_command_error(
                command=command,
                context="root",
                suggestions=suggestions,
            )
        else:
            # Unknown command within a group
            group_commands = self._get_group_commands(context)
            suggestions = self._find_similar_items(command, group_commands)

            return ErrorTemplates.format_unknown_command_error(
                command=command,
                context=context,
                suggestions=suggestions,
                group_commands=group_commands,
            )

    def handle_unexpected_argument(
        self,
        unexpected_arg: str,
        command_name: str,
        group_name: str = "",
        examples: str = "",
    ) -> str:
        """Handle unexpected argument errors with contextual examples

        Args:
            unexpected_arg: The unexpected argument
            command_name: Name of the command
            group_name: Name of the command group
            examples: Additional examples to show

        Returns:
            Formatted error message
        """
        # Try to get examples from command's error provider
        if not examples:
            examples = self._get_examples_for_error(
                "unexpected_argument",
                command_name=command_name,
                group_name=group_name,
                unexpected_arg=unexpected_arg,
            )

        from src.cmd.templates.error_templates import (
            UnexpectedArgumentData,
        )

        data = UnexpectedArgumentData(
            unexpected_arg=unexpected_arg,
            command=command_name,
            group=group_name,
        )

        return ErrorTemplates.format_unexpected_argument_error(
            data=data, examples=examples
        )

    def handle_missing_option(
        self, command: str, option: str, group_name: str = ""
    ) -> str:
        """Handle missing required option errors

        Args:
            command: The command name
            option: The missing option
            group_name: The command group name

        Returns:
            Formatted error message
        """
        # Get examples from command's error provider
        examples = self._get_examples_for_error(
            "missing_option",
            command_name=command,
            group_name=group_name,
            option=option,
        )

        from src.cmd.templates.error_templates import MissingOptionData

        data = MissingOptionData(
            option=option, command=command, group=group_name
        )

        return ErrorTemplates.format_missing_option_error(
            data=data, examples=examples
        )

    def handle_invalid_choice(
        self, option: str, value: str, choices: List[str]
    ) -> str:
        """Handle invalid choice errors with suggestions

        Args:
            option: The option name
            value: The invalid value
            choices: List of valid choices

        Returns:
            Formatted error message
        """
        suggestions = self._find_similar_items(value, choices)

        from src.cmd.templates.error_templates import InvalidChoiceData

        data = InvalidChoiceData(option=option, value=value, choices=choices)

        return ErrorTemplates.format_invalid_choice_error(
            data=data, suggestions=suggestions
        )

    def handle_device_not_found(self, device: str) -> str:
        """Handle device not found errors

        Args:
            device: The device name that was not found

        Returns:
            Formatted error message
        """
        # This would need to be implemented with actual device inventory
        # For now, provide a basic error message
        from src.cmd.templates.error_templates import DeviceNotFoundData

        data = DeviceNotFoundData(device=device)

        return ErrorTemplates.format_device_not_found_error(data=data)

    def _find_similar_items(
        self, target: str, candidates: List[str], cutoff: float = 0.6
    ) -> List[str]:
        """Find similar items using fuzzy matching

        Args:
            target: The target string to match
            candidates: List of candidate strings
            cutoff: Similarity cutoff threshold

        Returns:
            List of similar items
        """
        if not candidates:
            return []

        # Use difflib for fuzzy matching
        matches = difflib.get_close_matches(
            target, candidates, n=3, cutoff=cutoff
        )

        # If no close matches, try a lower cutoff
        if not matches and cutoff > 0.3:
            matches = difflib.get_close_matches(
                target, candidates, n=3, cutoff=0.3
            )

        return matches

    def _get_group_commands(self, group_name: str) -> List[str]:
        """Get command names for a group

        Args:
            group_name: Name of the group

        Returns:
            List of command names in the group
        """
        # Resolve group alias to full name if needed
        group_enum = CommandGroup.resolve_name_or_alias(group_name)
        if not group_enum:
            return []

        commands = self.command_registry.get_commands_for_group(
            group_enum.group_name
        )
        return [cmd.name for cmd in commands]

    def _get_examples_for_error(
        self,
        error_type: str,
        command_name: str = "",
        group_name: str = "",
        **kwargs,
    ) -> str:
        """Get examples for error from command's error provider

        Args:
            error_type: Type of error
            command_name: Name of the command
            group_name: Name of the command group
            **kwargs: Additional context for the error

        Returns:
            Example text or empty string if not found
        """
        try:
            # Try to get examples from command module's error provider
            if command_name and group_name:
                examples = self._get_examples_from_command_provider(
                    command_name, group_name, error_type, **kwargs
                )
                if examples:
                    return examples.for_error()

        except Exception as e:
            logger.debug(
                "Error getting examples for %s.%s error %s: %s",
                group_name,
                command_name,
                error_type,
                e,
            )

        return ""

    def _get_examples_from_command_provider(
        self, command_name: str, group_name: str, error_type: str, **kwargs
    ):
        """Get examples from command's error provider using duck typing

        Args:
            command_name: Name of the command
            group_name: Name of the command group
            error_type: Type of error
            **kwargs: Additional context

        Returns:
            ExampleSet or None if not found
        """
        try:
            # Resolve group alias to full name
            group_enum = CommandGroup.resolve_name_or_alias(group_name)
            if not group_enum:
                return None

            actual_group_name = group_enum.group_name

            # Try to import the command module
            import importlib

            module_name = f"src.cmd.commands.{actual_group_name}.{command_name.replace('-', '_')}"
            command_module = importlib.import_module(module_name)

            # Look for error provider
            if hasattr(command_module, "error_provider"):
                error_provider = getattr(command_module, "error_provider")
                if hasattr(error_provider, "get_examples_for_error_type"):
                    get_examples_func = getattr(
                        error_provider, "get_examples_for_error_type"
                    )
                    return get_examples_func(error_type, **kwargs)

        except Exception as e:
            logger.debug(
                "Could not get error examples from %s.%s: %s",
                group_name,
                command_name,
                e,
            )

        return None


# Global error handler instance
error_handler = CLIErrorHandler()
