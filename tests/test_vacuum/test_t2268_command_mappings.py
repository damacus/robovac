"""Tests for T2268 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2268_robovac() -> RoboVac:
    """Create a mock T2268 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2268",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2268_dps_codes(mock_t2268_robovac: RoboVac) -> None:
    """Test that T2268 has the correct DPS codes."""
    dps_codes = mock_t2268_robovac.getDpsCodes()

    assert dps_codes["START_PAUSE"] == "2"
    assert dps_codes["DIRECTION"] == "3"
    assert dps_codes["MODE"] == "5"
    assert dps_codes["STATUS"] == "15"
    assert dps_codes["RETURN_HOME"] == "101"
    assert dps_codes["FAN_SPEED"] == "102"
    assert dps_codes["LOCATE"] == "103"
    assert dps_codes["BATTERY_LEVEL"] == "104"
    assert dps_codes["ERROR_CODE"] == "106"


def test_t2268_mode_command_values(mock_t2268_robovac: RoboVac) -> None:
    """Test T2268 MODE command value mappings."""
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"

    # Unknown returns as-is
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2268_fan_speed_command_values(mock_t2268_robovac: RoboVac) -> None:
    """Test T2268 FAN_SPEED command value mappings."""
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "pure") == "Pure"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"

    # Unknown returns as-is
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2268_direction_command_values(mock_t2268_robovac: RoboVac) -> None:
    """Test T2268 DIRECTION command value mappings."""
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "forward") == "forward"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "back") == "back"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "left") == "left"
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "right") == "right"

    # Unknown returns as-is
    assert mock_t2268_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "unknown") == "unknown"


def test_t2268_command_codes(mock_t2268_robovac: RoboVac) -> None:
    """Test that T2268 command codes are correctly defined on model."""
    commands = mock_t2268_robovac.model_details.commands

    assert commands[RobovacCommand.START_PAUSE]["code"] == 2
    assert commands[RobovacCommand.DIRECTION]["code"] == 3
    assert commands[RobovacCommand.MODE]["code"] == 5
    assert commands[RobovacCommand.STATUS]["code"] == 15
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 101
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 102
    assert commands[RobovacCommand.LOCATE]["code"] == 103
    assert commands[RobovacCommand.BATTERY]["code"] == 104
    assert commands[RobovacCommand.ERROR]["code"] == 106
