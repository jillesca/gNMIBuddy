from src.gnmi.capabilities.version import NormalizedVersion, safe_compare


def test_semver_parse_and_compare():
    a = NormalizedVersion.from_string("1.2.3")
    b = NormalizedVersion.from_string("1.3.0")
    assert a.kind == "semver" and b.kind == "semver"
    assert safe_compare("1.2.3", "1.3.0") == -1
    assert safe_compare("1.3.0", "1.3.0") == 0
    assert safe_compare("1.4.0", "1.3.0") == 1


def test_date_and_raw_comparisons():
    assert safe_compare("2024-12-01", "2025-01-01") == -1
    assert safe_compare("abc", "abd") == -1


def test_mixed_kinds_return_none():
    assert safe_compare("1.2.3", "20240101") is None
    assert safe_compare("1.2.3", None) is None
