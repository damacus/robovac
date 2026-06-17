"""Tests for the RoboVac vacuum entity."""

import base64
import pytest
from typing import Any
from unittest.mock import AsyncMock, patch, MagicMock

from homeassistant.components.vacuum import VacuumActivity, VacuumEntityFeature
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
)
from custom_components.robovac.const import CONF_ROOM_SEGMENT_MAP_ID, CONF_ROOM_SEGMENTS
from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuum import (
    ATTR_ERROR,
    RoboVacEntity,
    _parse_clean_count,
    _parse_room_segment_map_id,
    _parse_room_segments,
)
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
async def test_error_attribute_uses_error_message(mock_robovac, mock_vacuum_data) -> None:
    """Test error attribute displays actual error details when present."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = "Cleaning"
        entity.error_code = "Wheel_stuck"

        assert entity.activity == VacuumActivity.ERROR
        assert entity.state == VacuumActivity.ERROR
        assert entity.extra_state_attributes[ATTR_ERROR] == "Wheel stuck"


@pytest.mark.asyncio
async def test_no_error_text_is_not_error_attribute(mock_robovac, mock_vacuum_data) -> None:
    """Test decoded 'No error' text is not exposed as an active error."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuya_state = "Charging"
        entity.error_code = "No error"

        assert entity.activity == VacuumActivity.DOCKED
        assert ATTR_ERROR not in entity.extra_state_attributes


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


def test_t2320_room_discovery_strategy_uses_local_room_meta(
    mock_robovac: MagicMock, mock_vacuum_data: dict[str, Any]
) -> None:
    """Test T2320 room discovery decodes the configured local DPS payload."""
    data = dict(mock_vacuum_data)
    data[CONF_MODEL] = "T2320"
    mock_robovac.getDpsCodes.return_value = {"ROOM_META": "165"}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(data)
        entity.tuyastatus = {"165": "room-payload"}

        with patch.object(
            entity,
            "_decode_t2320_room_meta",
            return_value={"map_id": 7, "rooms": [{"id": 3, "label": "Kitchen"}]},
        ) as decode:
            entity._update_room_names_from_device_payload()

    decode.assert_called_once_with("room-payload")
    assert entity._attr_room_map_id == 7
    assert entity._attr_room_names == {
        "3": {"id": 3, "key": "3", "label": "Kitchen", "source": "device"}
    }


def test_t2320_room_discovery_strategy_falls_back_to_dps_165(
    mock_robovac: MagicMock, mock_vacuum_data: dict[str, Any]
) -> None:
    """Test room discovery uses DPS 165 when model DPS codes do not expose ROOM_META."""
    data = dict(mock_vacuum_data)
    data[CONF_MODEL] = "T2320"
    mock_robovac.getDpsCodes.return_value = {}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(data)
        entity.tuyastatus = {"165": "fallback-payload"}

        with patch.object(
            entity,
            "_decode_t2320_room_meta",
            return_value={"map_id": 8, "rooms": [{"id": 4, "label": "Hall"}]},
        ) as decode:
            assert entity._discover_room_meta_from_local_dps() == {
                "map_id": 8,
                "rooms": [{"id": 4, "label": "Hall"}],
            }

    decode.assert_called_once_with("fallback-payload")


def test_non_room_discovery_model_ignores_room_meta_strategy(
    mock_robovac: MagicMock, mock_vacuum_data: dict[str, Any]
) -> None:
    """Test models without a strategy do not attempt room metadata discovery."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.tuyastatus = {"165": "ignored"}

        assert entity._supports_room_discovery() is False
        assert entity._discover_room_meta_from_local_dps() == {
            "map_id": None,
            "rooms": [],
        }


def test_t2320_room_discovery_strategy_uses_cloud_fetcher(
    mock_robovac: MagicMock, mock_vacuum_data: dict[str, Any]
) -> None:
    """Test cloud room discovery decodes DPS from the configured fetcher."""
    data = dict(mock_vacuum_data)
    data[CONF_MODEL] = "T2320"
    mock_robovac.getDpsCodes.return_value = {"ROOM_META": "165"}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(data)

        with (
            patch.object(
                entity,
                "_fetch_t2320_dps_from_cloud_sync",
                return_value={"dps": {"165": "cloud-payload"}},
            ) as fetch,
            patch.object(
                entity,
                "_decode_t2320_room_meta",
                return_value={"map_id": 9, "rooms": [{"id": 5, "label": "Office"}]},
            ) as decode,
        ):
            assert entity._fetch_room_meta_from_cloud_sync() == {
                "map_id": 9,
                "rooms": [{"id": 5, "label": "Office"}],
            }

    fetch.assert_called_once_with()
    decode.assert_called_once_with("cloud-payload")


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
async def test_activity_property_error_overrides_docked_return_progress() -> None:
    """Test active errors take precedence over stale docked return-progress payloads."""
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
            "177": base64.b64encode(bytes([3, 0x12, 0x01, 52])).decode(),
        }
        entity.update_entity_values()

        assert entity._return_progress_activity() == VacuumActivity.DOCKED
        assert entity.error_code == "Unable to leave station"
        assert entity.activity == VacuumActivity.ERROR


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


def test_cloud_dps_map_accepts_flat_and_nested_responses() -> None:
    """Tuya cloud may return either a flat DPS map or {'dps': {...}}."""
    assert RoboVacEntity._cloud_dps_map({"165": "flat"}) == {"165": "flat"}
    assert RoboVacEntity._cloud_dps_map({"dps": {"165": "nested"}}) == {"165": "nested"}


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
    segments = _parse_room_segments(
        "1:Kitchen, , bad, nope:Study, 2: Living Room, 3:"
    )

    assert [(segment.id, segment.name) for segment in segments] == [
        (1, "Kitchen"),
        (2, "Living Room"),
    ]


def test_room_segment_parser_fallbacks() -> None:
    """Test defensive parsing for configured segment controls."""
    assert _parse_room_segment_map_id(None) == 1
    assert _parse_room_segment_map_id("") == 1
    assert _parse_room_segment_map_id("bad") == 1
    assert _parse_clean_count("bad") == 1
    assert _parse_clean_count(0) == 1


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
async def test_async_get_segments_without_segments_returns_empty(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test no cleanable segments are exposed when none are configured/discovered."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

    assert await entity.async_get_segments() == []


@pytest.mark.asyncio
async def test_async_get_segments_uses_discovered_rooms(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test discovered room metadata is exposed when no manual segments exist."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

    entity._attr_room_names = {
        "room_1": {"id": 1, "label": "Kitchen"},
        "room_2": {"id": 2, "label": "Living Room"},
    }

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
async def test_async_clean_segments_ignores_empty_selection(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test segment cleaning does not dispatch when no supplied IDs are valid."""
    data = {
        **mock_vacuum_data,
        CONF_ROOM_SEGMENT_MAP_ID: 3,
        CONF_ROOM_SEGMENTS: "1:Kitchen,2:Living Room",
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(data)

    entity.async_send_command = AsyncMock()
    await entity.async_clean_segments(["bad", "99"])

    entity.async_send_command.assert_not_awaited()


@pytest.mark.asyncio
async def test_partial_startup_dps_sets_idle(mock_robovac, mock_vacuum_data) -> None:
    """Test partial startup DPS without status recovers HA from unknown."""
    mock_robovac._dps = {
        "151": True,
        "156": True,
        "158": "Standard",
        "159": True,
        "160": False,
        "161": 80,
        "163": 61,
    }
    mock_robovac.getDpsCodes.return_value = {
        "MODE": "152",
        "STATUS": "173",
        "RETURN_HOME": "153",
        "FAN_SPEED": "154",
        "LOCATE": "153",
        "BATTERY_LEVEL": "172",
        "ERROR_CODE": "169",
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        entity.update_entity_values()

        assert entity.activity == VacuumActivity.IDLE


@pytest.mark.asyncio
async def test_partial_startup_dps_keeps_explicit_status(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test partial-DPS fallback does not override explicit status."""
    mock_robovac._dps = {
        "151": True,
        "156": True,
        "158": "Standard",
        "159": True,
        "160": False,
        "161": 80,
        "163": 61,
        "173": "Charging",
    }
    mock_robovac.getDpsCodes.return_value = {
        "MODE": "152",
        "STATUS": "173",
        "RETURN_HOME": "153",
        "FAN_SPEED": "154",
        "LOCATE": "153",
        "BATTERY_LEVEL": "172",
        "ERROR_CODE": "169",
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        entity.update_entity_values()

        assert entity.tuya_state == "Charging"


@pytest.mark.asyncio
async def test_battery_only_dps_does_not_set_idle(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test battery-only updates are not enough to infer idle."""
    mock_robovac._dps = {"163": 74}
    mock_robovac.getDpsCodes.return_value = {
        "MODE": "152",
        "STATUS": "173",
        "RETURN_HOME": "153",
        "FAN_SPEED": "154",
        "LOCATE": "153",
        "BATTERY_LEVEL": "172",
        "ERROR_CODE": "169",
    }

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        entity.update_entity_values()

        assert entity.activity is None


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
