import json
import pytest
from src.parsers.system_info_parser import SystemInfoParser


@pytest.fixture
def sample_input():
    with open("tests/network_tools/system_info/system_info_input.json") as f:
        return json.load(f)


def test_system_info_parser_basic(sample_input):
    parser = SystemInfoParser()
    result = parser.parse(sample_input)
    # Check top-level fields
    assert result["hostname"] == "xrd-9"
    assert result["software_version"] == "24.2.1"
    assert result["timezone"] == "Universal"
    assert result["memory_physical"] == "33657106432"
    # Check gRPC server parsing
    assert isinstance(result["grpc_servers"], list)
    assert result["grpc_servers"][0]["name"] == "DEFAULT"
    assert result["grpc_servers"][0]["port"] == 57777
    # Check logging selectors
    assert isinstance(result["logging"], list)
    assert result["logging"][0]["severity"] == "DEBUG"
    # Check message summary
    assert result["message"]["msg"].startswith("RP/0/RP0/CPU0May 25")
    # Check users
    assert any(u["username"] == "admin" for u in result["users"])
    assert any(u["role"] == "root-lr" for u in result["users"])
    # Check boot_time
    assert result["boot_time"] == "1747381914000000000"
    # Check boot_time_human is a non-empty string and UTC formatted
    assert isinstance(result["boot_time_human"], str)
    assert result["boot_time_human"].endswith("UTC")
    assert len(result["boot_time_human"]) > 0
    # Check uptime is a non-empty string and contains d, h, m, s
    assert isinstance(result["uptime"], str)
    for part in ["d", "h", "m", "s"]:
        assert part in result["uptime"]


def test_system_info_parser_output_matches_expected(sample_input):
    parser = SystemInfoParser()
    result = parser.parse(sample_input)
    with open("tests/network_tools/system_info/system_info_output.json") as f:
        expected = json.load(f)

    # For uptime, allow a small difference in seconds due to runtime
    def parse_uptime(uptime_str):
        parts = uptime_str.split()
        days = int(parts[0][:-1])
        hours = int(parts[1][:-1])
        minutes = int(parts[2][:-1])
        seconds = int(parts[3][:-1])
        return days, hours, minutes, seconds

    # Compare all fields except uptime and current_datetime
    for key in expected:
        if key in ("uptime", "current_datetime"):
            continue
        assert result[key] == expected[key], f"Mismatch in field: {key}"
    # Uptime: just check format is correct (e.g. 'Xd Xh Xm Xs')
    import re

    assert re.match(
        r"^\d+d \d+h \d+m \d+s$", result["uptime"]
    ), f"Uptime format invalid: {result['uptime']}"
