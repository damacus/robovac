"""Tests for T2276 command mappings and DPS codes.

The T2276 (Eufy Clean X8 Pro SES) uses protocol 3.5 with standard Tuya DPS
codes (1-135), not the protobuf-encoded DPS 152-173 previously configured.
"""

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
    """Test that T2276 has the correct DPS codes (protocol 3.5, standard Tuya)."""
    dps_codes = mock_t2276_robovac.getDpsCodes()

    assert dps_codes["MODE"] == "5"
    assert dps_codes["STATUS"] == "15"
    assert dps_codes["RETURN_HOME"] == "101"
    assert dps_codes["FAN_SPEED"] == "102"
    assert dps_codes["LOCATE"] == "103"
    assert dps_codes["BATTERY_LEVEL"] == "104"
    assert dps_codes["ERROR_CODE"] == "106"
    assert dps_codes["DO_NOT_DISTURB"] == "107"
    assert dps_codes["CLEANING_TIME"] == "109"
    assert dps_codes["CLEANING_AREA"] == "110"
    assert dps_codes["BOOST_IQ"] == "118"


def test_t2276_mode_command_values(mock_t2276_robovac) -> None:
    """Test T2276 MODE command value mappings.

    Note: T2276 uses lowercase "auto" unlike T2128's "Auto",
    confirmed via local protocol 3.5 packet capture.
    """
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "auto"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"

    # Unknown returns as-is
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2276_start_pause_command_values(mock_t2276_robovac) -> None:
    """Test T2276 START_PAUSE value mapping (boolean DPS 2)."""
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t2276_return_home_command_values(mock_t2276_robovac) -> None:
    """Test T2276 RETURN_HOME value mapping (boolean DPS 101)."""
    # Boolean DPS — getRoboVacCommandValue returns the command as-is for bool DPS
    assert (
        mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return")
        == "return"
    )


def test_t2276_fan_speed_command_values(mock_t2276_robovac) -> None:
    """Test T2276 FAN_SPEED value mapping."""
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "pure") == "Quiet"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost") == "Boost"

    # Unknown returns as-is
    assert mock_t2276_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2276_command_codes(mock_t2276_robovac) -> None:
    """Test that T2276 command codes are correctly defined on model."""
    commands = mock_t2276_robovac.model_details.commands

    assert commands[RobovacCommand.START_PAUSE]["code"] == 2
    assert commands[RobovacCommand.MODE]["code"] == 5
    assert commands[RobovacCommand.STATUS]["code"] == 15
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 101
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 102
    assert commands[RobovacCommand.LOCATE]["code"] == 103
    assert commands[RobovacCommand.BATTERY]["code"] == 104
    assert commands[RobovacCommand.ERROR]["code"] == 106
    assert commands[RobovacCommand.DO_NOT_DISTURB]["code"] == 107
    assert commands[RobovacCommand.CLEANING_TIME]["code"] == 109
    assert commands[RobovacCommand.CLEANING_AREA]["code"] == 110
    assert commands[RobovacCommand.BOOST_IQ]["code"] == 118
