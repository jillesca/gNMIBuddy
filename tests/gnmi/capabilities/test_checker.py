from src.gnmi.capabilities.checker import CapabilityChecker
from src.gnmi.capabilities.models import DeviceCapabilities, ModelIdentifier
from src.gnmi.capabilities.service import CapabilityService
from src.gnmi.capabilities.encoding import EncodingPolicy
from src.schemas.models import Device
from src.gnmi.capabilities.encoding import GnmiEncoding
from src.gnmi.capabilities.errors import CapabilityError


class FakeService(CapabilityService):
    def __init__(self, caps):
        self._caps = caps

    def get_or_fetch(self, device):
        return self._caps


def _cmp(a, b):
    if a is None or b is None:
        return None
    at = tuple(int(x) for x in a.split("."))
    bt = tuple(int(x) for x in b.split("."))
    return -1 if at < bt else (1 if at > bt else 0)


def test_checker_missing_model():
    caps = DeviceCapabilities(
        models=[ModelIdentifier("openconfig-system", "0.17.1")],
        encodings=[GnmiEncoding.JSON_IETF],
    )
    service = FakeService(caps)
    checker = CapabilityChecker(service, _cmp, EncodingPolicy())
    device = Device(name="R1", ip_address="1.1.1.1")

    result = checker.check(
        device, ["openconfig-interfaces:interfaces"], GnmiEncoding.JSON_IETF
    )
    assert (
        result.is_failure()
        and result.error_type == CapabilityError.MODEL_NOT_SUPPORTED
    )


def test_checker_older_model_warning_and_success():
    caps = DeviceCapabilities(
        models=[
            ModelIdentifier("openconfig-system", "0.17.0"),
            ModelIdentifier("openconfig-interfaces", "4.1.0"),
        ],
        encodings=[GnmiEncoding.JSON],
    )
    service = FakeService(caps)
    checker = CapabilityChecker(service, _cmp, EncodingPolicy())
    device = Device(name="R1", ip_address="1.1.1.1")

    result = checker.check(
        device,
        [
            "openconfig-system:/system",
            "openconfig-interfaces:interfaces",
        ],
        GnmiEncoding.JSON,
    )
    assert (
        result.success is True
        and result.selected_encoding == GnmiEncoding.JSON
    )
    assert any("older" in w for w in result.warnings)


def test_checker_encoding_not_supported():
    caps = DeviceCapabilities(
        models=[ModelIdentifier("openconfig-system", "0.17.1")],
        encodings=[GnmiEncoding.JSON],
    )
    service = FakeService(caps)
    checker = CapabilityChecker(service, _cmp, EncodingPolicy())
    device = Device(name="R1", ip_address="1.1.1.1")

    result = checker.check(
        device, ["openconfig-system:/system"], GnmiEncoding.JSON_IETF
    )
    assert (
        result.is_failure()
        and result.error_type == CapabilityError.ENCODING_NOT_SUPPORTED
    )


def test_checker_fallback_encoding():
    caps = DeviceCapabilities(
        models=[ModelIdentifier("openconfig-system", "0.17.1")],
        encodings=[GnmiEncoding.ASCII],
    )
    service = FakeService(caps)
    checker = CapabilityChecker(service, _cmp, EncodingPolicy())
    device = Device(name="R1", ip_address="1.1.1.1")

    result = checker.check(device, ["openconfig-system:/system"], "json_ietf")
    assert (
        result.success is True
        and result.selected_encoding == GnmiEncoding.ASCII
    )
