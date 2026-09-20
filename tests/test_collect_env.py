from __future__ import annotations

from multinode_diag.collect_env import (
    collect_environment,
    collect_network_interfaces,
    optional_float,
    optional_int,
    package_version,
)


def test_optional_float_parses_number() -> None:
    assert optional_float("123.5") == 123.5


def test_optional_float_accepts_nvidia_na() -> None:
    assert optional_float("[N/A]") is None
    assert optional_float("N/A") is None
    assert optional_float("Not Supported") is None


def test_optional_float_accepts_malformed_value() -> None:
    assert optional_float("unexpected-value") is None


def test_optional_int_parses_number() -> None:
    assert optional_int("7") == 7


def test_optional_int_accepts_na() -> None:
    assert optional_int("[N/A]") is None


def test_collect_environment_has_required_sections() -> None:
    payload = collect_environment()

    assert "collected_at_utc" in payload
    assert "hostname" in payload
    assert "os" in payload
    assert "python" in payload
    assert "cpu" in payload
    assert "python_packages" in payload
    assert "network_interfaces" in payload
    assert "nvidia" in payload
    assert "commands" in payload


def test_python_version_is_present() -> None:
    payload = collect_environment()

    assert payload["python"]["version"]
    assert payload["python"]["executable"]


def test_network_interfaces_returns_list() -> None:
    assert isinstance(collect_network_interfaces(), list)


def test_missing_package_returns_none() -> None:
    assert package_version(
        "package-that-definitely-does-not-exist-123456789"
    ) is None
