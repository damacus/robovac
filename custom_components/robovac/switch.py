"""Switch entities for RoboVac DPS-backed toggles (edge-hugging mop)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_MODEL, CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .const import CONF_VACS, DOMAIN
from .vacuums import ROBOVAC_MODELS, resolve_model_code
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
        model_code = resolve_model_code(item.get(CONF_MODEL) or "")
        model_class = ROBOVAC_MODELS.get(model_code)
        if model_class is None:
            continue
        expose_config = getattr(model_class, "expose_config_entities", False)
        expose_dps = getattr(model_class, "expose_dps_entities", False)
        if not (expose_config or expose_dps):
            continue
        commands = getattr(model_class, "commands", {})
        if expose_config and RobovacCommand.CLEAN_PARAM in commands:
            entities.append(RobovacEdgeHuggingMopSwitch(item))
        if expose_dps and RobovacCommand.DO_NOT_DISTURB in commands:
            entities.append(
                RobovacBooleanDpsSwitch(
                    item,
                    str(commands[RobovacCommand.DO_NOT_DISTURB]["code"]),
                    "do_not_disturb",
                    "Do not disturb",
                    "mdi:minus-circle-off-outline",
                )
            )
        if expose_dps and RobovacCommand.BOOST_IQ in commands:
            entities.append(
                RobovacBooleanDpsSwitch(
                    item,
                    str(commands[RobovacCommand.BOOST_IQ]["code"]),
                    "boost_iq",
                    "BoostIQ",
                    "mdi:weather-windy",
                )
            )

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
            await self._refresh_after_write(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        vacuum_entity = self._vacuum()
        if vacuum_entity:
            await vacuum_entity.async_set_clean_param(edge_hugging_mopping=False)
            await self._refresh_after_write(False)

    async def _refresh_after_write(self, expected_state: bool) -> None:
        self._attr_available = True
        self._attr_is_on = expected_state
        self.async_write_ha_state()
        async_call_later(self.hass, 2, self._delayed_refresh_after_write)

    async def _delayed_refresh_after_write(self, _: Any) -> None:
        """Refresh again after the device has had time to echo patched DPS 154."""
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


class RobovacBooleanDpsSwitch(SwitchEntity):
    """A switch backed by one boolean Tuya datapoint."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        item: dict,
        dps_code: str,
        unique_suffix: str,
        name: str,
        icon: str,
    ) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_{unique_suffix}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_info = _device_info(item)

    @property
    def is_on(self) -> bool | None:
        return self._attr_is_on

    async def async_update(self) -> None:
        vacuum_entity = self._vacuum()
        if not (vacuum_entity and vacuum_entity.vacuum is not None):
            self._attr_available = False
            return
        raw = (vacuum_entity.tuyastatus or {}).get(self._dps_code)
        if raw is None:
            self._attr_available = False
            return
        self._attr_is_on = raw is True or str(raw).strip().casefold() in {
            "1",
            "on",
            "true",
        }
        self._attr_available = True

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_state(False)

    async def _async_set_state(self, state: bool) -> None:
        vacuum_entity = self._vacuum()
        if not (vacuum_entity and vacuum_entity.vacuum is not None):
            return
        await vacuum_entity.vacuum.async_set({self._dps_code: state})
        if vacuum_entity.tuyastatus is not None:
            vacuum_entity.tuyastatus[self._dps_code] = state
        self._attr_is_on = state
        self._attr_available = True
        self.async_write_ha_state()
        async_call_later(self.hass, 2, self._delayed_refresh_after_write)

    async def _delayed_refresh_after_write(self, _: Any) -> None:
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
