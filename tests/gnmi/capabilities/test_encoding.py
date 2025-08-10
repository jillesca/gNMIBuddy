from src.gnmi.capabilities.encoding import EncodingPolicy, GnmiEncoding


def test_normalize_and_choose_supported():
    p = EncodingPolicy()
    assert p.normalize("JSON_IETF") == GnmiEncoding.JSON_IETF
    assert p.normalize("json") == GnmiEncoding.JSON

    supported = ["JSON_IETF", "JSON"]
    sel, fb = p.choose_supported("json_ietf", supported)
    assert sel == GnmiEncoding.JSON_IETF and fb is False

    sel, fb = p.choose_supported("ascii", supported)
    assert sel is None and fb is False

    sel, fb = p.choose_supported("json_ietf", ["ASCII"])  # fallback
    assert sel == GnmiEncoding.ASCII and fb is True
