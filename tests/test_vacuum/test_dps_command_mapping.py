"""Tests for mapping between command codes and DPS values."""

import pytest
from unittest.mock import patch, MagicMock

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuum import RoboVacEntity
from custom_components.robovac.vacuums.base import RobovacCommand, TuyaCodes
from homeassistant.components.vacuum import VacuumActivity
from homeassistant.const import (
    CONF_NAME,
    CONF_ID,
    CONF_MAC,
    CONF_MODEL,
    CONF_IP_ADDRESS,
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
)


def test_dps_codes_match_expected_values() -> None:
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
            assert dps_codes.get("STATUS") == TuyaCodes.STATUS
            assert dps_codes.get("BATTERY_LEVEL") == TuyaCodes.BATTERY_LEVEL
            assert dps_codes.get("ERROR_CODE") == TuyaCodes.ERROR_CODE

            # If MODE is in the codes, verify it matches
            if "MODE" in dps_codes:
                assert dps_codes.get("MODE") == TuyaCodes.MODE

            # If FAN_SPEED is in the codes, verify it matches
            if "FAN_SPEED" in dps_codes:
                assert dps_codes.get("FAN_SPEED") == TuyaCodes.FAN_SPEED


def test_nonstandard_model_dps_codes() -> None:
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
        assert dps_codes.get("STATUS") != TuyaCodes.STATUS
        assert dps_codes.get("BATTERY_LEVEL") != TuyaCodes.BATTERY_LEVEL
        assert dps_codes.get("ERROR_CODE") != TuyaCodes.ERROR_CODE
        assert dps_codes.get("FAN_SPEED") != TuyaCodes.FAN_SPEED


def test_getDpsCodes_extraction_method() -> None:
    """Test that getDpsCodes extracts codes correctly from different command formats."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        # Test T1250 (model using default codes with dictionary structure)
        vacuum_t1250 = RoboVac(
            model_code="T1250",
            device_id="test_id",
            host="192.168.1.1",
            local_key="test_key",
        )

        t1250_dps_codes = vacuum_t1250.getDpsCodes()

        # Verify T1250 has default codes but uses dictionary structure
        assert "STATUS" in t1250_dps_codes
        assert t1250_dps_codes["STATUS"] == "15"  # Default code in dict format
        assert "BATTERY_LEVEL" in t1250_dps_codes
        assert t1250_dps_codes["BATTERY_LEVEL"] == "104"  # Default code in dict format
        assert "ERROR_CODE" in t1250_dps_codes
        assert t1250_dps_codes["ERROR_CODE"] == "106"  # Default code in dict format

        # Test T2267 (model with non-default codes)
        vacuum_t2267 = RoboVac(
            model_code="T2267",
            device_id="test_id",
            host="192.168.1.1",
            local_key="test_key",
        )

        t2267_dps_codes = vacuum_t2267.getDpsCodes()

        # Verify T2267 has different codes than the defaults
        assert "STATUS" in t2267_dps_codes
        assert t2267_dps_codes["STATUS"] == "153"  # Non-default code
        assert t2267_dps_codes["STATUS"] != TuyaCodes.STATUS
        assert "BATTERY_LEVEL" in t2267_dps_codes
        assert t2267_dps_codes["BATTERY_LEVEL"] == "163"  # Non-default code
        assert t2267_dps_codes["BATTERY_LEVEL"] != TuyaCodes.BATTERY_LEVEL
        assert "ERROR_CODE" in t2267_dps_codes
        assert t2267_dps_codes["ERROR_CODE"] == "177"  # Non-default code
        assert t2267_dps_codes["ERROR_CODE"] != TuyaCodes.ERROR_CODE

        # Test T2320 (another model with non-default codes)
        vacuum_t2320 = RoboVac(
            model_code="T2320",
            device_id="test_id",
            host="192.168.1.1",
            local_key="test_key",
        )

        t2320_dps_codes = vacuum_t2320.getDpsCodes()

        # Verify T2320 has different codes too
        assert "STATUS" in t2320_dps_codes
        assert t2320_dps_codes["STATUS"] == "173"  # Non-default code
        assert t2320_dps_codes["STATUS"] != TuyaCodes.STATUS
        assert "BATTERY_LEVEL" in t2320_dps_codes
        assert t2320_dps_codes["BATTERY_LEVEL"] == "172"  # Non-default code
        assert t2320_dps_codes["BATTERY_LEVEL"] != TuyaCodes.BATTERY_LEVEL
        assert "ERROR_CODE" in t2320_dps_codes
        assert t2320_dps_codes["ERROR_CODE"] == "169"  # Non-default code
        assert t2320_dps_codes["ERROR_CODE"] != TuyaCodes.ERROR_CODE


def test_status_mapping_t2320() -> None:
    """Test T2320 status codes map to human-readable values."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        vacuum = RoboVac(
            model_code="T2320",
            device_id="test_id",
            host="192.168.1.1",
            local_key="test_key",
        )

        status = vacuum.getRoboVacHumanReadableValue(
            RobovacCommand.STATUS, "EBAFGgA6AhACcgYaAggBIgA="
        )
        assert status == "Drying Mop"

        status = vacuum.getRoboVacHumanReadableValue(
            RobovacCommand.STATUS, "ChADGgIIAXICIgA="
        )
        assert status == "Fully Charged"

        status = vacuum.getRoboVacHumanReadableValue(
            RobovacCommand.STATUS, "CgoAEAUyAHICIgA="
        )
        assert status == "Auto Cleaning"


def test_activity_mapping_fully_charged_t2320() -> None:
    """Ensure Fully Charged status maps to DOCKED activity for T2320."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        vacuum = RoboVac(
            model_code="T2320",
            device_id="test_id",
            host="192.168.1.1",
            local_key="test_key",
        )

    mapping = vacuum.getRoboVacActivityMapping()
    assert mapping.get("Fully Charged") == VacuumActivity.DOCKED


def test_activity_mapping_auto_cleaning_t2320() -> None:
    """Ensure Auto Cleaning status maps to CLEANING activity for T2320."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        vacuum = RoboVac(
            model_code="T2320",
            device_id="test_id",
            host="192.168.1.1",
            local_key="test_key",
        )

    mapping = vacuum.getRoboVacActivityMapping()
    assert mapping.get("Auto Cleaning") == VacuumActivity.CLEANING


@pytest.mark.asyncio
async def test_vacuum_update_uses_correct_dps_codes() -> None:
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
