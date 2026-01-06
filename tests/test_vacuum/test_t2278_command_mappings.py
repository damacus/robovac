"""Tests for T2278 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from homeassistant.components.vacuum import VacuumActivity

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2278_robovac() -> RoboVac:
    """Create a mock T2278 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2278",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


class TestT2278DpsCodes:
    """Test T2278 DPS code mappings."""

    def test_dps_codes(self, mock_t2278_robovac: RoboVac) -> None:
        """Test that T2278 has the correct DPS codes."""
        dps_codes = mock_t2278_robovac.getDpsCodes()

        assert dps_codes["MODE"] == "152"
        assert dps_codes["STATUS"] == "153"
        assert dps_codes["START_PAUSE"] == "152"
        assert dps_codes["RETURN_HOME"] == "152"
        assert dps_codes["FAN_SPEED"] == "158"
        assert dps_codes["LOCATE"] == "160"
        assert dps_codes["BATTERY_LEVEL"] == "163"


class TestT2278ModeCommand:
    """Test T2278 MODE command value mappings."""

    def test_mode_command_values(self, mock_t2278_robovac: RoboVac) -> None:
        """Test T2278 MODE command value mappings."""
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "standby") == "AA=="
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause") == "AggN"
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "stop") == "AggG"
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "return") == "AggG"
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "BBoCCAE="
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "AggO"

    def test_mode_unknown_returns_as_is(self, mock_t2278_robovac: RoboVac) -> None:
        """Test unknown MODE value returns as-is."""
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


class TestT2278StatusCommand:
    """Test T2278 STATUS command value mappings."""

    def test_status_human_readable_values(self, mock_t2278_robovac: RoboVac) -> None:
        """Test T2278 STATUS command returns human-readable values."""
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "AA==") == "Standby"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "AggB") == "Paused"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "AhAB") == "Sleeping"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "BBADGgA=") == "Charging"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "BBAHQgA=") == "Heading Home"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "BgoAEAUyAA==") == "Cleaning"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "BgoAEAVSAA==") == "Positioning"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "BhADGgIIAQ==") == "Completed"

    def test_status_room_cleaning_values(self, mock_t2278_robovac: RoboVac) -> None:
        """Test T2278 room cleaning status values."""
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "CAoCCAEQBTIA") == "Room Cleaning"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "CAoCCAEQBVIA") == "Room Positioning"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "CgoCCAEQBTICCAE=") == "Room Paused"

    def test_status_zone_cleaning_values(self, mock_t2278_robovac: RoboVac) -> None:
        """Test T2278 zone cleaning status values."""
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "CAoCCAIQBTIA") == "Zone Cleaning"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "CAoCCAIQBVIA") == "Zone Positioning"
        assert mock_t2278_robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, "CgoCCAIQBTICCAE=") == "Zone Paused"


class TestT2278FanSpeedCommand:
    """Test T2278 FAN_SPEED command value mappings."""

    def test_fan_speed_command_values(self, mock_t2278_robovac: RoboVac) -> None:
        """Test T2278 FAN_SPEED value mapping."""
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"

    def test_fan_speed_unknown_returns_as_is(self, mock_t2278_robovac: RoboVac) -> None:
        """Test unknown FAN_SPEED value returns as-is."""
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


class TestT2278LocateCommand:
    """Test T2278 LOCATE command value mappings."""

    def test_locate_command_values(self, mock_t2278_robovac: RoboVac) -> None:
        """Test T2278 LOCATE value mapping."""
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "locate") == "true"

    def test_locate_unknown_returns_as_is(self, mock_t2278_robovac: RoboVac) -> None:
        """Test unknown LOCATE value returns as-is."""
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "unknown") == "unknown"


class TestT2278ReturnHomeCommand:
    """Test T2278 RETURN_HOME command value mappings."""

    def test_return_home_command_values(self, mock_t2278_robovac: RoboVac) -> None:
        """Test T2278 RETURN_HOME value mapping."""
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return") == "AggG"

    def test_return_home_unknown_returns_as_is(self, mock_t2278_robovac: RoboVac) -> None:
        """Test unknown RETURN_HOME value returns as-is."""
        assert mock_t2278_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "unknown") == "unknown"


class TestT2278CommandCodes:
    """Test T2278 command code definitions."""

    def test_command_codes(self, mock_t2278_robovac: RoboVac) -> None:
        """Test that T2278 command codes are correctly defined on model."""
        commands = mock_t2278_robovac.model_details.commands

        assert commands[RobovacCommand.MODE]["code"] == 152
        assert commands[RobovacCommand.START_PAUSE]["code"] == 152
        assert commands[RobovacCommand.STATUS]["code"] == 153
        assert commands[RobovacCommand.RETURN_HOME]["code"] == 152
        assert commands[RobovacCommand.FAN_SPEED]["code"] == 158
        assert commands[RobovacCommand.LOCATE]["code"] == 160
        assert commands[RobovacCommand.BATTERY]["code"] == 163


class TestT2278ActivityMapping:
    """Test T2278 activity mapping for Home Assistant integration."""

    def test_activity_mapping_exists(self, mock_t2278_robovac: RoboVac) -> None:
        """Test that T2278 has activity_mapping defined."""
        assert hasattr(mock_t2278_robovac.model_details, "activity_mapping")
        assert mock_t2278_robovac.model_details.activity_mapping is not None

    def test_activity_mapping_cleaning_states(self, mock_t2278_robovac: RoboVac) -> None:
        """Test cleaning states map to VacuumActivity.CLEANING."""
        mapping = mock_t2278_robovac.model_details.activity_mapping
        assert mapping["Cleaning"] == VacuumActivity.CLEANING
        assert mapping["Positioning"] == VacuumActivity.CLEANING
        assert mapping["Room Cleaning"] == VacuumActivity.CLEANING
        assert mapping["Room Positioning"] == VacuumActivity.CLEANING
        assert mapping["Zone Cleaning"] == VacuumActivity.CLEANING
        assert mapping["Zone Positioning"] == VacuumActivity.CLEANING

    def test_activity_mapping_docked_states(self, mock_t2278_robovac: RoboVac) -> None:
        """Test docked states map to VacuumActivity.DOCKED."""
        mapping = mock_t2278_robovac.model_details.activity_mapping
        assert mapping["Charging"] == VacuumActivity.DOCKED
        assert mapping["Completed"] == VacuumActivity.DOCKED

    def test_activity_mapping_paused_states(self, mock_t2278_robovac: RoboVac) -> None:
        """Test paused states map to VacuumActivity.PAUSED."""
        mapping = mock_t2278_robovac.model_details.activity_mapping
        assert mapping["Paused"] == VacuumActivity.PAUSED
        assert mapping["Room Paused"] == VacuumActivity.PAUSED
        assert mapping["Zone Paused"] == VacuumActivity.PAUSED

    def test_activity_mapping_returning_state(self, mock_t2278_robovac: RoboVac) -> None:
        """Test returning state maps to VacuumActivity.RETURNING."""
        mapping = mock_t2278_robovac.model_details.activity_mapping
        assert mapping["Heading Home"] == VacuumActivity.RETURNING

    def test_activity_mapping_idle_states(self, mock_t2278_robovac: RoboVac) -> None:
        """Test idle states map to VacuumActivity.IDLE."""
        mapping = mock_t2278_robovac.model_details.activity_mapping
        assert mapping["Sleeping"] == VacuumActivity.IDLE
        assert mapping["Standby"] == VacuumActivity.IDLE
