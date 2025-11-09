"""Tests covering the RoboVac select platform."""
from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import CONF_ID

from custom_components.robovac.const import CONF_VACS, DOMAIN
from custom_components.robovac.select import (
    CLEAN_WHOLE_HOUSE_OPTION,
    RobovacRoomSelect,
    async_setup_entry as async_setup_room_select,
)
from custom_components.robovac.vacuum import RoboVacEntity


async def _setup_select_entity(
    hass,
    vacuum_entity: RoboVacEntity,
    vacuum_data: dict,
) -> RobovacRoomSelect:
    """Helper to set up the select platform and return the created entity."""

    hass.data = {DOMAIN: {CONF_VACS: {vacuum_data[CONF_ID]: vacuum_entity}}}
    vacuum_entity.hass = hass
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_VACS: {vacuum_data[CONF_ID]: vacuum_data}},
    )

    added_entities: list = []

    async def _async_add_entities(entities, update_before_add: bool = False) -> None:
        for entity in entities:
            entity.hass = hass
        added_entities.extend(entities)

    await async_setup_room_select(hass, config_entry, _async_add_entities)
    await hass.async_block_till_done()
    return added_entities[0]


@pytest.mark.asyncio
async def test_select_options_reflect_room_names(
    hass, mock_vacuum_data, mock_robovac
) -> None:
    """Ensure the select entity exposes whole house and room options."""

    mock_robovac.getDpsCodes.return_value = {"ROOM_CLEAN": "168"}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        vacuum_entity = RoboVacEntity(mock_vacuum_data)

    vacuum_entity._attr_room_names = {
        "2": {"id": 2, "label": "Bedroom"},
        "1": {"id": 1, "label": "Kitchen"},
        "3": {"id": 3},
    }

    select_entity = await _setup_select_entity(hass, vacuum_entity, mock_vacuum_data)

    assert select_entity.options == [
        CLEAN_WHOLE_HOUSE_OPTION,
        "3",
        "Bedroom",
        "Kitchen",
    ]
    assert select_entity.current_option is None


@pytest.mark.asyncio
async def test_select_whole_house_triggers_auto_clean(
    hass, mock_vacuum_data, mock_robovac
) -> None:
    """Selecting whole house should start the vacuum in auto mode."""

    mock_robovac.getDpsCodes.return_value = {"ROOM_CLEAN": "168"}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        vacuum_entity = RoboVacEntity(mock_vacuum_data)

    vacuum_entity.async_start = AsyncMock()
    vacuum_entity.async_send_command = AsyncMock()

    select_entity = await _setup_select_entity(hass, vacuum_entity, mock_vacuum_data)

    await select_entity.async_select_option(CLEAN_WHOLE_HOUSE_OPTION)

    vacuum_entity.async_start.assert_awaited_once()
    vacuum_entity.async_send_command.assert_awaited_once_with("autoClean")
    assert select_entity.current_option == CLEAN_WHOLE_HOUSE_OPTION


@pytest.mark.asyncio
async def test_select_room_triggers_room_clean_payload(
    hass, mock_vacuum_data, mock_robovac
) -> None:
    """Selecting a room should issue the encoded room clean payload."""

    mock_robovac.getDpsCodes.return_value = {"ROOM_CLEAN": "168"}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        vacuum_entity = RoboVacEntity(mock_vacuum_data)

    vacuum_entity._attr_room_names = {
        "1": {"id": 1, "label": "Kitchen"},
    }

    select_entity = await _setup_select_entity(hass, vacuum_entity, mock_vacuum_data)

    await select_entity.async_select_option("Kitchen")

    assert mock_robovac.async_set.await_count == 1
    payload = mock_robovac.async_set.await_args.args[0]
    assert "168" in payload

    encoded = payload["168"]
    decoded = json.loads(base64.b64decode(encoded))
    assert decoded["method"] == "selectRoomsClean"
    assert decoded["data"] == {"roomIds": [1], "cleanTimes": 1}
    assert select_entity.current_option == "Kitchen"


@pytest.mark.asyncio
async def test_select_entity_tracks_room_name_updates(
    hass, mock_vacuum_data, mock_robovac
) -> None:
    """Room discovery updates trigger a select entity state refresh."""

    mock_robovac.getDpsCodes.return_value = {"ROOM_CLEAN": "168"}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        vacuum_entity = RoboVacEntity(mock_vacuum_data)

    select_entity = await _setup_select_entity(hass, vacuum_entity, mock_vacuum_data)

    with patch.object(select_entity, "async_write_ha_state") as mock_write:
        vacuum_entity._room_name_registry["1"] = {"id": 1, "label": "Living Room"}
        vacuum_entity._refresh_room_names_attr()
        await hass.async_block_till_done()

    assert "Living Room" in select_entity.options
    mock_write.assert_called()
