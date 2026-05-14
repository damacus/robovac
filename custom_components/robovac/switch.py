"""Switch entities for RoboVac DPS-backed toggles (edge-hugging mop)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_MODEL, CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VACS, DOMAIN
from .vacuums import ROBOVAC_MODELS
from .vacuums.base import RobovacCommand

if TYPE_CHECKING:
    from .vacuum import RoboVacEntity


def _device_info(item: dict) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, item[CONF_ID])},
        name=item[CONF_NAME],
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RoboVac switch entities."""
    vacuums = config_entry.data[CONF_VACS]
    entities: list[SwitchEntity] = []

    for key in vacuums:
        item = vacuums[key]
        model_prefix = (item.get(CONF_MODEL) or "")[:5]
        model_class = ROBOVAC_MODELS.get(model_prefix)
        if model_class is None:
            continue
        if not getattr(model_class, "expose_config_entities", False):
            continue
        commands = getattr(model_class, "commands", {})
        if RobovacCommand.CLEAN_PARAM not in commands:
            continue
        entities.append(RobovacEdgeHuggingMopSwitch(item))

    async_add_entities(entities)


class RobovacEdgeHuggingMopSwitch(SwitchEntity):
    """Toggle edge-hugging mop path (DPS 154 MopMode bit)."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:radius-outline"

    @property
    def is_on(self) -> bool | None:
        """Bypass ToggleEntity.cached_property so _attr_is_on updates are visible."""
        return self._attr_is_on

    def __init__(self, item: dict) -> None:
        self.robovac_id = item[CONF_ID]
        self._attr_unique_id = f"{item[CONF_ID]}_edge_hugging_mop"
        self._attr_name = "Edge mopping"
        self._attr_device_info = _device_info(item)

    async def async_update(self) -> None:
        try:
            vacuum_entity: RoboVacEntity | None = self.hass.data[DOMAIN][CONF_VACS].get(
                self.robovac_id
            )
        except KeyError:
            vacuum_entity = None
        if not (vacuum_entity and vacuum_entity.vacuum is not None):
            self._attr_available = False
            return
        self._attr_available = True
        val = vacuum_entity.edge_hugging_mopping
        self._attr_is_on = val

    async def async_turn_on(self, **kwargs: Any) -> None:
        vacuum_entity = self._vacuum()
        if vacuum_entity:
            await vacuum_entity.async_set_clean_param(edge_hugging_mopping=True)
            await self._refresh_after_write()

    async def async_turn_off(self, **kwargs: Any) -> None:
        vacuum_entity = self._vacuum()
        if vacuum_entity:
            await vacuum_entity.async_set_clean_param(edge_hugging_mopping=False)
            await self._refresh_after_write()

    async def _refresh_after_write(self) -> None:
        await self.async_update()
        self.async_write_ha_state()
        await asyncio.sleep(2)
        await self.async_update()
        self.async_write_ha_state()

    def _vacuum(self) -> RoboVacEntity | None:
        try:
            return cast(
                "RoboVacEntity | None",
                self.hass.data[DOMAIN][CONF_VACS].get(self.robovac_id),
            )
        except KeyError:
            return None
