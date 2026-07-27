"""Tests for T2267 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand
from custom_components.robovac.vacuums.T2267 import T2267
from homeassistant.components.vacuum import VacuumActivity


@pytest.fixture
def mock_t2267_robovac() -> RoboVac:
    """Create a mock T2267 RoboVac instance for testing."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
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
    assert dps_codes["START_PAUSE"] == "156"
    assert dps_codes["DO_NOT_DISTURB"] == "157"
    assert dps_codes["FAN_SPEED"] == "158"
    assert dps_codes["BOOST_IQ"] == "159"
    assert dps_codes["LOCATE"] == "160"
    assert dps_codes["BATTERY_LEVEL"] == "163"
    assert dps_codes["CONSUMABLES"] == "168"
    assert dps_codes["RETURN_HOME"] == "173"
    assert dps_codes["ERROR_CODE"] == "177"


def test_t2267_mode_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 MODE command value mappings."""
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto")
        == "BBoCCAE="
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause")
        == "AggN"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "Spot") == "AA=="
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "return")
        == "AggG"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "Nosweep")
        == "AggO"
    )

    # Unknown returns as-is
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown")
        == "unknown"
    )


def test_t2267_fan_speed_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 FAN_SPEED command value mappings."""
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet")
        == "Quiet"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard")
        == "Standard"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo")
        == "Turbo"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max")
        == "Max"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost_iq")
        == "Boost_IQ"
    )

    # Unknown returns as-is
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown")
        == "unknown"
    )


def test_t2267_direction_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 DIRECTION command value mappings."""
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "brake")
        == "brake"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "forward")
        == "forward"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "back")
        == "back"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "left")
        == "left"
    )
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "right")
        == "right"
    )

    # Unknown returns as-is
    assert (
        mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "unknown")
        == "unknown"
    )


def test_t2267_command_codes(mock_t2267_robovac: RoboVac) -> None:
    """Test that T2267 command codes are correctly defined on model."""
    commands = mock_t2267_robovac.model_details.commands

    assert commands[RobovacCommand.MODE]["code"] == 152
    assert commands[RobovacCommand.STATUS]["code"] == 153
    assert commands[RobovacCommand.DIRECTION]["code"] == 155
    assert commands[RobovacCommand.START_PAUSE]["code"] == 156
    assert commands[RobovacCommand.DO_NOT_DISTURB]["code"] == 157
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 158
    assert commands[RobovacCommand.BOOST_IQ]["code"] == 159
    assert commands[RobovacCommand.LOCATE]["code"] == 160
    assert commands[RobovacCommand.BATTERY]["code"] == 163
    assert commands[RobovacCommand.CONSUMABLES]["code"] == 168
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 173
    assert commands[RobovacCommand.ERROR]["code"] == 177


# ── Activity mapping ──────────────────────────────────────────────────────────


def test_t2267_activity_mapping_cleaning() -> None:
    """Test that known cleaning state payloads map to CLEANING."""
    cleaning_payloads = [
        "BgoAEAUyAA==",
        "BgoAEAVSAA==",
        "CAoAEAUyAggB",
        "CAoCCAEQBTIA",
        "CAoCCAEQBVIA",
        "CgoCCAEQBTICCAE=",
        "CAoCCAIQBTIA",
        "CAoCCAIQBVIA",
        "CgoCCAIQBTICCAE=",
    ]
    for payload in cleaning_payloads:
        assert (
            T2267.activity_mapping[payload] == VacuumActivity.CLEANING
        ), f"Expected CLEANING for payload {payload}"


def test_t2267_activity_mapping_returning() -> None:
    """Test that known returning state payloads map to RETURNING."""
    assert T2267.activity_mapping["BAoAEAY="] == VacuumActivity.RETURNING
    assert T2267.activity_mapping["BBAHQgA="] == VacuumActivity.RETURNING


def test_t2267_activity_mapping_docked() -> None:
    """Test that known docked state payloads map to DOCKED."""
    assert T2267.activity_mapping["BBADGgA="] == VacuumActivity.DOCKED
    assert T2267.activity_mapping["BhADGgIIAQ=="] == VacuumActivity.DOCKED


def test_t2267_activity_mapping_idle() -> None:
    """Test that known idle state payloads map to IDLE."""
    assert T2267.activity_mapping["AA=="] == VacuumActivity.IDLE
    assert T2267.activity_mapping["AhAB"] == VacuumActivity.IDLE


# ── decode_dps ────────────────────────────────────────────────────────────────


def test_t2267_decode_dps_no_error() -> None:
    """Test DPS 177 with no active error returns 'no_error'."""
    assert T2267.decode_dps(177, "DAicn/qmtIztzgFSAA==") == "no_error"


def test_t2267_decode_dps_robot_suspended() -> None:
    """Test DPS 177 returns 'Robot suspended' when robot is lifted off the ground."""
    assert T2267.decode_dps(177, "FAiP84Hms4ztzgEaAto2UgQSAto2") == "Robot suspended"


def test_t2267_decode_dps_invalid_base64() -> None:
    """Test DPS 177 with invalid base64 falls back to 'no_error'."""
    assert T2267.decode_dps(177, "!!!invalid!!!") == "no_error"


def test_t2267_decode_dps_other_dps_returns_none() -> None:
    """Test that DPS codes other than 177 return None."""
    assert T2267.decode_dps(152, "somevalue") is None
    assert T2267.decode_dps(153, "somevalue") is None
    assert T2267.decode_dps(1, "somevalue") is None


def test_t2267_decode_dps_unmapped_error_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an unmapped error code logs a warning with instructions to report it."""
    import logging
    import base64
    from custom_components.robovac.proto_decode import _parse_proto, _encode_varint

    # Build a minimal DPS 177 payload with an unknown error code (99999)
    # Field 3 = repeated uint32 warn, wire type 0
    unknown_code = 99999
    field_tag = (3 << 3) | 0  # field 3, wire type 0 (varint)
    proto_payload = _encode_varint(field_tag) + _encode_varint(unknown_code)
    # Add length prefix byte
    raw = bytes([len(proto_payload)]) + proto_payload
    payload = base64.b64encode(raw).decode()

    with caplog.at_level(
        logging.WARNING, logger="custom_components.robovac.vacuums.T2267"
    ):
        result = T2267.decode_dps(177, payload)

    assert result == "error_99999"
    assert "unmapped error code" in caplog.text
    assert "Check the Eufy app" in caplog.text
    assert "https://github.com/damacus/robovac/issues" in caplog.text
