from src.gnmi.capabilities.repository import DeviceCapabilitiesRepository
from src.gnmi.capabilities.models import DeviceCapabilities, ModelIdentifier
from src.schemas.models import Device


def _dev(name="R1"):
    return Device(name=name, ip_address="10.0.0.1", port=57777)


def test_repo_keying_and_basic_ops():
    repo = DeviceCapabilitiesRepository()
    d = _dev()
    key = repo.make_key(d)
    assert key.endswith(":10.0.0.1:57777")

    assert repo.get(d) is None and repo.has(d) is False
    caps = DeviceCapabilities(
        models=[ModelIdentifier("openconfig-system")], encodings=["json"]
    )
    repo.set(d, caps)
    assert repo.has(d) is True and repo.get(d) == caps

    repo.clear()
    assert repo.get(d) is None
