"""Tests for T2276 command mappings and DPS codes."""

import pytest
from typing import Any
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2276_robovac() -> RoboVac:
    """Create a mock T2276 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2276",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2276_dps_codes(mock_t2276_robovac) -> None:
    """Test that T2276 has the correct DPS codes.
    
    getDpsCodes() extracts codes from the commands dictionary.
    T2276 uses standard Tuya DPS codes for status (15, 104, 106)
    and custom command codes for control (152, 153, 154).
    """
    dps_codes = mock_t2276_robovac.getDpsCodes()

    # Codes extracted from commands dictionary
    assert dps_codes["MODE"] == "152"
    assert dps_codes["STATUS"] == "15"  # Standard Tuya code
    assert dps_codes["RETURN_HOME"] == "153"
    assert dps_codes["FAN_SPEED"] == "154"
    assert dps_codes["LOCATE"] == "153"
    assert dps_codes["BATTERY_LEVEL"] == "104"  # Standard Tuya code
    assert dps_codes["ERROR_CODE"] == "106"  # Standard Tuya code


def test_t2276_mode_command_values(mock_t2276_robovac) -> None:
    """Test T2276 MODE command value mappings."""
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "AA=="
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause") == "AggN"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "AggG"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "BBoCCAE="
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "AggO"

    # Unknown returns as-is
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2276_return_home_command_values(mock_t2276_robovac) -> None:
    """Test T2276 RETURN_HOME value mapping."""
    assert (
        mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return_home")
        == "AggB"
    )
    assert (
        mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "unknown")
        == "unknown"
    )


def test_t2276_fan_speed_command_values(mock_t2276_robovac) -> None:
    """Test T2276 FAN_SPEED value mapping."""
    assert (
        mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "fan_speed")
        == "AgkBCgIKAQoDCgEKBAoB"
    )
    assert (
        mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown")
        == "unknown"
    )


def test_t2276_locate_command_values(mock_t2276_robovac) -> None:
    """Test T2276 LOCATE value mapping."""
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "locate") == "AggC"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "unknown") == "unknown"


def test_t2276_command_codes(mock_t2276_robovac) -> None:
    """Test that T2276 command codes are correctly defined on model.
    
    T2276 uses custom command codes for sending control commands,
    but standard DPS codes for reading status.
    """
    commands = mock_t2276_robovac.model_details.commands

    # Custom command codes for control
    assert commands[RobovacCommand.MODE]["code"] == 152
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 153
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 154
    assert commands[RobovacCommand.LOCATE]["code"] == 153
    
    # Standard DPS codes for status reading
    assert commands[RobovacCommand.STATUS]["code"] == 15
    assert commands[RobovacCommand.BATTERY]["code"] == 104
    assert commands[RobovacCommand.ERROR]["code"] == 106
