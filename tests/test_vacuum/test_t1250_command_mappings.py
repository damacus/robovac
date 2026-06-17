"""Tests for T1250 command mappings and DPS codes."""

from typing import Any
from unittest.mock import patch

import pytest

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t1250_robovac() -> RoboVac:
    """Create a mock T1250 RoboVac instance for mapping tests."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        return RoboVac(
            model_code="T1250",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )


def _command_code(command: Any) -> str | None:
    """Return a command DPS code as a string."""
    if isinstance(command, dict) and "code" in command:
        return str(command["code"])
    if not isinstance(command, dict):
        return str(command)
    return None


def test_t1250_model_has_required_commands(mock_t1250_robovac: RoboVac) -> None:
    """Test that T1250 exposes required command mappings."""
    commands = mock_t1250_robovac.model_details.commands

    assert RobovacCommand.START_PAUSE in commands
    assert RobovacCommand.DIRECTION in commands
    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands


@pytest.mark.parametrize(
    ("command", "expected_code"),
    (
        (RobovacCommand.START_PAUSE, "2"),
        (RobovacCommand.DIRECTION, "3"),
        (RobovacCommand.STATUS, "15"),
        (RobovacCommand.RETURN_HOME, "101"),
        (RobovacCommand.LOCATE, "103"),
        (RobovacCommand.BATTERY, "104"),
        (RobovacCommand.ERROR, "106"),
    ),
)
def test_t1250_command_dps_codes(
    mock_t1250_robovac: RoboVac,
    command: RobovacCommand,
    expected_code: str,
) -> None:
    """Test T1250 command DPS codes."""
    commands = mock_t1250_robovac.model_details.commands

    assert _command_code(commands[command]) == expected_code


def test_t1250_start_pause_values(mock_t1250_robovac: RoboVac) -> None:
    """Test T1250 START_PAUSE maps start/pause to booleans."""
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t1250_direction_command_values(mock_t1250_robovac: RoboVac) -> None:
    """Test T1250 DIRECTION command value mappings."""
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "forward") == "Forward"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "back") == "Back"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "left") == "Left"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "right") == "Right"


def test_t1250_mode_command_values(mock_t1250_robovac: RoboVac) -> None:
    """Test T1250 MODE command value mappings."""
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"


def test_t1250_fan_speed_command_values(mock_t1250_robovac: RoboVac) -> None:
    """Test T1250 FAN_SPEED command value mappings."""
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert mock_t1250_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost_iq") == "Boost_IQ"
