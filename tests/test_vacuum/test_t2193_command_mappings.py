"""Tests for T2193 (LR30 Hybrid) command mappings."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2193_robovac() -> RoboVac:
    """Create a mock T2193 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2193",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2193_start_pause_values(mock_t2193_robovac) -> None:
    """Test T2193 START_PAUSE maps 'start' to True and 'pause' to False.

    GH-336: LR30 Hybrid controls do not work. START_PAUSE needs
    boolean values for the toggle to work correctly.
    """
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t2193_status_human_readable(mock_t2193_robovac) -> None:
    """Test T2193 STATUS values are mapped to human-readable strings.

    GH-336: LR30 Hybrid needs STATUS values for proper state reporting.
    """
    assert mock_t2193_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Running") == "Running"
    assert mock_t2193_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Charging") == "Charging"
    assert mock_t2193_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "completed") == "Completed"
    assert mock_t2193_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "standby") == "Standby"
    assert mock_t2193_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Sleeping") == "Sleeping"
    assert mock_t2193_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "Recharge") == "Returning to Dock"


def test_t2193_mode_command_values(mock_t2193_robovac) -> None:
    """Test T2193 MODE command value mappings."""
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"


def test_t2193_fan_speed_command_values(mock_t2193_robovac) -> None:
    """Test T2193 FAN_SPEED value mapping."""
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2193_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
