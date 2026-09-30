"""Tests for T2257 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2257_robovac() -> RoboVac:
    """Create a mock T2257 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        return RoboVac(
            model_code="T2257",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )


def test_t2257_reads_status_from_dps_15(mock_t2257_robovac) -> None:
    """Test T2257 takes status directly from DPS 15, unlike T2258.

    T2258 reads status from DPS 2 because DPS 15 is stuck on that model. On a
    live T2257 DPS 15 correctly reports real status strings (observed:
    'completed' while docked), so no DPS 2 workaround is needed here.
    """
    status = mock_t2257_robovac.model_details.commands[RobovacCommand.STATUS]

    assert status["code"] == 15


def test_t2257_uses_confirmed_cleaning_modes(mock_t2257_robovac) -> None:
    """Test T2257 exposes the wider G-series cleaning modes.

    Only 'nosweep' has been confirmed live against the device; the others
    follow the documented G-series convention but are unverified.
    """
    values = mock_t2257_robovac.model_details.commands[RobovacCommand.MODE]["values"]

    assert values == {
        "auto": "Auto",
        "small_room": "SmallRoom",
        "spot": "Spot",
        "edge": "Edge",
        "nosweep": "Nosweep",
    }
    assert mock_t2257_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"


def test_t2257_uses_confirmed_suction_levels(mock_t2257_robovac) -> None:
    """Test T2257 exposes suction levels without quiet or boost_iq.

    Only 'max' has been confirmed live against the device; quiet and boost_iq
    were omitted since they were not observed and this model tier may not
    support them (unlike the Hybrid variant T2258).
    """
    values = mock_t2257_robovac.model_details.commands[RobovacCommand.FAN_SPEED]["values"]

    assert values == {
        "standard": "Standard",
        "turbo": "Turbo",
        "max": "Max",
    }
    assert mock_t2257_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"


def test_t2257_exposes_direction_command(mock_t2257_robovac) -> None:
    """Test T2257 exposes manual direction controls, unlike T2258."""
    assert RobovacCommand.DIRECTION in mock_t2257_robovac.model_details.commands


def test_t2257_model_has_basic_commands(mock_t2257_robovac) -> None:
    """Test that T2257 model has required basic commands defined."""
    commands = mock_t2257_robovac.model_details.commands

    assert RobovacCommand.START_PAUSE in commands
    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands
    assert RobovacCommand.CLEANING_AREA in commands
    assert RobovacCommand.CLEANING_TIME in commands


def test_t2257_battery_code(mock_t2257_robovac) -> None:
    """Test T2257 reads battery from the confirmed DPS code 104."""
    battery = mock_t2257_robovac.model_details.commands[RobovacCommand.BATTERY]

    assert battery["code"] == 104


def test_t2257_error_code(mock_t2257_robovac) -> None:
    """Test T2257 reads error state from the confirmed DPS code 106."""
    error = mock_t2257_robovac.model_details.commands[RobovacCommand.ERROR]

    assert error["code"] == 106


def test_t2257_cleaning_stats_codes(mock_t2257_robovac) -> None:
    """Test T2257 reads cleaning area and time from confirmed DPS codes."""
    commands = mock_t2257_robovac.model_details.commands

    assert commands[RobovacCommand.CLEANING_AREA]["code"] == 109
    assert commands[RobovacCommand.CLEANING_TIME]["code"] == 110
