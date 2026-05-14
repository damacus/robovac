"""Tests for the RoboVac vacuum entity."""

import pytest
from typing import Any
from unittest.mock import patch, MagicMock

from homeassistant.components.vacuum import VacuumActivity
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
)
from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuum import RoboVacEntity
from custom_components.robovac.vacuums.base import TuyaCodes


@pytest.mark.asyncio
async def test_activity_property_none(mock_robovac, mock_vacuum_data) -> None:
    """Test activity property returns None when tuya_state is None."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = None

        # Act
        result = entity.activity

        # Assert
        assert result is None


@pytest.mark.asyncio
async def test_activity_property_uses_mode_without_status(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test mode DPS drives activity when no status DPS has been received."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = None
        entity.error_code = "no_error"

        entity._attr_mode = "auto"
        assert entity.activity == VacuumActivity.CLEANING

        entity._attr_mode = "pause"
        assert entity.activity == VacuumActivity.PAUSED

        entity._attr_mode = "return"
        assert entity.activity == VacuumActivity.RETURNING


@pytest.mark.asyncio
async def test_activity_property_idle_when_dps_has_no_status_or_mode(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test a connected vacuum with no active status/mode reports idle."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = None
        entity.error_code = "no_error"
        entity.tuyastatus = {"158": "Standard", "163": 39}

        assert entity.activity == VacuumActivity.IDLE


@pytest.mark.asyncio
async def test_activity_property_error(mock_robovac, mock_vacuum_data) -> None:
    """Test activity property returns ERROR when error_code is set."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = "Cleaning"
        entity.error_code = "E001"

        # Act
        result = entity.activity

        # Assert
        assert result == VacuumActivity.ERROR


@pytest.mark.asyncio
async def test_activity_property_docked(mock_robovac, mock_vacuum_data) -> None:
    """Test activity property returns DOCKED when state is Charging or completed."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Test for "Charging" state
        entity.tuya_state = "Charging"
        entity.error_code = 0

        # Act
        result = entity.activity

        # Assert
        assert result == VacuumActivity.DOCKED

        # Test for "completed" state
        entity.tuya_state = "completed"

        # Act
        result = entity.activity

        # Assert
        assert result == VacuumActivity.DOCKED


@pytest.mark.asyncio
async def test_activity_property_returning(mock_robovac, mock_vacuum_data) -> None:
    """Test activity property returns RETURNING when state is Recharge."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = "Recharge"
        entity.error_code = 0

        # Act
        result = entity.activity

        # Assert
        assert result == VacuumActivity.RETURNING


@pytest.mark.asyncio
async def test_activity_property_idle(mock_robovac, mock_vacuum_data) -> None:
    """Test activity property returns IDLE when state is Sleeping or standby."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.error_code = 0

        # Test for "Sleeping" state
        entity.tuya_state = "Sleeping"

        # Act
        result = entity.activity

        # Assert
        assert result == VacuumActivity.IDLE

        # Test for "standby" state
        entity.tuya_state = "standby"

        # Act
        result = entity.activity

        # Assert
        assert result == VacuumActivity.IDLE


@pytest.mark.asyncio
async def test_activity_property_paused(mock_robovac, mock_vacuum_data) -> None:
    """Test activity property returns PAUSED when state is Paused."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = "Paused"
        entity.error_code = 0

        # Act
        result = entity.activity

        # Assert
        assert result == VacuumActivity.PAUSED


@pytest.mark.asyncio
async def test_activity_property_cleaning(mock_robovac, mock_vacuum_data) -> None:
    """Test activity property returns CLEANING for other states."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = "Cleaning"
        entity.error_code = 0

        # Act
        result = entity.activity

        # Assert
        assert result == VacuumActivity.CLEANING


@pytest.mark.asyncio
async def test_activity_property_uses_mode_when_status_is_idle(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test active mode DPS overrides station-idle status for T2320-like models."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity._attr_activity_mapping = {"idle": VacuumActivity.IDLE}
        entity.tuya_state = "idle"
        entity.error_code = "no_error"

        entity._attr_mode = "auto"
        assert entity.activity == VacuumActivity.CLEANING

        entity._attr_mode = "pause"
        assert entity.activity == VacuumActivity.PAUSED

        entity._attr_mode = "return"
        assert entity.activity == VacuumActivity.RETURNING


@pytest.mark.asyncio
async def test_activity_property_uses_return_progress_over_stale_return_mode() -> None:
    """Test T2320 dock progress overrides stale DPS 152 return mode."""
    data = {
        CONF_NAME: "Test X9",
        CONF_ID: "test_x9_id",
        CONF_MODEL: "T2320",
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_key",
        CONF_DESCRIPTION: "X9 Pro",
        CONF_MAC: "aa:bb:cc:dd:ee:99",
    }
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2320",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=robovac):
        entity = RoboVacEntity(data)
        robovac._dps = {
            "152": "AggG",
            "153": "DhAFGgA6AhABcgQaACIA",
            "173": "LgokCgwKBggBGgIIChIAGAESBggBEgIIAjIMCgIIARIGCAEQARgPEgIIASoCCFg=",
        }
        entity.update_entity_values()

        assert entity.mode == "return"
        assert entity.activity == VacuumActivity.DOCKED


@pytest.mark.asyncio
async def test_activity_property_uses_return_progress_cleaning_signal() -> None:
    """Test T2320 active cleaning DPS 153 overrides standby/idle status."""
    data = {
        CONF_NAME: "Test X9",
        CONF_ID: "test_x9_id",
        CONF_MODEL: "T2320",
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_key",
        CONF_DESCRIPTION: "X9 Pro",
        CONF_MAC: "aa:bb:cc:dd:ee:99",
    }
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2320",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=robovac):
        entity = RoboVacEntity(data)
        robovac._dps = {
            "152": "AA==",
            "153": "CgoAEAUyAHICIgA=",
            "173": "LgokCgwKBggBGgIIChIAGAESBggBEgIIAjIMCgIIARIGCAEQARgPEgIIASoCCFg=",
        }
        entity.update_entity_values()

        assert entity.mode == "standby"
        assert entity.activity == VacuumActivity.CLEANING


@pytest.mark.asyncio
async def test_update_entity_values(mock_robovac, mock_vacuum_data) -> None:
    """Test update_entity_values correctly sets entity attributes."""
    # Arrange
    mock_robovac._dps = {
        TuyaCodes.BATTERY_LEVEL: 75,
        TuyaCodes.STATUS: "Cleaning",
        TuyaCodes.ERROR_CODE: 0,
        TuyaCodes.MODE: "auto",
        TuyaCodes.FAN_SPEED: "Standard",
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act
        entity.update_entity_values()

        # Assert
        # Battery level is now handled by separate sensor entity
        assert entity.tuya_state == "Cleaning"
        assert entity.error_code == 0
        assert entity._attr_mode == "auto"
        assert entity._attr_fan_speed == "Standard"


@pytest.mark.asyncio
async def test_fan_speed_formatting(mock_robovac, mock_vacuum_data) -> None:
    """Test fan speed formatting in update_entity_values."""
    # Arrange
    test_cases = [
        ("No_suction", "No Suction"),
        ("Boost_IQ", "Boost IQ"),
        ("Quiet", "Quiet"),
        ("Standard", "Standard"),  # No change
    ]

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        for input_speed, expected_output in test_cases:
            # Setup
            mock_robovac._dps = {TuyaCodes.FAN_SPEED: input_speed}

            # Act
            entity.update_entity_values()

            # Assert
            assert (
                entity._attr_fan_speed == expected_output
            ), f"Failed for input: {input_speed}"
