#!/usr/bin/env python3
"""Command implementations for the network tools CLI"""
from src.logging.config import get_logger
from src.utils.parallel_execution import run_command_on_all_devices

# Keep BaseCommand for backward compatibility while transitioning
from abc import ABC, abstractmethod

logger = get_logger(__name__)


class BaseCommand(ABC):
    """Legacy BaseCommand class for backward compatibility during migration"""

    name = None
    help = None
    description = None

    def __init__(self):
        self.parser = None

    @abstractmethod
    def configure_parser(self, parser):
        """Configure the argument parser for this command"""
        pass

    @abstractmethod
    def execute(self, args):
        """Execute the command with the given arguments"""
        pass

    def register(self, subparsers):
        """Register this command with the given subparsers"""
        if not self.name or not self.help:
            raise ValueError(
                f"Command {self.__class__.__name__} must define name and help attributes"
            )

        self.parser = subparsers.add_parser(
            self.name,
            help=self.help,
            description=self.description or self.help,
        )

        self.configure_parser(self.parser)
        return self.parser


class RoutingCommand(BaseCommand):
    """Command handler for routing information"""

    name = "routing"
    help = "Get routing information"
    description = "Get routing information from a network device"

    def configure_parser(self, parser):
        parser.add_argument(
            "--protocol", help="Routing protocol filter (bgp, isis)"
        )
        parser.add_argument(
            "--detail", action="store_true", help="Show detailed information"
        )

    def execute(self, args):
        from api import get_routing_info

        if hasattr(args, "all_devices") and args.all_devices:
            return run_command_on_all_devices(
                get_routing_info,
                args.protocol,
                args.detail,
                max_workers=args.max_workers,
            )
        return get_routing_info(args.device, args.protocol, args.detail)


class InterfaceCommand(BaseCommand):
    """Command handler for interface information"""

    name = "interface"
    help = "Get interface information"
    description = "Get interface information from a network device"

    def configure_parser(self, parser):
        parser.add_argument("--name", help="Interface name")

    def execute(self, args):
        from api import get_interface_info

        if hasattr(args, "all_devices") and args.all_devices:
            return run_command_on_all_devices(
                get_interface_info,
                args.name,
                max_workers=args.max_workers,
            )
        return get_interface_info(
            device_name=args.device,
            interface=args.name,
        )


class MPLSCommand(BaseCommand):
    """Command handler for MPLS information"""

    name = "mpls"
    help = "Get MPLS information"
    description = "Get MPLS and segment routing information"

    def configure_parser(self, parser):
        parser.add_argument(
            "--detail", action="store_true", help="Show detailed information"
        )

    def execute(self, args):
        from api import get_mpls_info

        if hasattr(args, "all_devices") and args.all_devices:
            return run_command_on_all_devices(
                get_mpls_info,
                args.detail,
                max_workers=args.max_workers,
            )
        return get_mpls_info(args.device, args.detail)


class VPNCommand(BaseCommand):
    """Command handler for VPN information"""

    name = "vpn"
    help = "Get VPN/VRF information"
    description = "Get VPN and VRF configuration information"

    def configure_parser(self, parser):
        parser.add_argument("--vrf", help="VRF name")
        parser.add_argument(
            "--detail", action="store_true", help="Show detailed information"
        )

    def execute(self, args):
        from api import get_vpn_info

        if hasattr(args, "all_devices") and args.all_devices:
            return run_command_on_all_devices(
                get_vpn_info,
                args.vrf,
                args.detail,
                max_workers=args.max_workers,
            )
        return get_vpn_info(args.device, args.vrf, args.detail)


class SystemCommand(BaseCommand):
    """Command handler for VPN information"""

    name = "system"
    help = "Get system information"
    description = "Get system information"

    def configure_parser(self, parser):
        parser.add_argument(
            "--detail", action="store_true", help="Show detailed information"
        )

    def execute(self, args):
        from api import get_system_info

        if hasattr(args, "all_devices") and args.all_devices:

            return run_command_on_all_devices(
                get_system_info,
                max_workers=args.max_workers,
            )
        return get_system_info(args.device)


class DeviceProfileCommand(BaseCommand):
    name = "deviceprofile"
    help = "Get device profile information"
    description = "Get device role/profile (PE, P, RR, etc.)"

    def configure_parser(self, parser):
        pass

    def execute(self, args):
        from api import get_device_profile_api

        if hasattr(args, "all_devices") and args.all_devices:
            return run_command_on_all_devices(
                get_device_profile_api,
                max_workers=args.max_workers,
            )

        return get_device_profile_api(args.device)


class LoggingCommand(BaseCommand):
    """Command handler for device logs"""

    name = "logging"
    help = "Get logs from the device"
    description = "Get logs from the device"

    def configure_parser(self, parser):
        parser.add_argument("--keywords", help="keywords to filter logs")
        parser.add_argument(
            "--minutes",
            help="displayed last logs on X minutes",
            type=int,
            default=5,
        )
        parser.add_argument(
            "--show-all-logs",
            action="store_true",
            help="disable time filtering and show all logs",
            dest="show_all_logs",
        )

    def execute(self, args):
        from api import get_logs

        if hasattr(args, "all_devices") and args.all_devices:
            return run_command_on_all_devices(
                get_logs,
                args.keywords,
                args.minutes,
                args.show_all_logs,
                max_workers=args.max_workers,
            )
        return get_logs(
            args.device, args.keywords, args.minutes, args.show_all_logs
        )


class ListDevicesCommand(BaseCommand):
    """Command handler for listing available devices"""

    name = "list-devices"
    help = "List available devices"
    description = "Show all available devices in the inventory"

    def configure_parser(self, parser):
        pass  # No additional arguments needed

    def execute(self, args):
        from api import get_devices

        return get_devices()


class ListCommandsCommand(BaseCommand):
    """Command handler for listing all available commands"""

    name = "list-commands"
    help = "List all available commands and their options"
    description = "Display all available CLI commands and network commands"

    def configure_parser(self, parser):
        parser.add_argument(
            "--detail",
            action="store_true",
            help="Show detailed command information",
        )

    def execute(self, args):
        logger.info("Displaying all available commands")
        from src.cmd.display import display_all_commands

        display_all_commands(detailed=args.detail)
        return None  # Special case, no result to return


class TestAllCommand(BaseCommand):
    """Command handler for testing all APIs against devices"""

    name = "test-all"
    help = "Run all available APIs against devices"
    description = "Test all network APIs against one or all devices"

    def configure_parser(self, parser):
        parser.add_argument(
            "--detail",
            action="store_true",
            help="Show detailed information for each API",
        )
        parser.add_argument(
            "--minutes",
            type=int,
            default=5,
            help="Minutes for logs filtering (default: 5)",
        )
        parser.add_argument(
            "--show-all-logs",
            action="store_true",
            help="Show all logs without time filtering",
        )
        parser.add_argument(
            "--test-query",
            action="store_true",
            help="Test query_network API with a sample query",
        )

    def execute(self, args):
        if hasattr(args, "all_devices") and args.all_devices:
            logger.info("Testing all APIs against all available devices")
            from api import list_available_devices

            devices_info = list_available_devices()
            device_list = [
                device["name"] for device in devices_info["devices"]
            ]

            results = {}
            for device_name in device_list:
                results[device_name] = self._run_all_apis(device_name, args)

            return {
                "command": "test-all",
                "all_devices": True,
                "results": results,
            }
        else:
            logger.info("Testing all APIs against device: %s", args.device)
            result = self._run_all_apis(args.device, args)
            return {
                "command": "test-all",
                "device": args.device,
                "results": result,
            }

    def _run_all_apis(self, device_name, args):
        """Run all APIs for a single device and collect the results"""
        from api import (
            get_routing_info,
            get_logs,
            get_interface_info,
            get_mpls_info,
            get_vpn_info,
            get_system_info,
            get_device_profile_api,
            get_topology_ip_adjacency_dump,
            get_topology_neighbors,
            # get_topology_path,
            # get_topology_segment,
        )

        results = {}

        logger.info("Testing routing API for %s", device_name)
        try:
            results["routing"] = get_routing_info(
                device_name, include_details=args.detail
            )
        except Exception as e:
            logger.error("Error testing routing API: %s", e)
            results["routing"] = {"error": str(e)}

        logger.info("Testing logs API for %s", device_name)
        try:
            results["logs"] = get_logs(
                device_name,
                minutes=args.minutes,
                show_all_logs=args.show_all_logs,
            )
        except Exception as e:
            logger.error("Error testing logs API: %s", e)
            results["logs"] = {"error": str(e)}

        logger.info("Testing interface API for %s", device_name)
        try:
            results["interface"] = get_interface_info(device_name)
        except Exception as e:
            logger.error("Error testing interface API: %s", e)
            results["interface"] = {"error": str(e)}

        logger.info("Testing MPLS API for %s", device_name)
        try:
            results["mpls"] = get_mpls_info(
                device_name, include_details=args.detail
            )
        except Exception as e:
            logger.error("Error testing MPLS API: %s", e)
            results["mpls"] = {"error": str(e)}

        logger.info("Testing VPN API for %s", device_name)
        try:
            results["vpn"] = get_vpn_info(
                device_name, include_details=args.detail
            )
        except Exception as e:
            logger.error("Error testing VPN API: %s", e)
            results["vpn"] = {"error": str(e)}

        logger.info("Testing system for %s", device_name)
        try:
            results["system"] = get_system_info(device_name)
        except Exception as e:
            logger.error("Error testing System API: %s", e)
            results["system"] = {"error": str(e)}

        logger.info("Testing  deviceprofile for %s", device_name)
        try:
            results["deviceprofile"] = get_device_profile_api(device_name)
        except Exception as e:
            logger.error("Error testing System API: %s", e)
            results["deviceprofile"] = {"error": str(e)}

        logger.info("Testing topology_adjacency for %s", device_name)
        try:
            results["topology_adjacency"] = get_topology_ip_adjacency_dump(
                device_name
            )
        except Exception as e:
            logger.error("Error testing topology_adjacency API: %s", e)
            results["topology_adjacency"] = {"error": str(e)}

        logger.info("Testing topology_neighbors for %s", device_name)
        try:
            results["topology_neighbors"] = get_topology_neighbors(device_name)
        except Exception as e:
            logger.error("Error testing topology_neighbors API: %s", e)
            results["topology_neighbors"] = {"error": str(e)}

        # logger.info("Testing topology_path for %s", device_name)
        # try:
        #     # Use device_name as both source and target for test, or skip if not provided
        #     # In real test, you may want to parametrize this
        #     results["topology_path"] = get_topology_path(
        #         device_name, device_name
        #     )
        # except Exception as e:
        #     logger.error("Error testing topology_path API: %s", e)
        #     results["topology_path"] = {"error": str(e)}

        # logger.info("Testing topology_segment for %s", device_name)
        # try:
        #     # Use a dummy network for test, or parametrize as needed
        #     results["topology_segment"] = get_topology_segment(
        #         device_name, "10.0.0.0/30"
        #     )
        # except Exception as e:
        #     logger.error("Error testing topology_segment API: %s", e)
        #     results["topology_segment"] = {"error": str(e)}

        if args.test_query:
            logger.info(
                "Skipping query API (not implemented) for %s", device_name
            )
            results["query"] = {
                "status": "skipped",
                "reason": "API not implemented",
            }

        return results


class TopologyIPAdjacencyCommand(BaseCommand):
    name = "topology-adjacency"
    help = "Show full topology adjacency dump"
    description = "Show all adjacency edges in the topology graph"

    def configure_parser(self, parser):
        pass  # Only needs device

    def execute(self, args):
        from api import get_topology_ip_adjacency_dump

        if hasattr(args, "all_devices") and args.all_devices:
            return run_command_on_all_devices(
                get_topology_ip_adjacency_dump,
                max_workers=args.max_workers,
            )

        return get_topology_ip_adjacency_dump(args.device)


class TopologyNeighborsCommand(BaseCommand):
    name = "topology-neighbors"
    help = "Show direct neighbors of a device"
    description = (
        "Show direct neighbors of a specified device in the topology graph"
    )

    def configure_parser(self, parser):
        pass  # Only needs device

    def execute(self, args):
        from api import get_topology_neighbors

        if hasattr(args, "all_devices") and args.all_devices:
            return run_command_on_all_devices(
                get_topology_neighbors,
                max_workers=args.max_workers,
            )

        return get_topology_neighbors(args.device)


class LogLevelCommand(BaseCommand):
    """Command handler for managing application logging levels"""

    name = "log-level"
    help = "Manage application logging levels"
    description = "View and modify logging levels for different modules"

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers(
            dest="log_action", help="Log level actions"
        )

        # Show current levels
        show_parser = subparsers.add_parser(
            "show", help="Show current log levels"
        )

        # Set module log level
        set_parser = subparsers.add_parser(
            "set", help="Set log level for a module"
        )
        set_parser.add_argument(
            "module",
            help="Module name (e.g., gnmibuddy.collectors.interfaces)",
        )
        set_parser.add_argument(
            "level",
            choices=["debug", "info", "warning", "error"],
            help="Log level",
        )

        # List available modules
        list_parser = subparsers.add_parser(
            "modules", help="List available modules for logging control"
        )

    def execute(self, args):
        from src.logging.config import LoggingConfig, LoggerNames

        if args.log_action == "show":
            return self._show_current_levels()
        elif args.log_action == "set":
            return self._set_module_level(args.module, args.level)
        elif args.log_action == "modules":
            return self._list_available_modules()
        else:
            return {"error": "Invalid log action"}

    def _show_current_levels(self):
        from src.logging.config import LoggingConfig

        levels = LoggingConfig.get_module_levels()
        return {
            "current_module_levels": levels,
            "available_actions": ["show", "set", "modules"],
        }

    def _set_module_level(self, module: str, level: str):
        from src.logging.config import LoggingConfig

        try:
            LoggingConfig.set_module_level(module, level)
            return {
                "success": True,
                "message": f"Set {module} log level to {level}",
                "module": module,
                "level": level,
            }
        except (ValueError, KeyError, AttributeError) as e:
            return {
                "success": False,
                "error": str(e),
                "module": module,
                "level": level,
            }

    def _list_available_modules(self):
        from src.logging.config import LoggerNames

        # Get all logger name constants
        modules = []
        for attr_name in dir(LoggerNames):
            if not attr_name.startswith("_"):
                modules.append(getattr(LoggerNames, attr_name))

        return {
            "available_modules": sorted(modules),
            "examples": [
                "gnmibuddy.collectors.interfaces - Interface collection operations",
                "gnmibuddy.collectors.routing - Routing protocol operations",
                "gnmibuddy.gnmi - gNMI client operations",
                "gnmibuddy.inventory - Device inventory management",
                "pygnmi - External pygnmi library",
            ],
            "usage": "Use 'log-level set <module> <level>' to change levels",
        }


# Dictionary of all available commands
COMMANDS = {
    cmd.name: cmd()
    for cmd in [
        RoutingCommand,
        InterfaceCommand,
        MPLSCommand,
        VPNCommand,
        ListDevicesCommand,
        ListCommandsCommand,
        LoggingCommand,
        TestAllCommand,
        SystemCommand,
        DeviceProfileCommand,
        TopologyIPAdjacencyCommand,
        TopologyNeighborsCommand,
        LogLevelCommand,
        # TopologyPathCommand,
        # TopologySegmentCommand,
    ]
}
