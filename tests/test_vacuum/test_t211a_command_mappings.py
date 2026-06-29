"""Tests for T211A (Omni C28) command mappings and registration."""

from unittest.mock import patch

import pytest

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums import ROBOVAC_MODELS
from custom_components.robovac.vacuums.T2280 import T2280
from custom_components.robovac.vacuums.base import RobovacCommand


def test_t211a_registered_in_robovac_models() -> None:
    """Test T211A is registered in ROBOVAC_MODELS."""
    assert ROBOVAC_MODELS["T211A"].commands == T2280.commands


@pytest.fixture
def mock_t211a_robovac() -> RoboVac:
    """Create a mock T211A RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T211A",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t211a_mode_command_values(mock_t211a_robovac: RoboVac) -> None:
    """Test T211A MODE command uses the Omni C-series values."""
    assert (
        mock_t211a_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto")
        == "BBoCCAE="
    )
    assert (
        mock_t211a_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause")
        == "AggN"
    )


def test_t211a_model_has_commands(mock_t211a_robovac: RoboVac) -> None:
    """Test that T211A model has required commands defined."""
    commands = mock_t211a_robovac.model_details.commands

    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands
