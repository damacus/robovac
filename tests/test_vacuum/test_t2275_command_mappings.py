"""Tests for T2275 command mappings and DPS codes."""

import pytest
from typing import Any
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2275_robovac() -> RoboVac:
    """Create a mock T2275 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2275",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2275_dps_codes(mock_t2275_robovac) -> None:
    """Test that T2275 has the correct DPS codes."""
    dps_codes = mock_t2275_robovac.getDpsCodes()

    assert dps_codes["MODE"] == "152"
    assert dps_codes["STATUS"] == "173"
    assert dps_codes["RETURN_HOME"] == "153"
    assert dps_codes["CLEAN_PARAM"] == "154"
    assert dps_codes["FAN_SPEED"] == "158"
    assert dps_codes["LOCATE"] == "153"
    assert dps_codes["BATTERY_LEVEL"] == "172"
    assert dps_codes["ERROR_CODE"] == "169"


def test_t2275_mode_command_values(mock_t2275_robovac) -> None:
    """Test T2275 MODE command value mappings."""
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "AA=="
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause") == "AggN"
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "AggG"
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "BBoCCAE="
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "AggO"

    # Unknown returns as-is
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2275_return_home_command_values(mock_t2275_robovac) -> None:
    """Test T2275 RETURN_HOME value mapping."""
    assert (
        mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return_home")
        == "AggB"
    )
    assert (
        mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "unknown")
        == "unknown"
    )


def test_t2275_fan_speed_command_values(mock_t2275_robovac) -> None:
    """Test T2275 FAN_SPEED maps HA selections to direct fan speed values."""
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert (
        mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown")
        == "unknown"
    )


def test_t2275_fan_speed_list_exposes_real_speeds(mock_t2275_robovac) -> None:
    """Test T2275 fan speed list does not expose the clean-param placeholder."""
    assert mock_t2275_robovac.getFanSpeeds() == ["Quiet", "Standard", "Turbo", "Max"]


def test_t2275_locate_command_values(mock_t2275_robovac) -> None:
    """Test T2275 LOCATE value mapping."""
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "locate") == "AggC"
    assert mock_t2275_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "unknown") == "unknown"


def test_t2275_command_codes(mock_t2275_robovac) -> None:
    """Test that T2275 command codes are correctly defined on model."""
    commands = mock_t2275_robovac.model_details.commands

    assert commands[RobovacCommand.MODE]["code"] == 152
    assert commands[RobovacCommand.STATUS]["code"] == 173
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 153
    assert commands[RobovacCommand.CLEAN_PARAM]["code"] == 154
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 158
    assert commands[RobovacCommand.LOCATE]["code"] == 153
    assert commands[RobovacCommand.BATTERY]["code"] == 172
    assert commands[RobovacCommand.ERROR]["code"] == 169
