"""Tests for T2267 (RoboVac L60) command mappings and DPS decoding."""

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


# ── Model structure ───────────────────────────────────────────────────────────


def test_t2267_model_has_required_commands(mock_t2267_robovac: RoboVac) -> None:
    """Test that T2267 model has all required commands defined."""
    commands = mock_t2267_robovac.model_details.commands

    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.ERROR in commands


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
    """Test DPS 177 with last byte 0x00 returns 'no_error'."""
    # base64 of bytes ending in 0x00
    import base64

    payload = base64.b64encode(bytes([0x01, 0x02, 0x00])).decode()
    assert T2267.decode_dps(177, payload) == "no_error"


def test_t2267_decode_dps_error_code() -> None:
    """Test DPS 177 with non-zero last byte returns the error code as string."""
    import base64

    payload = base64.b64encode(bytes([0x01, 0x02, 39])).decode()
    assert T2267.decode_dps(177, payload) == "39"


def test_t2267_decode_dps_error_code_54() -> None:
    """Test DPS 177 returns error code 54 as string."""
    import base64

    payload = base64.b64encode(bytes([0x01, 0x02, 54])).decode()
    assert T2267.decode_dps(177, payload) == "54"


def test_t2267_decode_dps_empty_payload() -> None:
    """Test DPS 177 with empty decoded bytes returns 'no_error'."""
    import base64

    payload = base64.b64encode(b"").decode()
    assert T2267.decode_dps(177, payload) == "no_error"


def test_t2267_decode_dps_invalid_base64() -> None:
    """Test DPS 177 with invalid base64 falls back to 'no_error'."""
    assert T2267.decode_dps(177, "!!!invalid!!!") == "no_error"


def test_t2267_decode_dps_other_dps_returns_none() -> None:
    """Test that DPS codes other than 177 return None (fall through to standard handling)."""
    assert T2267.decode_dps(152, "somevalue") is None
    assert T2267.decode_dps(153, "somevalue") is None
    assert T2267.decode_dps(1, "somevalue") is None
