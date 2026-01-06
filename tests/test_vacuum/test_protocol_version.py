import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.T2267 import T2267


@pytest.fixture
def common_args() -> dict[str, str]:
    return {
        "device_id": "test_id",
        "host": "192.168.1.100",
        "local_key": "abcdefghijklmnop",
    }


def test_default_protocol_version_for_old_model(common_args: dict[str, str]) -> None:
    """Default to protocol (3,3) for models without explicit version (e.g., T2118)."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None) as m_init:
        RoboVac(model_code="T2118", **common_args)
        # Ensure version kwarg is passed and equals (3,3)
        assert m_init.called
        _, kwargs = m_init.call_args
        assert kwargs.get("version") == (3, 3)


def test_model_specific_protocol_version_tuple_overrides(common_args: dict[str, str]) -> None:
    """If model defines protocol_version tuple, it should be passed through."""
    # Set model's protocol_version to (3,5)
    original = getattr(T2267, "protocol_version", None)
    T2267.protocol_version = (3, 5)
    try:
        with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None) as m_init:
            RoboVac(model_code="T2267", **common_args)
            assert m_init.called
            _, kwargs = m_init.call_args
            assert kwargs.get("version") == (3, 5)
    finally:
        # restore
        if original is None:
            delattr(T2267, "protocol_version")
        else:
            T2267.protocol_version = original


def test_model_specific_protocol_version_float_is_converted(common_args: dict[str, str]) -> None:
    """If model defines protocol_version float, convert to tuple (major, minor)."""
    original = getattr(T2267, "protocol_version", None)
    T2267.protocol_version = 3.4
    try:
        with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None) as m_init:
            RoboVac(model_code="T2267", **common_args)
            assert m_init.called
            _, kwargs = m_init.call_args
            assert kwargs.get("version") == (3, 4)
    finally:
        if original is None:
            delattr(T2267, "protocol_version")
        else:
            T2267.protocol_version = original
