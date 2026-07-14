"""Tests for fan-speed values audited against cached eufy manuals."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.mark.parametrize(
    ("model_code", "expected_values"),
    [
        (
            "T2181",
            {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        ),
        (
            "T2210",
            {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "boost_iq": "Boost_IQ",
            },
        ),
        (
            "T2212",
            {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "boost_iq": "Boost_IQ",
            },
        ),
        (
            "T2254",
            {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        ),
        (
            "T2255",
            {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        ),
        (
            "T2270",
            {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        ),
        (
            "T2272",
            {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        ),
        (
            "T2273",
            {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        ),
        (
            "T2276",
            {
                "pure": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "boost": "Boost",
            },
        ),
        (
            "T2351",
            {
                "quiet": "Quiet",
                "standard": "standard",
                "turbo": "turbo",
                "max": "max",
                "boost_iq": "boost_iq",
            },
        ),
    ],
)
def test_documented_fan_speed_values(model_code: str, expected_values: dict[str, str]) -> None:
    """Test fan speeds documented in eufy manuals are exposed by model mappings."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code=model_code,
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

    assert robovac.model_details.commands[RobovacCommand.FAN_SPEED]["values"] == expected_values
