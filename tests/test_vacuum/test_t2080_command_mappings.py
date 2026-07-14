"""Tests for T2080 command mappings and DPS codes."""

import importlib
import pytest
import sys
from typing import Any
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2080_robovac() -> RoboVac:
    """Create a mock T2080 RoboVac instance for testing."""
    # Force reload of modules to avoid caching issues
    modules_to_reload = [
        "custom_components.robovac.vacuums.base",
        "custom_components.robovac.vacuums.T2080",
        "custom_components.robovac.vacuums",
        "custom_components.robovac.robovac",
    ]
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

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


def test_t2080_mop_level_command_exists(mock_t2080_robovac) -> None:
    """Test that T2080 model has MOP_LEVEL command defined."""
    commands = mock_t2080_robovac.model_details.commands

    # Verify MOP_LEVEL command exists
    assert RobovacCommand.MOP_LEVEL in commands, "MOP_LEVEL command should be defined in T2080"

    # Verify DPS code from issue #105 debug logs
    assert commands[RobovacCommand.MOP_LEVEL]["code"] == 10, "MOP_LEVEL should use DPS code 10"

    # Verify all mop level values are defined
    mop_values = commands[RobovacCommand.MOP_LEVEL]["values"]
    assert "low" in mop_values, "MOP_LEVEL should support 'low'"
    assert "middle" in mop_values, "MOP_LEVEL should support 'middle'"
    assert "normal" in mop_values, "MOP_LEVEL should support 'normal'"
    assert "strong" in mop_values, "MOP_LEVEL should support 'strong'"

    # Verify symmetric string mappings
    assert mop_values["low"] == "low"
    assert mop_values["middle"] == "middle"
    assert mop_values["normal"] == "normal"
    assert mop_values["strong"] == "strong"
