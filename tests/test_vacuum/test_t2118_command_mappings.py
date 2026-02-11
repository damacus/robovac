"""Tests for T2118 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2118_robovac() -> RoboVac:
    """Create a mock T2118 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2118",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2118_mode_command_values(mock_t2118_robovac) -> None:
    """Test T2118 MODE command value mappings."""
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2118_fan_speed_command_values(mock_t2118_robovac) -> None:
    """Test T2118 FAN_SPEED value mapping."""
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "no_suction") == "No_suction"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost_iq") == "Boost_IQ"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2118_status_human_readable(mock_t2118_robovac) -> None:
    """Test T2118 STATUS values are mapped to human-readable strings.

    GH-185: The vacuum reports status values like 'completed', 'Charging',
    'Running' etc. which should be mapped to human-readable names.
    """
    assert mock_t2118_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "completed") == "Completed"
    assert mock_t2118_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Charging") == "Charging"
    assert mock_t2118_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Running") == "Running"
    assert mock_t2118_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "standby") == "Standby"
    assert mock_t2118_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Sleeping") == "Sleeping"
    assert mock_t2118_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "recharge_needed") == "Recharge needed"


def test_t2118_error_human_readable(mock_t2118_robovac) -> None:
    """Test T2118 ERROR value '0' maps to 'No error'.

    GH-185: The vacuum reports error code '0' which should map to 'No error'.
    """
    assert mock_t2118_robovac.getRoboVacHumanReadableValue(RobovacCommand.ERROR, "0") == "No error"


def test_t2118_mode_human_readable_nosweep(mock_t2118_robovac) -> None:
    """Test T2118 MODE 'Nosweep' reverse lookup works.

    GH-185: The vacuum reports mode 'Nosweep' which should be found via
    case-insensitive reverse lookup on the existing MODE values dict.
    """
    assert mock_t2118_robovac.getRoboVacHumanReadableValue(RobovacCommand.MODE, "Nosweep") == "Nosweep"


def test_t2118_start_pause_values(mock_t2118_robovac) -> None:
    """Test T2118 START_PAUSE maps 'start' to True and 'pause' to False.

    GH-303: Older models use boolean toggle for START_PAUSE DPS code 2.
    """
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t2118_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t2118_model_has_commands(mock_t2118_robovac) -> None:
    """Test that T2118 model has required commands defined."""
    commands = mock_t2118_robovac.model_details.commands

    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands
