"""Tests for T2277 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2277_robovac():
    """Create a mock T2277 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2277",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2277_dps_codes(mock_t2277_robovac):
    """Test that T2277 has the correct DPS codes."""
    dps_codes = mock_t2277_robovac.getDpsCodes()

    assert dps_codes["MODE"] == "152"
    assert dps_codes["STATUS"] == "173"
    assert dps_codes["RETURN_HOME"] == "153"
    assert dps_codes["FAN_SPEED"] == "154"
    assert dps_codes["LOCATE"] == "153"
    assert dps_codes["BATTERY_LEVEL"] == "172"
    assert dps_codes["ERROR_CODE"] == "169"


def test_t2277_mode_command_values(mock_t2277_robovac):
    """Test T2277 MODE command value mappings."""
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "AA=="
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause") == "AggN"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "AggG"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "BBoCCAE="
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "AggO"

    # Unknown returns as-is
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2277_return_home_command_values(mock_t2277_robovac):
    """Test T2277 RETURN_HOME value mapping."""
    assert (
        mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return_home")
        == "AggB"
    )
    assert (
        mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "unknown")
        == "unknown"
    )


def test_t2277_fan_speed_command_values(mock_t2277_robovac):
    """Test T2277 FAN_SPEED value mapping."""
    assert (
        mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "fan_speed")
        == "AgkBCgIKAQoDCgEKBAoB"
    )
    assert (
        mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown")
        == "unknown"
    )


def test_t2277_locate_command_values(mock_t2277_robovac):
    """Test T2277 LOCATE value mapping."""
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "locate") == "AggC"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "unknown") == "unknown"


def test_t2277_command_codes(mock_t2277_robovac):
    """Test that T2277 command codes are correctly defined on model."""
    commands = mock_t2277_robovac.model_details.commands

    assert commands[RobovacCommand.MODE]["code"] == 152
    assert commands[RobovacCommand.STATUS]["code"] == 173
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 153
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 154
    assert commands[RobovacCommand.LOCATE]["code"] == 153
    assert commands[RobovacCommand.BATTERY]["code"] == 172
    assert commands[RobovacCommand.ERROR]["code"] == 169
