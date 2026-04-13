"""Tests for T2277 command mappings and DPS codes."""

import pytest
from typing import Any
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2277_robovac() -> RoboVac:
    """Create a mock T2277 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2277",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2277_dps_codes(mock_t2277_robovac: RoboVac) -> None:
    """Test that T2277 has the correct DPS codes."""
    dps_codes = mock_t2277_robovac.getDpsCodes()

    assert dps_codes["MODE"] == "152"
    assert dps_codes["STATUS"] == "153"
    assert dps_codes["START_PAUSE"] == "152"
    assert dps_codes["RETURN_HOME"] == "152"
    assert dps_codes["FAN_SPEED"] == "158"
    assert dps_codes["LOCATE"] == "160"
    assert dps_codes["BATTERY_LEVEL"] == "163"
    assert dps_codes["ERROR_CODE"] == "177"


def test_t2277_mode_command_values(mock_t2277_robovac: RoboVac) -> None:
    """Test T2277 MODE command value mappings."""
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "standby") == "AA=="
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause") == "AggN"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "stop") == "AggG"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "return") == "AggG"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "BBoCCAE="
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "AggO"

    # Unknown returns as-is
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2277_return_home_command_values(mock_t2277_robovac: RoboVac) -> None:
    """Test T2277 RETURN_HOME value mapping."""
    assert (
        mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return")
        == "AggG"
    )
    assert (
        mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "unknown")
        == "unknown"
    )


def test_t2277_fan_speed_command_values(mock_t2277_robovac: RoboVac) -> None:
    """Test T2277 FAN_SPEED value mapping."""
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert (
        mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown")
        == "unknown"
    )


def test_t2277_locate_command_values(mock_t2277_robovac: RoboVac) -> None:
    """Test T2277 LOCATE value mapping."""
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "locate") == "true"
    assert mock_t2277_robovac.getRoboVacCommandValue(RobovacCommand.LOCATE, "unknown") == "unknown"


def test_t2277_command_codes(mock_t2277_robovac: RoboVac) -> None:
    """Test that T2277 command codes are correctly defined on model."""
    commands = mock_t2277_robovac.model_details.commands

    assert commands[RobovacCommand.MODE]["code"] == 152
    assert commands[RobovacCommand.START_PAUSE]["code"] == 152
    assert commands[RobovacCommand.STATUS]["code"] == 153
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 152
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 158
    assert commands[RobovacCommand.LOCATE]["code"] == 160
    assert commands[RobovacCommand.BATTERY]["code"] == 163
    assert commands[RobovacCommand.ERROR]["code"] == 177


def test_t2277_error_dps_enabled(mock_t2277_robovac: RoboVac) -> None:
    """Test that ERROR command (DPS 177) is now enabled."""
    commands = mock_t2277_robovac.model_details.commands
    assert RobovacCommand.ERROR in commands
    assert commands[RobovacCommand.ERROR]["code"] == 177


def test_t2277_decode_dps_mode_ctrl() -> None:
    """Test decode_dps for MODE command (DPS 152)."""
    from custom_components.robovac.vacuums.T2277 import T2277

    # Test with a valid mode control value
    result = T2277.decode_dps(152, "AggN")
    assert result is not None


def test_t2277_decode_dps_status() -> None:
    """Test decode_dps for STATUS command (DPS 153)."""
    from custom_components.robovac.vacuums.T2277 import T2277

    # Test returns None when no valid data
    result = T2277.decode_dps(153, "AA==")
    # Should not raise an exception
    assert result is None or isinstance(result, str)


def test_t2277_decode_dps_battery() -> None:
    """Test decode_dps for unknown DPS code."""
    from custom_components.robovac.vacuums.T2277 import T2277

    # Unknown DPS codes should return None
    result = T2277.decode_dps(999, "AA==")
    assert result is None


def test_t2277_decode_dps_invalid_base64() -> None:
    """Test decode_dps handles invalid base64 gracefully."""
    from custom_components.robovac.vacuums.T2277 import T2277

    # Invalid base64 should return None without raising
    result = T2277.decode_dps(152, "invalid@base64!")
    assert result is None


def test_t2277_decode_dps_exception_handling() -> None:
    """Test decode_dps exception handling."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    # Mock proto_decode to raise an exception
    with patch("custom_components.robovac.proto_decode.decode_mode_ctrl", side_effect=Exception("decode error")):
        result = T2277.decode_dps(152, "AggN")
        assert result is None


def test_t2277_decode_dps_clean_param() -> None:
    """Test decode_dps for CLEAN_PARAM (DPS 154)."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    with patch(
        "custom_components.robovac.proto_decode.decode_clean_param_response",
        return_value={"running_clean_param": {"fan": "Standard"}}
    ):
        result = T2277.decode_dps(154, "AA==")
        assert result == "Standard"


def test_t2277_decode_dps_clean_records() -> None:
    """Test decode_dps for CLEAN_RECORDS (DPS 164)."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    with patch(
        "custom_components.robovac.proto_decode.decode_clean_record_list",
        return_value=[{"timestamp": 1234567890}]
    ):
        result = T2277.decode_dps(164, "AA==")
        assert "record" in result


def test_t2277_decode_dps_consumables() -> None:
    """Test decode_dps for CONSUMABLES (DPS 168)."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    with patch(
        "custom_components.robovac.proto_decode.decode_consumable_response",
        return_value={"side_brush": 100, "filter": 80}
    ):
        result = T2277.decode_dps(168, "AA==")
        assert "side_brush" in result


def test_t2277_decode_dps_device_info() -> None:
    """Test decode_dps for DEVICE_INFO (DPS 169)."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    with patch(
        "custom_components.robovac.proto_decode.decode_device_info",
        return_value={"product_name": "T2277", "software": "1.0.0"}
    ):
        result = T2277.decode_dps(169, "AA==")
        assert "product_name" in result


def test_t2277_decode_dps_work_status_v2() -> None:
    """Test decode_dps for WORK_STATUS_V2 (DPS 173)."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    with patch(
        "custom_components.robovac.proto_decode.decode_work_status_v2",
        return_value="Cleaning"
    ):
        result = T2277.decode_dps(173, "AA==")
        assert result == "Cleaning"


def test_t2277_decode_dps_unisetting() -> None:
    """Test decode_dps for UNISETTING (DPS 176)."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    with patch(
        "custom_components.robovac.proto_decode.decode_unisetting_response",
        return_value={"wifi_ssid": "MyNetwork"}
    ):
        result = T2277.decode_dps(176, "AA==")
        assert "wifi_ssid" in result


def test_t2277_decode_dps_error_code() -> None:
    """Test decode_dps for ERROR (DPS 177)."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    with patch(
        "custom_components.robovac.proto_decode.decode_error_code",
        return_value="Battery low"
    ):
        result = T2277.decode_dps(177, "AA==")
        assert result == "Battery low"


def test_t2277_decode_dps_last_clean() -> None:
    """Test decode_dps for LAST_CLEAN (DPS 179)."""
    from custom_components.robovac.vacuums.T2277 import T2277
    from unittest.mock import patch

    with patch(
        "custom_components.robovac.proto_decode.decode_analysis_response",
        return_value={"clean_time_s": 3600}
    ):
        result = T2277.decode_dps(179, "AA==")
        assert "clean_time_s" in result
