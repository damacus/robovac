"""Tests for T2267 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from homeassistant.components.vacuum import VacuumActivity

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2267_robovac() -> RoboVac:
    """Create a mock T2267 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2267",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2267_dps_codes(mock_t2267_robovac: RoboVac) -> None:
    """Test that T2267 has the correct DPS codes."""
    dps_codes = mock_t2267_robovac.getDpsCodes()

    assert dps_codes["MODE"] == "152"
    assert dps_codes["STATUS"] == "153"
    assert dps_codes["DIRECTION"] == "155"
    # START_PAUSE uses MODE command (code 152) for protobuf models
    assert dps_codes["START_PAUSE"] == "152"
    assert dps_codes["DO_NOT_DISTURB"] == "157"
    assert dps_codes["FAN_SPEED"] == "158"
    assert dps_codes["BOOST_IQ"] == "159"
    assert dps_codes["LOCATE"] == "160"
    assert dps_codes["BATTERY_LEVEL"] == "163"
    assert dps_codes["CONSUMABLES"] == "168"
    # RETURN_HOME uses MODE command (code 152) for protobuf models
    assert dps_codes["RETURN_HOME"] == "152"
    assert dps_codes["ERROR_CODE"] == "177"


def test_t2267_mode_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 MODE command value mappings."""
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "BBoCCAE="
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause") == "AggN"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "AA=="
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "return") == "AggG"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "AggO"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2267_fan_speed_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 FAN_SPEED command value mappings."""
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost_iq") == "Boost_IQ"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2267_direction_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 DIRECTION command value mappings."""
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "brake") == "brake"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "forward") == "forward"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "back") == "back"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "left") == "left"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "right") == "right"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "unknown") == "unknown"


def test_t2267_start_pause_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 START_PAUSE command value mappings.

    START_PAUSE uses the MODE DPS code (152) with protobuf-encoded values:
    - "AggN" encodes ModeCtrlRequest.Method.PAUSE_TASK (13)
    - "AggO" encodes ModeCtrlRequest.Method.RESUME_TASK (14)
    """
    # Pause command - encodes PAUSE_TASK (method=13)
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") == "AggN"

    # Resume command - encodes RESUME_TASK (method=14)
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "resume") == "AggO"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "unknown") == "unknown"


def test_t2267_return_home_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 RETURN_HOME command value mappings.

    RETURN_HOME uses the MODE DPS code (152) with protobuf-encoded value:
    - "AggG" encodes ModeCtrlRequest.Method.START_GOHOME (6)
    """
    # Return home command - encodes START_GOHOME (method=6)
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return") == "AggG"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "unknown") == "unknown"


def test_t2267_stop_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 STOP command value mappings.

    STOP uses the MODE DPS code (152) with protobuf-encoded value:
    - "AggM" encodes ModeCtrlRequest.Method.STOP_TASK (12)
    """
    # Stop command - encodes STOP_TASK (method=12)
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.STOP, "stop") == "AggM"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.STOP, "unknown") == "unknown"


def test_t2267_command_codes(mock_t2267_robovac: RoboVac) -> None:
    """Test that T2267 command codes are correctly defined on model."""
    commands = mock_t2267_robovac.model_details.commands

    assert commands[RobovacCommand.MODE]["code"] == 152
    assert commands[RobovacCommand.STATUS]["code"] == 153
    assert commands[RobovacCommand.DIRECTION]["code"] == 155
    # START_PAUSE uses MODE command (code 152) for protobuf models
    assert commands[RobovacCommand.START_PAUSE]["code"] == 152
    assert commands[RobovacCommand.DO_NOT_DISTURB]["code"] == 157
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 158
    assert commands[RobovacCommand.BOOST_IQ]["code"] == 159
    assert commands[RobovacCommand.LOCATE]["code"] == 160
    assert commands[RobovacCommand.BATTERY]["code"] == 163
    assert commands[RobovacCommand.CONSUMABLES]["code"] == 168
    # RETURN_HOME uses MODE command (code 152) for protobuf models
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 152
    assert commands[RobovacCommand.ERROR]["code"] == 177


def test_t2267_status_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 STATUS command value mappings."""
    # Cleaning states
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "BgoAEAUyAA=="
    ) == "Cleaning"
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "BgoAEAVSAA=="
    ) == "Positioning"

    # Room cleaning states
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "CAoCCAEQBTIA"
    ) == "Room Cleaning"
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "CgoCCAEQBTICCAE="
    ) == "Room Paused"

    # Zone cleaning states
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "CAoCCAIQBTIA"
    ) == "Zone Cleaning"
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "CgoCCAIQBTICCAE="
    ) == "Zone Paused"

    # Docked/charging states
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "BBADGgA="
    ) == "Charging"
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "BhADGgIIAQ=="
    ) == "Completed"

    # Navigation states
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "BBAHQgA="
    ) == "Heading Home"

    # Idle states
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "AA=="
    ) == "Standby"
    assert mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "AhAB"
    ) == "Sleeping"


def test_t2267_activity_mapping(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 activity_mapping for VacuumActivity states."""
    activity_mapping = mock_t2267_robovac.model_details.activity_mapping

    # Verify activity_mapping exists
    assert activity_mapping is not None

    # Cleaning states map to CLEANING
    assert activity_mapping["Cleaning"] == VacuumActivity.CLEANING
    assert activity_mapping["Positioning"] == VacuumActivity.CLEANING
    assert activity_mapping["Room Cleaning"] == VacuumActivity.CLEANING
    assert activity_mapping["Zone Cleaning"] == VacuumActivity.CLEANING
    assert activity_mapping["Remote Control"] == VacuumActivity.CLEANING

    # Paused states map to PAUSED
    assert activity_mapping["Paused"] == VacuumActivity.PAUSED
    assert activity_mapping["Room Paused"] == VacuumActivity.PAUSED
    assert activity_mapping["Zone Paused"] == VacuumActivity.PAUSED

    # Returning states map to RETURNING
    assert activity_mapping["Heading Home"] == VacuumActivity.RETURNING

    # Docked states map to DOCKED
    assert activity_mapping["Charging"] == VacuumActivity.DOCKED
    assert activity_mapping["Completed"] == VacuumActivity.DOCKED

    # Idle states map to IDLE
    assert activity_mapping["Standby"] == VacuumActivity.IDLE
    assert activity_mapping["Sleeping"] == VacuumActivity.IDLE


def test_t2267_status_patterns(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 status pattern matching for dynamic STATUS codes."""
    # Verify status_patterns exists
    status_patterns = mock_t2267_robovac.model_details.status_patterns
    assert status_patterns is not None
    assert len(status_patterns) > 0

    # Test pattern matching for positioning codes with different timestamps
    # These codes follow the pattern: DA...FSAA== (start with DA, end with FSAA==)
    positioning_codes = [
        "DAi73ou93qHyzgFSAA==",  # Different timestamps
        "DAjE74KF76HyzgFSAA==",
        "DAiCobvM+KHyzgFSAA==",
        "DAxxxxxxxxxxxxxxFSAA==",  # Any content in middle should match
    ]

    for code in positioning_codes:
        result = mock_t2267_robovac.getRoboVacHumanReadableValue(
            RobovacCommand.STATUS, code
        )
        assert result == "Positioning", f"Expected 'Positioning' for {code}, got {result}"

    # Test that non-matching codes are returned as-is
    non_matching = "XYZabc123=="
    result = mock_t2267_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, non_matching
    )
    assert result == non_matching
