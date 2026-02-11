"""Tests for T2194 (L35 Hybrid) command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2194_robovac() -> RoboVac:
    """Create a mock T2194 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2194",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2194_start_pause_values(mock_t2194_robovac) -> None:
    """Test T2194 START_PAUSE maps 'start' to True and 'pause' to False.

    GH-309: L35 Hybrid only spot cleans when start command sent. The vacuum
    needs START_PAUSE boolean toggle along with MODE to start correctly.
    """
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t2194_status_human_readable(mock_t2194_robovac) -> None:
    """Test T2194 STATUS values include 'completed' and 'Charging'.

    GH-309: Device reports 'completed' and 'Charging' statuses that were
    missing from the values dict.
    """
    assert mock_t2194_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Running") == "Running"
    assert mock_t2194_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "completed") == "Completed"
    assert mock_t2194_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Charging") == "Charging"
    assert mock_t2194_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "standby") == "Standby"
    assert mock_t2194_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Sleeping") == "Sleeping"
    assert mock_t2194_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "recharge_needed") == "Recharge needed"


def test_t2194_fan_speed_dps_code(mock_t2194_robovac) -> None:
    """Test T2194 FAN_SPEED uses DPS code 130 (not 102).

    GH-333: Fan speeds off by one on L35 Hybrid. Device DPS dump shows
    fan speed at code 130, not 102 as originally defined.
    """
    dps_codes = mock_t2194_robovac.getDpsCodes()
    assert dps_codes["FAN_SPEED"] == "130"


def test_t2194_fan_speed_command_values(mock_t2194_robovac) -> None:
    """Test T2194 FAN_SPEED value mapping."""
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"


def test_t2194_mode_command_values(mock_t2194_robovac) -> None:
    """Test T2194 MODE command value mappings."""
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2194_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"


def test_t2194_model_has_commands(mock_t2194_robovac) -> None:
    """Test that T2194 model has required commands defined."""
    commands = mock_t2194_robovac.model_details.commands

    assert RobovacCommand.START_PAUSE in commands
    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands
