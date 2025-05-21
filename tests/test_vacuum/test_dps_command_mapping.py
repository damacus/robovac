"""Tests for mapping between command codes and DPS values."""

import pytest
from unittest.mock import patch, MagicMock

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuum import TUYA_CODES, RoboVacEntity
from custom_components.robovac.vacuums.base import RobovacCommand
from homeassistant.const import (
    CONF_NAME,
    CONF_ID,
    CONF_MAC,
    CONF_MODEL,
    CONF_IP_ADDRESS,
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
)


def test_dps_codes_match_expected_values():
    """Test that DPS codes match the expected values for default models."""
    # Setup test model codes
    test_models = ["T2128", "T1250"]

    for model_code in test_models:
        # Initialize RoboVac instance with mock parameters
        with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
            vacuum = RoboVac(
                model_code=model_code,
                device_id="test_id",
                host="192.168.1.1",
                local_key="test_key",
            )

            # Get DPS codes from the model
            dps_codes = vacuum.getDpsCodes()

            # Verify common DPS values match their respective expected codes
            assert dps_codes.get("STATE") == TUYA_CODES.STATE
            assert dps_codes.get("BATTERY_LEVEL") == TUYA_CODES.BATTERY_LEVEL
            assert dps_codes.get("ERROR_CODE") == TUYA_CODES.ERROR_CODE

            # If MODE is in the codes, verify it matches
            if "MODE" in dps_codes:
                assert dps_codes.get("MODE") == TUYA_CODES.MODE

            # If FAN_SPEED is in the codes, verify it matches
            if "FAN_SPEED" in dps_codes:
                assert dps_codes.get("FAN_SPEED") == TUYA_CODES.FAN_SPEED


def test_nonstandard_model_dps_codes():
    """Test that non-standard models have DPS codes that differ from defaults."""
    # Setup test for a model with non-standard codes (T2267)
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        vacuum = RoboVac(
            model_code="T2267",
            device_id="test_id",
            host="192.168.1.1",
            local_key="test_key",
        )

        # Get DPS codes from the model
        dps_codes = vacuum.getDpsCodes()

        # Verify T2267 has different codes than the defaults
        assert dps_codes.get("STATE") != TUYA_CODES.STATE
        assert dps_codes.get("BATTERY_LEVEL") != TUYA_CODES.BATTERY_LEVEL
        assert dps_codes.get("ERROR_CODE") != TUYA_CODES.ERROR_CODE
        assert dps_codes.get("FAN_SPEED") != TUYA_CODES.FAN_SPEED


def test_getDpsCodes_extraction_method():
    """Test that getDpsCodes extracts codes correctly from different command formats."""
    # Setup test model with various command format types
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        # Test with T2128 which has both direct values and dict with code
        vacuum = RoboVac(
            model_code="T2128",
            device_id="test_id",
            host="192.168.1.1",
            local_key="test_key",
        )

        dps_codes = vacuum.getDpsCodes()

        # Test mapping from command to DPS code name
        # STATUS -> STATE
        assert "STATE" in dps_codes
        assert dps_codes["STATE"] == "15"  # From STATUS: 15

        # BATTERY -> BATTERY_LEVEL
        assert "BATTERY_LEVEL" in dps_codes
        assert dps_codes["BATTERY_LEVEL"] == "104"  # From BATTERY: 104

        # Test direct value and dict with code extraction
        assert "START_PAUSE" in dps_codes
        assert dps_codes["START_PAUSE"] == "2"  # Direct value

        assert "FAN_SPEED" in dps_codes
        assert dps_codes["FAN_SPEED"] == "102"  # From dict with code


@pytest.mark.asyncio
async def test_vacuum_update_uses_correct_dps_codes():
    """Test that vacuum update uses the right DPS codes for the model."""
    # Mock vacuum data
    mock_vacuum_data = {
        CONF_NAME: "Test Vacuum",
        CONF_ID: "test_id",
        CONF_MAC: "test_mac",
        CONF_MODEL: "T2128",
        CONF_IP_ADDRESS: "192.168.1.1",
        CONF_ACCESS_TOKEN: "test_token",
        CONF_DESCRIPTION: "Test Description",
    }

    # Create mock RoboVac instance
    mock_robovac = MagicMock()
    mock_robovac._dps = {
        "15": "Cleaning",  # Status
        "104": 75,         # Battery level
        "106": 0,          # Error code
        "5": "auto",       # Mode
        "102": "Standard"  # Fan speed
    }

    # Initialize the vacuum entity
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.update_entity_values()

        # Check that the correct values were extracted
        assert entity._attr_battery_level == 75
        assert entity._attr_tuya_state == "Cleaning"
        assert entity._attr_error_code == 0
        assert entity._attr_mode == "auto"
        assert entity._attr_fan_speed == "Standard"
