#!/usr/bin/env python3
"""
System information parser module.
Parses system information data from gNMI responses into a structured format.
"""

from typing import Dict, Any
from src.parsers.base import BaseParser
import datetime


class SystemInfoParser(BaseParser):
    """
    Parser for system information data from gNMI responses.
    """

    def parse(self, data: Dict[str, Any]) -> Dict[str, Any]:
        extracted = self.extract_data(data)
        return self.transform_data(extracted)

    def extract_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Extract the first system response if present
        responses = data.get("response", [])
        if not responses:
            return {}
        val = responses[0].get("val", {})
        return val

    def transform_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        # Parse only selected fields for clarity and usability
        state = extracted_data.get("state", {})
        clock = extracted_data.get("clock", {}).get("state", {})
        memory = extracted_data.get("memory", {}).get("state", {})
        grpc_servers = self._parse_grpc_servers(extracted_data)
        logging = self._parse_logging_selectors(extracted_data)
        message_summary = self._parse_message_summary(extracted_data)
        users = self._parse_users(extracted_data)
        boot_time_ns = state.get("boot-time")
        boot_time_human = self._parse_boot_time(boot_time_ns)
        uptime = self._calculate_uptime(boot_time_ns)

        return {
            "hostname": state.get("hostname"),
            "current_datetime": state.get("current-datetime"),
            "software_version": state.get("software-version"),
            "timezone": clock.get("timezone-name"),
            "memory_physical": memory.get("physical"),
            "grpc_servers": grpc_servers,
            "logging": logging,
            "message": message_summary,
            "users": users,
            "boot_time": boot_time_ns,
            "boot_time_human": boot_time_human,
            "uptime": uptime,
        }

    def _calculate_uptime(self, boot_time_ns):
        try:
            if boot_time_ns is None:
                return None
            boot_time_ns = int(boot_time_ns)
            boot_time_sec = boot_time_ns / 1e9
            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            uptime_seconds = int(now - boot_time_sec)
            # Format as days, hours, minutes, seconds
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{days}d {hours}h {minutes}m {seconds}s"
        except (ValueError, TypeError, OSError):
            return None

    def _parse_users(self, extracted_data: Dict[str, Any]):
        aaa_users = (
            extracted_data.get("aaa", {})
            .get("authentication", {})
            .get("users", {})
            .get("user", [])
        )
        return [
            {
                "username": u["state"].get("username"),
                "role": u["state"].get("role"),
            }
            for u in aaa_users
            if u.get("state")
        ]

    def _parse_grpc_servers(self, extracted_data: Dict[str, Any]):
        grpc_servers = extracted_data.get(
            "openconfig-system-grpc:grpc-servers", {}
        ).get("grpc-server", [])
        return [
            {
                "name": s.get("state", {}).get("name"),
                "enable": s.get("state", {}).get("enable"),
                "port": s.get("state", {}).get("port"),
                "transport_security": s.get("state", {}).get(
                    "transport-security"
                ),
                "listen_addresses": s.get("state", {}).get(
                    "listen-addresses", []
                ),
            }
            for s in grpc_servers
        ]

    def _parse_logging_selectors(self, extracted_data: Dict[str, Any]):
        logging_console = (
            extracted_data.get("logging", {})
            .get("console", {})
            .get("selectors", {})
            .get("selector", [])
        )
        return [
            {"severity": sel.get("severity"), "facility": sel.get("facility")}
            for sel in logging_console
        ]

    def _parse_message_summary(self, extracted_data: Dict[str, Any]):
        messages = extracted_data.get("messages", {}).get("state", {})
        message = messages.get("message", {})
        if not message:
            return {}
        return {
            "msg": message.get("msg"),
            "priority": message.get("priority"),
            "app_name": message.get("app-name"),
        }

    def _parse_boot_time(self, boot_time_ns):
        # boot_time_ns is a string representing nanoseconds since epoch
        try:
            if boot_time_ns is None:
                return None
            boot_time_ns = int(boot_time_ns)
            boot_time_sec = boot_time_ns / 1e9
            dt = datetime.datetime.fromtimestamp(
                boot_time_sec, datetime.timezone.utc
            )
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError, OSError):
            return None
