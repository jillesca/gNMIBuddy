import json
import os
from src.parsers.deviceprofile_parser import DeviceProfileParser


def load_json(path):
    with open(path) as f:
        return json.load(f)


def test_deviceprofile_pe():
    input_data = load_json(
        os.path.join(os.path.dirname(__file__), "input_pe.json")
    )
    expected = load_json(
        os.path.join(os.path.dirname(__file__), "output_pe.json")
    )
    parser = DeviceProfileParser()
    result = parser.parse(input_data)
    assert result == expected


def test_deviceprofile_p():
    input_data = load_json(
        os.path.join(os.path.dirname(__file__), "input_p.json")
    )
    expected = load_json(
        os.path.join(os.path.dirname(__file__), "output_p.json")
    )
    parser = DeviceProfileParser()
    result = parser.parse(input_data)
    assert result == expected


def test_deviceprofile_rr():
    input_data = load_json(
        os.path.join(os.path.dirname(__file__), "input_rr.json")
    )
    expected = load_json(
        os.path.join(os.path.dirname(__file__), "output_rr.json")
    )
    parser = DeviceProfileParser()
    result = parser.parse(input_data)
    assert result == expected


def test_deviceprofile_ce():
    input_data = load_json(
        os.path.join(os.path.dirname(__file__), "input_ce.json")
    )
    expected = load_json(
        os.path.join(os.path.dirname(__file__), "output_ce.json")
    )
    parser = DeviceProfileParser()
    result = parser.parse(input_data)
    assert result == expected


def test_deviceprofile_unknown():
    input_data = load_json(
        os.path.join(os.path.dirname(__file__), "input_unknown.json")
    )
    expected = load_json(
        os.path.join(os.path.dirname(__file__), "output_unknown.json")
    )
    parser = DeviceProfileParser()
    result = parser.parse(input_data)
    assert result == expected
