"""Tests for T2320 command mappings based on debug logs from issue #178."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac, RobovacCommand
from custom_components.robovac.vacuums.T2320 import T2320


@pytest.fixture
def t2320_robovac() -> RoboVac:
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
        """Test RETURN_HOME command returns protobuf-encoded value like T2267."""
        # T2320 uses same protobuf encoding as T2267 for return home
        result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return")
        assert result == "AggG"  # Protobuf: ModeCtrlRequest.Method.START_GOHOME

    def test_start_pause_command_exists(self, t2320_robovac):
        """Test START_PAUSE command is defined for T2320."""
        # Debug log shows: "dps": {"2": false}
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.START_PAUSE in commands

    def test_start_pause_command_value(self, t2320_robovac):
        """Test START_PAUSE command returns protobuf-encoded values like T2267."""
        # T2320 uses same protobuf encoding as T2267 for pause/resume
        pause_result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause")
        assert pause_result == "AggN"  # Protobuf: ModeCtrlRequest.Method.PAUSE_TASK

        resume_result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "resume")
        assert resume_result == "AggO"  # Protobuf: ModeCtrlRequest.Method.RESUME_TASK

    def test_mode_command_value(self, t2320_robovac):
        """Test MODE command returns protobuf-encoded values like T2267."""
        # T2320 uses same protobuf encoding as T2267 for mode commands
        result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto")
        assert result == "BBoCCAE="  # Protobuf: ModeCtrlRequest.Method.START_AUTO_CLEAN

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
        """Test DPS codes match expected values."""
        dps_codes = t2320_robovac.getDpsCodes()
        assert dps_codes.get("RETURN_HOME") == "152"  # Same as MODE, uses protobuf like T2267
        assert dps_codes.get("START_PAUSE") == "152"  # Same as MODE, uses protobuf like T2267
        assert dps_codes.get("MODE") == "152"
        assert dps_codes.get("STOP") == "152"  # Same as MODE, uses protobuf like T2267
        assert dps_codes.get("FAN_SPEED") == "154"
        assert dps_codes.get("LOCATE") == "160"  # Fixed: was 153 (conflict with RETURN_HOME)
        assert dps_codes.get("STATUS") == "177"  # T2320 uses different STATUS code than T2267
        assert dps_codes.get("BATTERY_LEVEL") == "172"
        assert dps_codes.get("ERROR_CODE") == "177"

    def test_status_command_exists(self, t2320_robovac):
        """Test STATUS command is defined for state polling."""
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.STATUS in commands

    def test_locate_command_exists(self, t2320_robovac):
        """Test LOCATE command is defined."""
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.LOCATE in commands

    def test_locate_uses_different_code_than_return_home(self, t2320_robovac):
        """Test LOCATE and RETURN_HOME use different DPS codes."""
        dps_codes = t2320_robovac.getDpsCodes()
        # LOCATE should NOT share the same code as RETURN_HOME
        assert dps_codes.get("LOCATE") != dps_codes.get("RETURN_HOME")

    def test_status_values_mapping(self, t2320_robovac):
        """Test STATUS command has value mappings for protobuf-encoded states."""
        # Test that STATUS has value mappings
        commands = t2320_robovac.model_details.commands
        status_cmd = commands.get(RobovacCommand.STATUS)
        assert status_cmd is not None
        assert "values" in status_cmd

        # Test common status values exist
        status_values = status_cmd["values"]
        # Check charging state exists
        assert "BBADGgA=" in status_values
        assert status_values["BBADGgA="] == "Charging"
        # Check standby state exists
        assert "AA==" in status_values
        assert status_values["AA=="] == "Standby"

    def test_activity_mapping_exists(self, t2320_robovac):
        """Test T2320 has activity_mapping for Home Assistant states."""
        activity_mapping = t2320_robovac.model_details.activity_mapping
        assert activity_mapping is not None
        assert len(activity_mapping) > 0

    def test_activity_mapping_contains_station_states(self, t2320_robovac):
        """Test activity_mapping includes X9 Pro auto-clean station states."""
        from homeassistant.components.vacuum import VacuumActivity
        activity_mapping = t2320_robovac.model_details.activity_mapping

        # X9 Pro has auto-clean station - verify station states are mapped
        assert "Washing Mop" in activity_mapping
        assert activity_mapping["Washing Mop"] == VacuumActivity.DOCKED
        assert "Drying Mop" in activity_mapping
        assert activity_mapping["Drying Mop"] == VacuumActivity.DOCKED
        assert "Emptying Dust" in activity_mapping
        assert activity_mapping["Emptying Dust"] == VacuumActivity.DOCKED

    def test_human_readable_status_conversion(self, t2320_robovac):
        """Test STATUS values are converted to human-readable strings."""
        # Test protobuf-encoded status -> human readable
        result = t2320_robovac.getRoboVacHumanReadableValue(
            RobovacCommand.STATUS, "BBADGgA="
        )
        assert result == "Charging"

        result = t2320_robovac.getRoboVacHumanReadableValue(
            RobovacCommand.STATUS, "AA=="
        )
        assert result == "Standby"

        result = t2320_robovac.getRoboVacHumanReadableValue(
            RobovacCommand.STATUS, "BhAJOgIQAQ=="
        )
        assert result == "Washing Mop"

    def test_fan_speed_values(self, t2320_robovac):
        """Test FAN_SPEED command value mappings."""
        # Test snake_case input -> PascalCase output
        assert t2320_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
        assert t2320_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
        assert t2320_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
        assert t2320_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"

    def test_status_patterns_exist(self, t2320_robovac):
        """Test T2320 has status_patterns for dynamic STATUS codes."""
        status_patterns = t2320_robovac.model_details.status_patterns
        assert status_patterns is not None
        assert len(status_patterns) > 0
        # Verify positioning pattern exists
        assert ("DA", "FSAA==", "Positioning") in status_patterns

    def test_error_patterns_exist(self, t2320_robovac):
        """Test T2320 has error_patterns to prevent false error states."""
        error_patterns = t2320_robovac.model_details.error_patterns
        assert error_patterns is not None
        assert len(error_patterns) > 0
        # Verify positioning-on-error pattern exists
        assert ("DA", "FSAA==", "no_error") in error_patterns

    def test_status_pattern_matching(self, t2320_robovac):
        """Test STATUS pattern matching for dynamic positioning codes."""
        # These codes have dynamic timestamps in the middle
        positioning_codes = [
            "DAi73ou93qHyzgFSAA==",
            "DAjE74KF76HyzgFSAA==",
            "DAiCobvM+KHyzgFSAA==",
        ]

        for code in positioning_codes:
            result = t2320_robovac.getRoboVacHumanReadableValue(
                RobovacCommand.STATUS, code
            )
            assert result == "Positioning", f"Expected 'Positioning' for {code}, got {result}"

    def test_error_pattern_matching(self, t2320_robovac):
        """Test ERROR pattern matching prevents false error states."""
        # Positioning status sent on ERROR DPS should return "no_error"
        positioning_codes = [
            "DAi73ou93qHyzgFSAA==",
            "DAjE74KF76HyzgFSAA==",
        ]

        for code in positioning_codes:
            result = t2320_robovac.getRoboVacHumanReadableValue(
                RobovacCommand.ERROR, code
            )
            assert result == "no_error", f"Expected 'no_error' for {code} on ERROR DPS, got {result}"
