"""Tests for T2320 command mappings based on debug logs from issue #178."""

import pytest
from unittest.mock import patch
import base64

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
        """Test MODE command returns base64 protobuf values observed on X9."""
        result = t2320_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto")
        assert result == "BBoCCAE="

    def test_fan_speed_command_has_multiple_options(self, t2320_robovac):
        """Test FAN_SPEED command has multiple readable options."""
        fan_speeds = t2320_robovac.getFanSpeeds()
        assert fan_speeds == ["Standard", "Turbo", "Max", "Quiet"]
        # Should have more than one option and not contain base64-like strings
        assert len(fan_speeds) > 1
        for speed in fan_speeds:
            # Should not be base64-like encoded strings
            assert not speed.startswith("Ag")
            assert len(speed) < 20  # Reasonable length for human-readable names

    def test_fan_speed_command_values(self, t2320_robovac):
        """Test FAN_SPEED command values match X9 suction levels."""
        assert t2320_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
        assert t2320_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
        assert t2320_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
        assert t2320_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"

    def test_dps_codes_mapping(self, t2320_robovac):
        """Test DPS codes match debug log expectations."""
        dps_codes = t2320_robovac.getDpsCodes()
        # Based on debug logs
        assert dps_codes.get("RETURN_HOME") == "153"
        assert dps_codes.get("START_PAUSE") == "2"
        assert dps_codes.get("MODE") == "152"
        assert dps_codes.get("CLEAN_PARAM") == "154"
        assert dps_codes.get("FAN_SPEED") == "158"
        assert dps_codes.get("BATTERY_LEVEL") == "163"
        assert dps_codes.get("CONSUMABLES") == "168"
        assert dps_codes.get("ERROR_CODE") == "177"
        assert "ROOM_CLEAN" not in dps_codes

    def test_status_command_exists(self, t2320_robovac):
        """Test STATUS command is defined for state polling."""
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.STATUS in commands

    def test_consumables_command_exists(self, t2320_robovac):
        """Test DPS 168 is exposed as consumables, not room-clean metadata."""
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.CONSUMABLES in commands
        assert t2320_robovac.model_details.commands[RobovacCommand.CONSUMABLES]["code"] == 168

    def test_locate_command_exists(self, t2320_robovac):
        """Test LOCATE command is defined."""
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.LOCATE in commands

    def test_clean_param_command_enables_mop_telemetry_sensor(self, t2320_robovac):
        """CLEAN_PARAM on 154 is required for RobovacCleanTypeSensor (sweep/mop mode)."""
        commands = t2320_robovac.getSupportedCommands()
        assert RobovacCommand.CLEAN_PARAM in commands
        assert t2320_robovac.model_details.commands[RobovacCommand.CLEAN_PARAM]["code"] == 154

    def test_decode_station_status_from_base64_payload(self):
        """Test station keywords are found after base64 decoding DPS 173."""
        raw = base64.b64encode(b"\x08\x01 station WASHING active").decode()
        assert T2320.decode_dps("173", raw) == "washing"

    def test_decode_station_status_from_live_washing_payload(self):
        """Test observed X9 station status payload maps to washing."""
        raw = "MgokCgwKBggBGgIIChIAGAESBggBEgIIAjIMCgIIARIGCAEQARgPEgYIARABKAEqAggt"
        assert T2320.decode_dps("173", raw) == "washing"

    def test_decode_station_status_from_live_drying_payload(self):
        """Test observed X9 station status payload maps to drying."""
        raw = "MAokCgwKBggBGgIIChIAGAESBggBEgIIAjIMCgIIARIGCAEQARgPEgQIARACKgIITA=="
        assert T2320.decode_dps("173", raw) == "drying"

    def test_decode_error_without_active_codes_is_no_error(self):
        """Test empty/zero DPS 177 protobuf payload does not force an error."""
        assert T2320.decode_dps("177", "AA==") == "no_error"

    def test_decode_warning_only_station_payload_is_no_error(self):
        """Test observed X9 warning-only station payload does not force error."""
        assert T2320.decode_dps("177", "Dwj22eCIkfFEGgFSIgBSAA==") == "no_error"

    def test_decode_warning_dps_from_live_payload(self):
        """Test observed X9 warning payload exposes non-fatal warnings."""
        assert T2320.decode_warning_dps("Dwj22eCIkfFEGgFSIgBSAA==") == [
            {"code": 82, "message": "Clean station wash tray"}
        ]

    def test_decode_return_progress_payloads(self):
        """Test observed X9 return progress payloads distinguish moving vs docked."""
        assert T2320.decode_dps("153", "CBAFGgA6AhAB") == "returning"
        assert T2320.decode_dps("153", "CBAHQgByAiIA") == "returning"
        assert T2320.decode_dps("153", "DhAFGgA6AhABcgQaACIA") == "docked"
        assert T2320.decode_dps("153", "EBAFGgA6AhACcgYaAggBIgA=") == "docked"
        assert T2320.decode_dps("153", "FAoAEAUaADICCAE6AhABcgQaACIA") == "docked"
        assert T2320.decode_dps("153", "CgoAEAUyAHICIgA=") == "cleaning"

    def test_decode_route_unavailable_prompt(self):
        """Test observed X9 room-clean failure prompt from DPS 178."""
        assert T2320.decode_dps("178", "CwjczIPu6YlJEgEH") == (
            "Path planning failed, cannot reach the designated area"
        )

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("CwiY+IOJrO9JEgEK", "Positioning successful"),
            ("Cwj6iLDX8uxJEgEM", "Cannot start task while on station"),
        ],
    )
    def test_decode_observed_x9_prompt_codes(self, raw, expected):
        """Test observed X9 prompt codes avoid raw prompt_N states."""
        assert T2320.decode_dps("178", raw) == expected

    def test_decode_observed_x9_prompt_17(self):
        """Test observed X9 prompt 17 avoids a raw prompt_N state."""
        raw = base64.b64encode(bytes([3, 0x12, 0x01, 17])).decode()
        assert T2320.decode_dps("178", raw) == "Mop cleaning completed"
