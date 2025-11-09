"""Select entities that expose RoboVac room cleaning targets."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VACS, DOMAIN
from .vacuum import RoboVacEntity

CLEAN_WHOLE_HOUSE_OPTION = "Clean Whole House"


@dataclass(frozen=True)
class _RoomOption:
    """Representation of a selectable room."""

    label: str
    identifier: str


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RoboVac room selectors for a config entry."""
    configured_vacuums = entry.data.get(CONF_VACS, {})
    registered_vacuums = hass.data.get(DOMAIN, {}).get(CONF_VACS, {})

    entities: list[RobovacRoomSelect] = []
    for vacuum_id in configured_vacuums:
        vacuum = registered_vacuums.get(vacuum_id)
        if isinstance(vacuum, RoboVacEntity):
            entities.append(RobovacRoomSelect(vacuum))

    if entities:
        async_add_entities(entities)


class RobovacRoomSelect(SelectEntity):
    """Select entity that triggers room cleaning on a RoboVac."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, vacuum: RoboVacEntity) -> None:
        """Initialise the select entity."""
        self._vacuum = vacuum
        self._attr_unique_id = f"{vacuum.unique_id}_room_select"
        self._attr_name = "Cleaning Target"
        self._current_option: str | None = None
        self._attr_device_info = vacuum.device_info
        self._remove_room_listener: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Register callbacks once the entity is added to Home Assistant."""

        await super().async_added_to_hass()

        def _handle_room_update() -> None:
            if self.hass is not None and self.enabled:
                self.async_write_ha_state()

        remove_listener = getattr(self._vacuum, "add_room_name_listener", None)
        if callable(remove_listener):
            self._remove_room_listener = remove_listener(_handle_room_update)
            if self._remove_room_listener is not None:
                self.async_on_remove(self._remove_room_listener)

    @property
    def available(self) -> bool:
        """Return whether the select entity is available."""
        return self._vacuum.available

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        return self._current_option

    @property
    def options(self) -> list[str]:
        """Return the list of options."""
        room_labels = [option.label for option in self._iter_room_options()]
        return [CLEAN_WHOLE_HOUSE_OPTION, *room_labels]

    def _iter_room_options(self) -> Iterable[_RoomOption]:
        """Yield room options derived from the vacuum entity."""
        room_names = getattr(self._vacuum, "_attr_room_names", None)
        options: list[_RoomOption] = []
        seen_identifiers: set[str] = set()

        if isinstance(room_names, dict):
            items = room_names.items()
        elif isinstance(room_names, list):
            items = enumerate(room_names)
        else:
            items = []

        for key, value in items:
            identifier: Any = key
            label: str | None = None

            if isinstance(value, dict):
                identifier = value.get("id", identifier)
                label = (
                    value.get("label")
                    or value.get("name")
                    or value.get("room_name")
                )
            elif isinstance(value, str):
                label = value
            elif value is not None:
                label = str(value)

            if identifier is None:
                continue

            identifier_str = str(identifier)
            if identifier_str in seen_identifiers:
                continue
            seen_identifiers.add(identifier_str)
            display_label = label if label else identifier_str
            options.append(
                _RoomOption(display_label, identifier_str)
            )

        options.sort(key=lambda option: option.label.casefold())
        return options

    async def async_select_option(self, option: str) -> None:
        """Handle option selection."""
        if option == CLEAN_WHOLE_HOUSE_OPTION:
            await self._vacuum.async_start()
            await self._vacuum.async_send_command("autoClean")
            self._current_option = option
            self.async_write_ha_state()
            return

        lookup = {room_option.label: room_option.identifier for room_option in self._iter_room_options()}
        if option not in lookup:
            raise ValueError(f"Invalid option: {option}")

        room_id = lookup[option]
        try:
            room_value: Any = int(room_id)
        except (TypeError, ValueError):
            room_value = room_id

        await self._vacuum.async_send_command(
            "roomClean",
            {"roomIds": [room_value], "count": 1},
        )
        self._current_option = option
        self.async_write_ha_state()

    @property
    def device_info(self):
        """Return device info for the select entity."""
        return self._attr_device_info
