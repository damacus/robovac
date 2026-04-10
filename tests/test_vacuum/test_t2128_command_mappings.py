"""Tests for T2128 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2128_robovac() -> RoboVac:
    """Create a mock T2128 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2128",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2128_start_pause_values(mock_t2128_robovac) -> None:
    """Test T2128 START_PAUSE maps 'start' to True and 'pause' to False.

    GH-303: T2128 (15C MAX) uses boolean toggle for START_PAUSE DPS code 2.
    Setting mode to 'auto' alone does not start the vacuum.
    """
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t2128_mode_command_values(mock_t2128_robovac) -> None:
    """Test T2128 MODE command value mappings."""
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2128_fan_speed_command_values(mock_t2128_robovac) -> None:
    """Test T2128 FAN_SPEED value mapping."""
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "no_suction") == "No_suction"
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost_iq") == "Boost_IQ"
    assert mock_t2128_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"


def test_t2128_model_has_commands(mock_t2128_robovac) -> None:
    """Test that T2128 model has required commands defined."""
    commands = mock_t2128_robovac.model_details.commands

    assert RobovacCommand.START_PAUSE in commands
    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands
