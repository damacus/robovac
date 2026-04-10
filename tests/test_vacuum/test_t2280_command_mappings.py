"""Tests for T2280 (C20 Hybrid SES) command mappings and registration."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums import ROBOVAC_MODELS
from custom_components.robovac.vacuums.base import RobovacCommand


def test_t2280_registered_in_robovac_models() -> None:
    """Test T2280 is registered in ROBOVAC_MODELS dict.

    GH-158: C20 not showing under integration because T2280 exists
    as a model file but was not registered in the models dictionary.
    """
    assert "T2280" in ROBOVAC_MODELS


@pytest.fixture
def mock_t2280_robovac() -> RoboVac:
    """Create a mock T2280 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2280",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2280_mode_command_values(mock_t2280_robovac) -> None:
    """Test T2280 MODE command sends base64 encoded values."""
    assert mock_t2280_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "BBoCCAE="
    assert mock_t2280_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause") == "AggN"


def test_t2280_model_has_commands(mock_t2280_robovac) -> None:
    """Test that T2280 model has required commands defined."""
    commands = mock_t2280_robovac.model_details.commands

    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands
