"""Tests for T2258 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import (
    RoboVacEntityFeature,
    RobovacCommand,
)


@pytest.fixture
def mock_t2258_robovac() -> RoboVac:
    """Create a mock T2258 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        return RoboVac(
            model_code="T2258",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )


def test_t2258_uses_documented_cleaning_modes(mock_t2258_robovac) -> None:
    """Test T2258 only exposes documented Auto and Spot modes."""
    values = mock_t2258_robovac.model_details.commands[RobovacCommand.MODE]["values"]

    assert values == {
        "auto": "Auto",
        "spot": "Spot",
    }
    assert mock_t2258_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "Auto"
    assert mock_t2258_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"


def test_t2258_excludes_undocumented_mode_values(mock_t2258_robovac) -> None:
    """Test T2258 does not expose undocumented G-series cleaning modes."""
    values = mock_t2258_robovac.model_details.commands[RobovacCommand.MODE]["values"]

    assert "small_room" not in values
    assert "edge" not in values
    assert "nosweep" not in values


def test_t2258_uses_documented_suction_levels(mock_t2258_robovac) -> None:
    """Test T2258 exposes documented suction levels."""
    values = mock_t2258_robovac.model_details.commands[RobovacCommand.FAN_SPEED]["values"]

    assert values == {
        "quiet": "Quiet",
        "standard": "Standard",
        "turbo": "Turbo",
        "max": "Max",
    }
    assert mock_t2258_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2258_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2258_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2258_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert "boost_iq" not in values


def test_t2258_exposes_boost_iq_as_separate_setting(mock_t2258_robovac) -> None:
    """Test T2258 follows documented BoostIQ feature behavior."""
    assert mock_t2258_robovac.model_details.robovac_features & RoboVacEntityFeature.BOOST_IQ


def test_t2258_does_not_expose_direction_command(mock_t2258_robovac) -> None:
    """Test T2258 does not expose undocumented manual direction controls."""
    assert RobovacCommand.DIRECTION not in mock_t2258_robovac.model_details.commands


def test_t2258_model_has_basic_commands(mock_t2258_robovac) -> None:
    """Test that T2258 model has required basic commands defined."""
    commands = mock_t2258_robovac.model_details.commands

    assert RobovacCommand.START_PAUSE in commands
    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands


def test_t2258_does_not_override_default_boost_iq_dps_code(mock_t2258_robovac) -> None:
    """Test T2258 relies on the default BoostIQ DPS fallback."""
    assert mock_t2258_robovac.getDpsCodes().get("BOOST_IQ") is None
