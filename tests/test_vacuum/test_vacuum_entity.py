"""Tests for the RoboVac vacuum entity."""

import base64
import json

import pytest
from unittest.mock import patch

from homeassistant.components.vacuum import VacuumActivity
from custom_components.robovac.const import CONF_ROOM_NAMES
from custom_components.robovac.vacuum import RoboVacEntity
from custom_components.robovac.vacuums.base import TuyaCodes


@pytest.mark.asyncio
async def test_activity_property_none(mock_robovac, mock_vacuum_data):
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
async def test_activity_property_error(mock_robovac, mock_vacuum_data):
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
async def test_activity_property_docked(mock_robovac, mock_vacuum_data):
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
async def test_activity_property_drying_mop(mock_robovac, mock_vacuum_data):
    """Test activity property returns DOCKED when state is Drying Mop."""
    mock_robovac.getRoboVacActivityMapping.return_value = {
        "Drying Mop": VacuumActivity.DOCKED
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = "Drying Mop"

        result = entity.activity

        assert result == VacuumActivity.DOCKED


@pytest.mark.asyncio
async def test_activity_property_returning(mock_robovac, mock_vacuum_data):
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
async def test_activity_property_idle(mock_robovac, mock_vacuum_data):
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
async def test_activity_property_paused(mock_robovac, mock_vacuum_data):
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
async def test_activity_property_cleaning(mock_robovac, mock_vacuum_data):
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
async def test_update_entity_values(mock_robovac, mock_vacuum_data):
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
        assert entity._attr_battery_level == 75
        assert entity.tuya_state == "Cleaning"
        assert entity.error_code == 0
        assert entity._attr_mode == "auto"
        assert entity._attr_fan_speed == "Standard"


@pytest.mark.asyncio
async def test_fan_speed_formatting(mock_robovac, mock_vacuum_data):
    """Test fan speed formatting in update_entity_values."""
    # Arrange
    test_cases = [
        ("No_suction", "No Suction"),
        ("Boost_IQ", "Boost IQ"),
        ("Quiet", "Pure"),
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


@pytest.mark.asyncio
async def test_update_entity_values_decodes_room_names(mock_robovac, mock_vacuum_data):
    """Room metadata embedded in the room clean DPS is decoded into labels."""

    mock_robovac.getDpsCodes.return_value = {"ROOM_CLEAN": "168"}
    room_payload = base64.b64encode(
        json.dumps(
            {
                "method": "syncMultiMapRoomList",
                "data": {
                    "rooms": [
                        {"roomId": 1, "roomName": "Kitchen"},
                        {"roomId": 3, "label": "Bedroom"},
                        {"roomId": "uuid-4", "name": "Office"},
                    ]
                },
            }
        ).encode("utf-8")
    ).decode("utf-8")
    mock_robovac._dps = {"168": room_payload}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.update_entity_values()

    assert entity._attr_room_names is not None
    assert entity._attr_room_names["1"]["label"] == "Kitchen"
    assert entity._attr_room_names["1"]["device_label"] == "Kitchen"
    assert entity._attr_room_names["1"]["source"] == "device"
    assert entity._attr_room_names["1"]["key"] == "1"
    assert entity._attr_room_names["3"]["label"] == "Bedroom"
    assert entity._attr_room_names["3"]["source"] == "device"
    assert entity._attr_room_names["uuid-4"]["label"] == "Office"
    assert entity._attr_room_names["uuid-4"]["source"] == "device"


@pytest.mark.asyncio
async def test_room_name_overrides_take_precedence(mock_robovac, mock_vacuum_data):
    """Configured overrides replace discovered room labels."""

    mock_vacuum_data[CONF_ROOM_NAMES] = {"3": "Guest Room"}
    mock_robovac.getDpsCodes.return_value = {"ROOM_CLEAN": "168"}
    room_payload = base64.b64encode(
        json.dumps(
            {
                "method": "syncMultiMapRoomList",
                "data": {"rooms": [{"roomId": 3, "roomName": "Bedroom"}]},
            }
        ).encode("utf-8")
    ).decode("utf-8")
    mock_robovac._dps = {"168": room_payload}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.update_entity_values()

    assert entity._attr_room_names is not None
    assert entity._attr_room_names["3"]["label"] == "Guest Room"


@pytest.mark.asyncio
async def test_known_room_payload_mapping(mock_robovac, mock_vacuum_data):
    """Non-JSON room payloads map to known room labels when recognised."""

    mock_robovac.getDpsCodes.return_value = {"ROOM_CLEAN": "168"}
    mock_robovac._dps = {
        "168": "KAomCgIIZBIDCI4CGgMIjgIiAghkKgIIZDIDCJ4BoAG4x7Lu/9HAuhg=",
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.update_entity_values()

    assert entity._attr_room_names is not None
    assert entity._attr_room_names["100"]["label"] == "Living Room"
