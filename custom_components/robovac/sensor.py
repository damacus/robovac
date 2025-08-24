import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, CONF_NAME, CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_VACS, DOMAIN, REFRESH_RATE
from .vacuums.base import TuyaCodes

_LOGGER = logging.getLogger(__name__)

BATTERY = "Battery"
SCAN_INTERVAL = timedelta(seconds=REFRESH_RATE)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Eufy RoboVac sensor platform."""
    vacuums = config_entry.data[CONF_VACS]
    entities = []

    for item in vacuums:
        item = vacuums[item]
        entities.append(RobovacBatterySensor(item))

    async_add_entities(entities)


class RobovacBatterySensor(SensorEntity):
    """Representation of a Eufy RoboVac Battery Sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_should_poll = True

    def __init__(self, item: dict) -> None:
        """Initialize the sensor.

        Args:
            item: Dictionary containing vacuum configuration.
        """
        self.robovac = item
        self.robovac_id = item[CONF_ID]
        self._attr_unique_id = f"{item[CONF_ID]}_battery"
        self._attr_name = "Battery"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, item[CONF_ID])},
            name=item[CONF_NAME],
        )

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            vacuum_entity = self.hass.data[DOMAIN][CONF_VACS].get(self.robovac_id)

            if not vacuum_entity:
                _LOGGER.debug("Vacuum entity not found for %s", self.robovac_id)
                self._attr_available = False
                return

            # Prefer the parsed value maintained by the vacuum entity if present
            value = getattr(vacuum_entity, "battery_level", None)

            # Fallback: read raw DPS using model-specific code if needed
            if value is None and getattr(vacuum_entity, "tuyastatus", None) is not None:
                dps_codes = {}
                if getattr(vacuum_entity, "vacuum", None) is not None:
                    dps_codes = vacuum_entity.vacuum.getDpsCodes() or {}
                battery_code = dps_codes.get("BATTERY_LEVEL", TuyaCodes.BATTERY_LEVEL)
                value = vacuum_entity.tuyastatus.get(battery_code)

            if value is None:
                self._attr_available = False
                return

            # Coerce and clamp to 0..100
            try:
                value_int = int(value)
                value_int = max(0, min(100, value_int))
                self._attr_native_value = value_int
                self._attr_available = True
            except (TypeError, ValueError):
                _LOGGER.debug("Battery value not an int for %s: %s", self.robovac_id, value)
                self._attr_available = False

        except Exception as ex:
            _LOGGER.error("Failed to update battery sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False
