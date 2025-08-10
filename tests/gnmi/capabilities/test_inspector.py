from src.gnmi.capabilities.inspector import RequestInspector


def test_infer_requirements_basic_and_variants():
    inspector = RequestInspector()
    paths = [
        "openconfig-system:/system",
        "openconfig-interfaces:interfaces/interface[name=*]/state",
        "openconfig-network-instance:network-instances/network-instance[name=default]",
        "openconfig-system:system",
    ]
    reqs = inspector.infer_requirements(paths)
    names = sorted([r.name for r in reqs])
    assert names == [
        "openconfig-interfaces",
        "openconfig-network-instance",
        "openconfig-system",
    ]


def test_infer_requirements_ignores_unknown():
    inspector = RequestInspector()
    reqs = inspector.infer_requirements(["unknown:/x", "something-other/y"])
    assert reqs == []
