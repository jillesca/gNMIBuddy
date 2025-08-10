from src.gnmi.capabilities.encoding import EncodingPolicy


def test_normalize_and_choose_supported():
    p = EncodingPolicy()
    assert p.normalize("JSON_IETF") == "json_ietf"
    assert p.normalize("json") == "json"

    supported = ["JSON_IETF", "JSON"]
    sel, fb = p.choose_supported("json_ietf", supported)
    assert sel == "json_ietf" and fb is False

    sel, fb = p.choose_supported("ascii", supported)
    assert sel is None and fb is False

    sel, fb = p.choose_supported("json_ietf", ["ASCII"])  # fallback
    assert sel == "ascii" and fb is True
