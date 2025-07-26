#!/usr/bin/env python3
"""Module logging help system for --module-log-levels option"""
from dataclasses import dataclass
from typing import List, Dict, Tuple
import click
from src.logging import LoggerNames


@dataclass
class ModuleLogHelpData:
    """Complete data for module log help template"""

    log_levels: List[str]
    level_descriptions: Dict[str, str]
    module_categories: Dict[str, List[Tuple[str, str]]]
    usage_examples: List[Tuple[str, str]]
    common_scenarios: List[Tuple[str, str]]


class ModuleLogHelp:
    """Helper class for displaying module logging information using a single template"""

    # Single comprehensive template
    HELP_TEMPLATE = """
═══════════════════════════════════════════════════════════
📋 Module-Specific Logging Help
═══════════════════════════════════════════════════════════

The --module-log-levels option allows you to control logging verbosity
for specific modules, reducing noise and focusing on relevant information.

📝 Format: --module-log-levels "module1=level1,module2=level2"

📊 Available Log Levels:
{log_levels_section}

{module_categories_section}

💡 Usage Examples:
{usage_examples_section}

🎯 Common Scenarios:
{common_scenarios_section}

📚 Additional Resources:
  • Full documentation: src/logging/README.md
  • Implementation details: src/logging/IMPLEMENTATION.md

💡 Tip: Use --structured-logging for machine-readable JSON output
═══════════════════════════════════════════════════════════
"""

    # Available log levels
    LOG_LEVELS = ["debug", "info", "warning", "error"]

    # Log level descriptions
    LEVEL_DESCRIPTIONS = {
        "debug": "Detailed diagnostic information",
        "info": "General operational information",
        "warning": "Something unexpected happened but we can continue",
        "error": "Serious problem that prevented operation completion",
    }

    # Module categories for organized display
    MODULE_CATEGORIES = {
        "Core Application": [
            (LoggerNames.APP_ROOT, "Root application logger"),
            (LoggerNames.API, "API layer"),
            (LoggerNames.CLI, "CLI components"),
            (LoggerNames.MCP, "MCP server"),
        ],
        "Data Collection": [
            (LoggerNames.COLLECTORS, "All data collection modules"),
            (LoggerNames.INTERFACES, "Interface data collection"),
            (LoggerNames.ROUTING, "Routing protocol data"),
            (LoggerNames.MPLS, "MPLS data collection"),
            (LoggerNames.VPN, "VPN/VRF data collection"),
            (LoggerNames.LOGS, "Device logs collection"),
            (LoggerNames.SYSTEM, "System information collection"),
            (LoggerNames.TOPOLOGY, "Topology data collection"),
            (LoggerNames.PROFILE, "Device profile analysis"),
        ],
        "Infrastructure": [
            (LoggerNames.GNMI, "gNMI client operations"),
            (LoggerNames.INVENTORY, "Device inventory management"),
            (LoggerNames.PROCESSORS, "Data processing modules"),
            (LoggerNames.SERVICES, "Service layer"),
            (LoggerNames.UTILS, "Utility functions"),
        ],
        "External Libraries": [
            (LoggerNames.PYGNMI, "PyGNMI library (external)"),
            (LoggerNames.GRPC, "gRPC library (external)"),
            ("urllib3", "HTTP client library"),
            ("asyncio", "Async I/O operations"),
        ],
    }

    # Simplified usage examples
    USAGE_EXAMPLES = [
        (
            "Enable debug logging for interface collection",
            f"{LoggerNames.INTERFACES}=debug",
        ),
        (
            "Multiple modules with different levels",
            f"{LoggerNames.COLLECTORS}=debug,{LoggerNames.PYGNMI}=error",
        ),
        (
            "Quiet external libraries",
            f"{LoggerNames.PYGNMI}=error,{LoggerNames.GRPC}=error,urllib3=warning",
        ),
        (
            "Debug gNMI connection issues",
            f"{LoggerNames.GNMI}=debug,{LoggerNames.PYGNMI}=info",
        ),
        (
            "Focus on specific data collection",
            f"{LoggerNames.ROUTING}=debug,{LoggerNames.PYGNMI}=warning",
        ),
    ]

    # Simplified common scenarios
    COMMON_SCENARIOS = [
        (
            "🔍 Debugging Interface Issues",
            f'--log-level warning --module-log-levels "{LoggerNames.INTERFACES}=debug"',
        ),
        (
            "🔍 Debugging gNMI Connection",
            f'--log-level warning --module-log-levels "{LoggerNames.GNMI}=debug,{LoggerNames.PYGNMI}=info"',
        ),
        (
            "🔇 Minimal Noise (Production)",
            f'--log-level error --module-log-levels "{LoggerNames.PYGNMI}=error,{LoggerNames.GRPC}=error"',
        ),
        ("📈 Full Debug Mode", "--log-level debug"),
        (
            "🎛️  Granular Control",
            f'--module-log-levels "{LoggerNames.COLLECTORS}=debug,{LoggerNames.GNMI}=info,{LoggerNames.PYGNMI}=warning"',
        ),
    ]

    @classmethod
    def get_all_modules(cls) -> List[str]:
        """Get a flat list of all available modules"""
        modules = []
        for category_modules in cls.MODULE_CATEGORIES.values():
            modules.extend([module for module, _ in category_modules])
        return sorted(modules)

    @classmethod
    def format_complete_help(cls) -> str:
        """Format the complete help message using the single template"""
        # Format log levels section
        log_levels_lines = []
        for level in cls.LOG_LEVELS:
            description = cls.LEVEL_DESCRIPTIONS.get(level, "")
            log_levels_lines.append(f"  • {level:<8} - {description}")
        log_levels_section = "\n".join(log_levels_lines)

        # Format module categories section
        category_lines = []
        for category_name, modules in cls.MODULE_CATEGORIES.items():
            category_lines.append(f"📁 {category_name}:")
            for module, description in modules:
                category_lines.append(f"  • {module:<35} - {description}")
            category_lines.append("")  # Add spacing between categories
        module_categories_section = "\n".join(category_lines).rstrip()

        # Format usage examples section
        examples_lines = []
        for i, (description, module_config) in enumerate(
            cls.USAGE_EXAMPLES, 1
        ):
            examples_lines.append(f"{i}. {description}:")
            examples_lines.append(f'   --module-log-levels "{module_config}"')
            if i < len(cls.USAGE_EXAMPLES):
                examples_lines.append("")
        usage_examples_section = "\n".join(examples_lines)

        # Format common scenarios section
        scenarios_lines = []
        for description, command in cls.COMMON_SCENARIOS:
            scenarios_lines.append(f"{description}:")
            scenarios_lines.append(f"  {command}")
            scenarios_lines.append("")
        common_scenarios_section = "\n".join(scenarios_lines).rstrip()

        # Apply to template
        return cls.HELP_TEMPLATE.format(
            log_levels_section=log_levels_section,
            module_categories_section=module_categories_section,
            usage_examples_section=usage_examples_section,
            common_scenarios_section=common_scenarios_section,
        ).strip()


def show_module_log_help():
    """Display the complete module logging help"""
    help_text = ModuleLogHelp.format_complete_help()
    click.echo(help_text)


def show_module_log_help_callback(ctx, param, value):
    """Callback for showing module log help"""
    if not value or ctx.resilient_parsing:
        return

    show_module_log_help()
    ctx.exit()


def get_available_modules() -> List[str]:
    """Get list of available modules for validation"""
    return ModuleLogHelp.get_all_modules()


def validate_module_log_levels(module_levels_str: str) -> Tuple[bool, str]:
    """
    Validate module log levels string format

    Args:
        module_levels_str: String in format "module1=level1,module2=level2"

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not module_levels_str:
        return True, ""

    available_levels = set(ModuleLogHelp.LOG_LEVELS)

    try:
        pairs = module_levels_str.split(",")
        for pair in pairs:
            pair = pair.strip()
            if "=" not in pair:
                return (
                    False,
                    f"Invalid format in '{pair}'. Use 'module=level' format.",
                )

            module, level = pair.split("=", 1)
            module = module.strip()
            level = level.strip().lower()

            if level not in available_levels:
                return (
                    False,
                    f"Invalid log level '{level}'. Available levels: {', '.join(sorted(available_levels))}",
                )

            # Note: We don't validate module names strictly since users might want to use
            # other modules not in our predefined list

    except Exception as e:
        return False, f"Error parsing module log levels: {str(e)}"

    return True, ""


# Export main functions
__all__ = [
    "ModuleLogHelp",
    "ModuleLogHelpData",
    "show_module_log_help",
    "show_module_log_help_callback",
    "get_available_modules",
    "validate_module_log_levels",
]
