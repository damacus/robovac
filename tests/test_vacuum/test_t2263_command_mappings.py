"""Tests for T2263 (L70 Max) command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2263_robovac() -> RoboVac:
    """Create a mock T2263 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2263",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2263_dps_codes(mock_t2263_robovac: RoboVac) -> None:
    """Test that T2263 has the expected DPS codes."""
    dps_codes = mock_t2263_robovac.getDpsCodes()

    assert dps_codes["START_PAUSE"] == "2"
    assert dps_codes["DIRECTION"] == "3"
    assert dps_codes["MODE"] == "5"
    assert dps_codes["STATUS"] == "15"
    assert dps_codes["RETURN_HOME"] == "101"
    assert dps_codes["FAN_SPEED"] == "102"
    assert dps_codes["LOCATE"] == "103"
    assert dps_codes["BATTERY_LEVEL"] == "104"
    assert dps_codes["ERROR_CODE"] == "106"


def test_t2263_start_pause_command_values(mock_t2263_robovac: RoboVac) -> None:
    """Test T2263 START_PAUSE maps 'start' to True and 'pause' to False."""
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t2263_direction_command_values(mock_t2263_robovac: RoboVac) -> None:
    """Test T2263 DIRECTION command value mappings."""
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "forward") == "Forward"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "back") == "Back"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "left") == "Left"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "right") == "Right"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "unknown") == "unknown"


def test_t2263_mode_command_values(mock_t2263_robovac: RoboVac) -> None:
    """Test T2263 MODE command value mappings."""
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"

    # Unknown returns as-is
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2263_mode_case_insensitive(mock_t2263_robovac: RoboVac) -> None:
    """Test T2263 MODE command accepts case-insensitive values via getRoboVacHumanReadableValue."""
    # Case-insensitive matching should work for device responses
    assert mock_t2263_robovac.getRoboVacHumanReadableValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2263_robovac.getRoboVacHumanReadableValue(RobovacCommand.MODE, "Auto") == "Auto"
    assert mock_t2263_robovac.getRoboVacHumanReadableValue(RobovacCommand.MODE, "AUTO") == "Auto"


def test_t2263_return_home_command_values(mock_t2263_robovac: RoboVac) -> None:
    """Test T2263 RETURN_HOME maps 'return' to True."""
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return") is True


def test_t2263_fan_speed_command_values(mock_t2263_robovac: RoboVac) -> None:
    """Test T2263 FAN_SPEED value mapping."""
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert mock_t2263_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"
    assert mock_t2263_robovac.getFanSpeeds() == ["Quiet", "Standard", "Turbo", "Max"]


def test_t2263_model_has_commands(mock_t2263_robovac: RoboVac) -> None:
    """Test that T2263 model has required commands defined."""
    commands = mock_t2263_robovac.model_details.commands

    assert RobovacCommand.START_PAUSE in commands
    assert RobovacCommand.DIRECTION in commands
    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands
