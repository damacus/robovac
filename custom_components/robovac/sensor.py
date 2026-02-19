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
        self._attr_available = False  # Start as unavailable

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, item[CONF_ID])},
            name=item[CONF_NAME]
        )

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            # Get the vacuum entity from hass data
            vacuum_entity = self.hass.data[DOMAIN][CONF_VACS].get(self.robovac_id)
            
            if not vacuum_entity:
                _LOGGER.debug(
                    "Vacuum entity not found for %s",
                    self.robovac_id
                )
                self._attr_available = False
                return
            
            # Check if vacuum has tuyastatus data (from vacuum._dps)
            if not vacuum_entity.tuyastatus:
                _LOGGER.debug(
                    "No tuyastatus available yet for %s. Waiting for connection...",
                    self.robovac_id
                )
                self._attr_available = False
                return
            
            # Get the model-specific battery DPS code
            battery_dps_code = self._get_battery_dps_code(vacuum_entity)
            
            # Get battery value using the correct DPS code
            battery_value = vacuum_entity.tuyastatus.get(battery_dps_code)
            
            if battery_value is not None:
                self._attr_native_value = battery_value
                self._attr_available = True
                _LOGGER.debug(
                    "Battery for %s: %s%% (DPS code: %s)",
                    self.robovac_id,
                    battery_value,
                    battery_dps_code
                )
            else:
                _LOGGER.debug(
                    "Battery DPS code %s not in tuyastatus. Available codes: %s",
                    battery_dps_code,
                    list(vacuum_entity.tuyastatus.keys())
                )
                self._attr_available = False
                
        except KeyError as ex:
            _LOGGER.error(
                "Missing key in hass data for %s: %s",
                self.robovac_id,
                ex
            )
            self._attr_available = False
        except AttributeError as ex:
            _LOGGER.error(
                "Attribute error accessing vacuum for %s: %s",
                self.robovac_id,
                ex
            )
            self._attr_available = False
        except Exception as ex:
            _LOGGER.error(
                "Unexpected error updating battery sensor for %s: %s",
                self.robovac_id,
                ex
            )
            self._attr_available = False

    def _get_battery_dps_code(self, vacuum_entity) -> str:
        """Get the correct DPS code for battery.
        
        Args:
            vacuum_entity: The RoboVacEntity instance
            
        Returns:
            The DPS code as a string (e.g., "163" for T2267, "104" for default)
        """
        try:
            # Try to get the model-specific code from the vacuum
            if hasattr(vacuum_entity, 'vacuum') and vacuum_entity.vacuum:
                dps_codes = vacuum_entity.vacuum.getDpsCodes()
                if "BATTERY_LEVEL" in dps_codes:
                    code = dps_codes["BATTERY_LEVEL"]
                    return code
        except Exception as ex:
            _LOGGER.debug("Could not get model-specific DPS code: %s", ex)
        
        # Fallback to default
        return TuyaCodes.BATTERY_LEVEL