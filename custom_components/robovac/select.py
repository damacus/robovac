"""Select entities for RoboVac DPS-backed settings (clean type, mop level, fan speed)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from homeassistant.components.select import SelectEntity
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

_CLEAN_TYPE_LABELS_ALL = {
    "sweep_only": "Sweep only",
    "mop_only": "Mop only",
    "sweep_and_mop": "Vacuum and mop",
    "sweep_then_mop": "Vacuum then mop",
}
_DEFAULT_CLEAN_TYPE_KEYS = tuple(_CLEAN_TYPE_LABELS_ALL.keys())

_MOP_LEVEL_TO_OPTION = {"low": "Low", "middle": "Middle", "high": "High"}
_OPTION_TO_MOP_LEVEL = {v: k for k, v in _MOP_LEVEL_TO_OPTION.items()}


class _RobovacSelectEntity(SelectEntity):
    """Base that bypasses SelectEntity cached_property for options/current_option.

    HA caches the first return value of options/current_option; our values are
    filled after the vacuum reports DPS, so we always read _attr_* directly.
    """

    @property
    def options(self) -> list[str]:
        return self._attr_options

    @property
    def current_option(self) -> str | None:
        return self._attr_current_option


def _vacuum_ready(vacuum_entity: RoboVacEntity | None) -> bool:
    """True when the vacuum object exists and can accept setting commands."""
    return bool(vacuum_entity and vacuum_entity.vacuum is not None)


def _match_fan_speed_option(current: str, options: list[str]) -> str | None:
    """Pick the fan_speed_list entry that matches the vacuum's displayed fan string."""
    cur = str(current).strip()
    if not cur:
        return None
    folded = cur.casefold()
    for opt in options:
        if opt == cur or str(opt).casefold() == folded:
            return opt
    return None


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
    """Set up RoboVac select entities."""
    vacuums = config_entry.data[CONF_VACS]
    entities: list[SelectEntity] = []

    for key in vacuums:
        item = vacuums[key]
        model_prefix = (item.get(CONF_MODEL) or "")[:5]
        model_class = ROBOVAC_MODELS.get(model_prefix)
        if model_class is None:
            continue
        if not getattr(model_class, "expose_config_entities", False):
            continue
        commands = getattr(model_class, "commands", {})
        if RobovacCommand.FAN_SPEED in commands:
            entities.append(RobovacFanSpeedSelect(item))

        if RobovacCommand.CLEAN_PARAM in commands:
            dps = str(commands[RobovacCommand.CLEAN_PARAM]["code"])
            clean_keys: tuple[str, ...] = getattr(
                model_class, "clean_type_select_keys", _DEFAULT_CLEAN_TYPE_KEYS
            )
            entities.append(RobovacCleanTypeSelect(item, dps, clean_keys))
            entities.append(RobovacMopLevelSelect(item, dps))

    async_add_entities(entities)


class RobovacCleanTypeSelect(_RobovacSelectEntity):
    """Select clean type (sweep / mop / both) via DPS 154 protobuf patch."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:broom"

    def __init__(self, item: dict, dps_code: str, clean_type_keys: tuple[str, ...]) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._snake_to_label = {
            k: _CLEAN_TYPE_LABELS_ALL[k]
            for k in clean_type_keys
            if k in _CLEAN_TYPE_LABELS_ALL
        }
        self._label_to_snake = {v: k for k, v in self._snake_to_label.items()}
        self._attr_unique_id = f"{item[CONF_ID]}_clean_type_select"
        self._attr_name = "Clean type"
        self._attr_device_info = _device_info(item)
        self._attr_options = list(self._snake_to_label.values())

    async def async_update(self) -> None:
        try:
            vacuum_entity: RoboVacEntity | None = self.hass.data[DOMAIN][CONF_VACS].get(
                self.robovac_id
            )
        except KeyError:
            vacuum_entity = None
        if not _vacuum_ready(vacuum_entity):
            self._attr_available = False
            self._attr_current_option = None
            return
        vacuum_entity = cast("RoboVacEntity", vacuum_entity)
        self._attr_available = True
        ct = vacuum_entity.clean_type
        if ct is None:
            self._attr_current_option = None
            return
        key = str(ct).lower().replace(" ", "_").replace("-", "_")
        opt = self._snake_to_label.get(key)
        if opt is None and key == "sweep_then_mop" and "sweep_and_mop" in self._snake_to_label:
            opt = self._snake_to_label["sweep_and_mop"]
        self._attr_current_option = opt

    async def async_select_option(self, option: str) -> None:
        try:
            vacuum_entity: RoboVacEntity | None = self.hass.data[DOMAIN][CONF_VACS].get(
                self.robovac_id
            )
        except KeyError:
            vacuum_entity = None
        if not vacuum_entity:
            return
        snake = self._label_to_snake.get(option, option.lower().replace(" ", "_"))
        await vacuum_entity.async_set_clean_param(clean_type=snake)
        await self.async_update()
        self.async_write_ha_state()


class RobovacMopLevelSelect(_RobovacSelectEntity):
    """Select mop water level via DPS 154 protobuf patch."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:cup-water"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_mop_level_select"
        self._attr_name = "Mop level"
        self._attr_device_info = _device_info(item)
        self._attr_options = list(_MOP_LEVEL_TO_OPTION.values())

    async def async_update(self) -> None:
        try:
            vacuum_entity: RoboVacEntity | None = self.hass.data[DOMAIN][CONF_VACS].get(
                self.robovac_id
            )
        except KeyError:
            vacuum_entity = None
        if not _vacuum_ready(vacuum_entity):
            self._attr_available = False
            self._attr_current_option = None
            return
        vacuum_entity = cast("RoboVacEntity", vacuum_entity)
        self._attr_available = True
        ml = vacuum_entity.mop_level
        if ml is None:
            self._attr_current_option = None
            return
        key = str(ml).lower().replace(" ", "_")
        opt = _MOP_LEVEL_TO_OPTION.get(key)
        self._attr_current_option = opt

    async def async_select_option(self, option: str) -> None:
        try:
            vacuum_entity: RoboVacEntity | None = self.hass.data[DOMAIN][CONF_VACS].get(
                self.robovac_id
            )
        except KeyError:
            vacuum_entity = None
        if not vacuum_entity:
            return
        snake = _OPTION_TO_MOP_LEVEL.get(option, option.lower())
        await vacuum_entity.async_set_mop_level(snake)
        await self.async_update()
        self.async_write_ha_state()


class RobovacFanSpeedSelect(_RobovacSelectEntity):
    """Fan / suction level (same DPS as the vacuum card, exposed under Configuration)."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:fan"

    def __init__(self, item: dict) -> None:
        self.robovac_id = item[CONF_ID]
        self._attr_unique_id = f"{item[CONF_ID]}_fan_speed_select"
        self._attr_name = "Fan speed"
        self._attr_device_info = _device_info(item)
        model_prefix = (item.get(CONF_MODEL) or "")[:5]
        model_class = ROBOVAC_MODELS.get(model_prefix)
        values: dict[str, str] = {}
        if model_class is not None:
            command = getattr(model_class, "commands", {}).get(RobovacCommand.FAN_SPEED, {})
            values = command.get("values", {}) if isinstance(command, dict) else {}
        self._attr_options = [
            key.replace("_", " ").title()
            for key in values
        ]

    async def async_update(self) -> None:
        try:
            vacuum_entity: RoboVacEntity | None = self.hass.data[DOMAIN][CONF_VACS].get(
                self.robovac_id
            )
        except KeyError:
            vacuum_entity = None
        if not _vacuum_ready(vacuum_entity):
            self._attr_available = False
            self._attr_current_option = None
            return
        vacuum_entity = cast("RoboVacEntity", vacuum_entity)
        opts = list(vacuum_entity.fan_speed_list or self._attr_options)
        if not opts:
            self._attr_available = False
            self._attr_current_option = None
            return
        self._attr_options = opts
        self._attr_available = True
        cur = vacuum_entity.fan_speed
        if not cur:
            self._attr_current_option = None
            return
        self._attr_current_option = _match_fan_speed_option(str(cur), opts)

    async def async_select_option(self, option: str) -> None:
        try:
            vacuum_entity: RoboVacEntity | None = self.hass.data[DOMAIN][CONF_VACS].get(
                self.robovac_id
            )
        except KeyError:
            vacuum_entity = None
        if not vacuum_entity:
            return
        await vacuum_entity.async_set_fan_speed(option)
        await self.async_update()
        self.async_write_ha_state()
