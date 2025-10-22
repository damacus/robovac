"""Tests for T2080 command mappings and DPS codes."""

import pytest
from typing import Any
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2080_robovac() -> RoboVac:
    """Create a mock T2080 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2080",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2080_fan_speed_command_values(mock_t2080_robovac) -> None:
    """Test T2080 FAN_SPEED value mapping."""
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2080_mop_level_command_values(mock_t2080_robovac) -> None:
    """Test T2080 MOP_LEVEL value mapping."""
    # Device uses symmetric values: low, middle, normal, strong
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.MOP_LEVEL, "low") == "low"
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.MOP_LEVEL, "middle") == "middle"
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.MOP_LEVEL, "normal") == "normal"
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.MOP_LEVEL, "strong") == "strong"
    assert mock_t2080_robovac.getRoboVacCommandValue(RobovacCommand.MOP_LEVEL, "unknown") == "unknown"


def test_t2080_mop_level_human_readable(mock_t2080_robovac) -> None:
    """Test T2080 MOP_LEVEL human-readable value conversion."""
    # Symmetric mapping for device values
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(RobovacCommand.MOP_LEVEL, "low") == "low"
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(RobovacCommand.MOP_LEVEL, "middle") == "middle"
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(RobovacCommand.MOP_LEVEL, "normal") == "normal"
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(RobovacCommand.MOP_LEVEL, "strong") == "strong"


def test_t2080_status_human_readable(mock_t2080_robovac) -> None:
    """Test T2080 STATUS human-readable value conversion for key states."""
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "CAoAEAUyAggB") == "Paused"
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "CgoAEAkaAggBMgA=") == "Auto Cleaning"
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "BhADGgIIAQ==") == "Completed"
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "BBADGgA=") == "Charging"
