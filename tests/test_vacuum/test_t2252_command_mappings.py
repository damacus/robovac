"""Tests for T2252 command mappings and DPS codes."""

import pytest
from typing import Any
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2252_robovac() -> RoboVac:
    """Create a mock T2252 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2252",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2252_mode_command_values(mock_t2252_robovac) -> None:
    """Test T2252 MODE command value mappings."""
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"

    # Unknown returns as-is
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2252_mode_case_insensitive(mock_t2252_robovac) -> None:
    """Test T2252 MODE command accepts case-insensitive values via getRoboVacHumanReadableValue."""
    # Case-insensitive matching should work for device responses
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.MODE, "Auto") == "Auto"
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.MODE, "AUTO") == "Auto"


def test_t2252_fan_speed_command_values(mock_t2252_robovac) -> None:
    """Test T2252 FAN_SPEED value mapping."""
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost_iq") == "Boost_IQ"
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2252_error_code_mapping(mock_t2252_robovac) -> None:
    """Test T2252 error code 0 maps to 'No error'."""
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.ERROR, "0") == "No error"


def test_t2252_status_human_readable(mock_t2252_robovac) -> None:
    """Test T2252 STATUS values are mapped to human-readable strings.

    GH-196: The G30 Verge reports status values like 'Charging', 'completed',
    'Running' etc. which should be mapped to human-readable names.
    """
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Charging") == "Charging"
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "completed") == "Completed"
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Running") == "Running"
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "standby") == "Standby"
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Sleeping") == "Sleeping"
    assert mock_t2252_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "recharge_needed") == "Recharge needed"


def test_t2252_start_pause_values(mock_t2252_robovac) -> None:
    """Test T2252 START_PAUSE maps 'start' to True and 'pause' to False.

    GH-196: G30 Verge GUI control commands not working. START_PAUSE needs
    boolean values for the toggle to work correctly.
    """
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t2252_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t2252_model_has_commands(mock_t2252_robovac) -> None:
    """Test that T2252 model has required commands defined."""
    commands = mock_t2252_robovac.model_details.commands

    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands
