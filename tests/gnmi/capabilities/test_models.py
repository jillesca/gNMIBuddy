import pytest
from src.gnmi.capabilities.models import (
    ModelIdentifier,
    ModelRequirement,
    DeviceCapabilities,
)
from src.gnmi.capabilities.encoding import GnmiEncoding


def test_model_identifier_basic():
    m = ModelIdentifier(
        name="openconfig-system", version="0.17.1", organization="OC"
    )
    assert m.matches("openconfig-system")
    assert m.normalized_version() == "0.17.1"
    assert "openconfig-system@0.17.1" in str(m)


def test_model_requirement_requires_version():
    r1 = ModelRequirement(name="openconfig-system", minimum_version="0.17.1")
    r2 = ModelRequirement(name="openconfig-system")
    assert r1.requires_version() is True
    assert r2.requires_version() is False


def _cmp(a, b):
    if a is None or b is None:
        return None
    # very small comparator for tests: numeric compare by tuple of ints
    at = tuple(int(x) for x in a.split("."))
    bt = tuple(int(x) for x in b.split("."))
    return -1 if at < bt else (1 if at > bt else 0)


def _norm(x):
    return x.lower() if x else None


def test_device_capabilities_methods():
    caps = DeviceCapabilities(
        models=[
            ModelIdentifier(name="openconfig-system", version="0.17.0"),
            ModelIdentifier(name="openconfig-interfaces", version="4.1.0"),
        ],
        encodings=[GnmiEncoding.JSON_IETF, GnmiEncoding.JSON],
        gnmi_version="0.8.0",
    )

    req_sys = ModelRequirement("openconfig-system", "0.17.1")
    req_int = ModelRequirement("openconfig-interfaces", "3.0.0")
    present, older = caps.has_model(req_sys, _cmp)
    assert present is True and older is True
    present, older = caps.has_model(req_int, _cmp)
    assert present is True and older is False

    assert caps.supports_encoding(GnmiEncoding.JSON_IETF)
    assert caps.supports_encoding(GnmiEncoding.JSON)
    assert not caps.supports_encoding(GnmiEncoding.ASCII)
