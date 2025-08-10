#!/usr/bin/env python3
import types
from click.testing import CliRunner
from src.cmd.parser import cli, register_commands


def test_device_capabilities_help():
    register_commands()
    runner = CliRunner()
    result = runner.invoke(cli, ["device", "capabilities", "--help"])
    assert result.exit_code == 0
    assert "capabilities" in result.output.lower()
