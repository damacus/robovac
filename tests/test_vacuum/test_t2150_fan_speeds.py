"""Regression coverage for G10 Hybrid fan-speed capabilities."""

from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac


def test_t2150_advertises_only_supported_fan_speeds() -> None:
    """The G10 Hybrid exposes only its Standard and Max choices to Home Assistant."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2150",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

    assert robovac.getFanSpeeds() == ["Standard", "Max"]
