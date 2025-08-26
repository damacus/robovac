"""Tests for T2320 command mappings based on debug logs from issue #178."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac, RobovacCommand
from custom_components.robovac.vacuums.T2320 import T2320


@pytest.fixture
def t2320_robovac():
    """Create a T2320 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2320",
            device_id="ebdf9164106a625759qybp",
            host="192.168.187.132",
            local_key="test_key",
        )
        return robovac


class TestT2320CommandMappings:
    """Test T2320 command mappings match debug log expectations."""

    def test_return_home_command_value(self, t2320_robovac):
        """Test RETURN_HOME command returns boolean true as seen in debug logs."""
        # Debug log shows: "dps": {"153": true}
        result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return_home")
        assert result is True or result == "True" or result == "true"

    def test_start_pause_command_exists(self, t2320_robovac):
        """Test START_PAUSE command is defined for T2320."""
        # Debug log shows: "dps": {"2": false}
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.START_PAUSE in commands

    def test_start_pause_command_value(self, t2320_robovac):
        """Test START_PAUSE command returns boolean values."""
        # Debug log shows: "dps": {"2": false}
        pause_result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause")
        assert pause_result is False or pause_result == "False" or pause_result == "false"

        start_result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start")
        assert start_result is True or start_result == "True" or start_result == "true"

    def test_mode_command_value(self, t2320_robovac):
        """Test MODE command returns plain string values as seen in debug logs."""
        # Debug log shows: "dps": {"152": "auto"}
        result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto")
        assert result == "auto"

    def test_fan_speed_command_has_multiple_options(self, t2320_robovac):
        """Test FAN_SPEED command has multiple readable options."""
        fan_speeds = t2320_robovac.getFanSpeeds()
        # Should have more than one option and not contain base64-like strings
        assert len(fan_speeds) > 1
        for speed in fan_speeds:
            # Should not be base64-like encoded strings
            assert not speed.startswith("Ag")
            assert len(speed) < 20  # Reasonable length for human-readable names

    def test_dps_codes_mapping(self, t2320_robovac):
        """Test DPS codes match debug log expectations."""
        dps_codes = t2320_robovac.getDpsCodes()
        # Based on debug logs
        assert dps_codes.get("RETURN_HOME") == "153"
        assert dps_codes.get("START_PAUSE") == "2"
        assert dps_codes.get("MODE") == "152"
        assert dps_codes.get("FAN_SPEED") == "154"

    def test_status_command_exists(self, t2320_robovac):
        """Test STATUS command is defined for state polling."""
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.STATUS in commands

    def test_locate_command_exists(self, t2320_robovac):
        """Test LOCATE command is defined."""
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.LOCATE in commands
