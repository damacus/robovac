"""Tests for the RoboVac vacuum entity."""

import pytest
from typing import Any
from unittest.mock import AsyncMock, patch, MagicMock

from homeassistant.components.vacuum import VacuumActivity, VacuumEntityFeature
from homeassistant.const import CONF_ID

from custom_components.robovac.const import CONF_ROOM_SEGMENT_MAP_ID, CONF_ROOM_SEGMENTS
from custom_components.robovac.vacuum import RoboVacEntity, _parse_room_segments
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


def test_parse_room_segments() -> None:
    """Test configured room segment parsing."""
    segments = _parse_room_segments("1:Kitchen, bad, nope:Study, 2: Living Room, 3:")

    assert [(segment.id, segment.name) for segment in segments] == [
        (1, "Kitchen"),
        (2, "Living Room"),
    ]


def test_clean_area_feature_enabled_only_with_segments(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test CLEAN_AREA is enabled only when segments are configured."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        assert not entity.supported_features & VacuumEntityFeature.CLEAN_AREA

    segmented_data = {
        **mock_vacuum_data,
        CONF_ROOM_SEGMENT_MAP_ID: 3,
        CONF_ROOM_SEGMENTS: "1:Kitchen,2:Living Room",
    }
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(segmented_data)
        assert entity.supported_features & VacuumEntityFeature.CLEAN_AREA


@pytest.mark.asyncio
async def test_async_get_segments(mock_robovac, mock_vacuum_data) -> None:
    """Test Home Assistant segment metadata is returned from configured rooms."""
    data = {
        **mock_vacuum_data,
        CONF_ROOM_SEGMENT_MAP_ID: 3,
        CONF_ROOM_SEGMENTS: "1:Kitchen,2:Living Room",
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(data)

    segments = await entity.async_get_segments()

    assert [(segment.id, segment.name) for segment in segments] == [
        ("1", "Kitchen"),
        ("2", "Living Room"),
    ]


@pytest.mark.asyncio
async def test_async_clean_segments_maps_to_room_clean(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test segment cleaning validates IDs and calls roomClean."""
    data = {
        **mock_vacuum_data,
        CONF_ID: "test_robovac_id",
        CONF_ROOM_SEGMENT_MAP_ID: 3,
        CONF_ROOM_SEGMENTS: "1:Kitchen,2:Living Room",
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(data)

    entity.async_send_command = AsyncMock()
    await entity.async_clean_segments(["2", "bad", "99"], repeats=2)

    entity.async_send_command.assert_awaited_once_with(
        "roomClean",
        {
            "room_ids": [2],
            "map_id": 3,
            "count": 2,
        },
    )


@pytest.mark.asyncio
async def test_fan_speed_formatting(mock_robovac, mock_vacuum_data) -> None:
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
