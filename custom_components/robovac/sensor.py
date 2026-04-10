from __future__ import annotations
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, CONF_NAME, CONF_ID, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_VACS, DOMAIN, REFRESH_RATE
from .vacuums.base import TuyaCodes, RobovacCommand
from .vacuums import ROBOVAC_MODELS
from .proto_decode import (
    decode_consumable_response,
    decode_device_info,
    decode_unisetting_response,
)

if TYPE_CHECKING:
    from .vacuum import RoboVacEntity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=REFRESH_RATE)

# Consumables exposed as individual sensors for proto-based models (DPS 168).
# Each tuple: (decode_key, display_name, icon)
_PROTO_CONSUMABLES = [
    ("side_brush",    "Side Brush",    "mdi:brush"),
    ("rolling_brush", "Rolling Brush", "mdi:brush-variant"),
    ("filter_mesh",   "Filter",        "mdi:air-filter"),
    ("scrape",        "Scraper",       "mdi:squeegee"),
    ("sensor",        "Sensor",        "mdi:motion-sensor"),
    ("dustbag",       "Dust Bag",      "mdi:trash-can-outline"),
]


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
    """Set up the Eufy RoboVac sensor platform."""
    vacuums = config_entry.data[CONF_VACS]
    entities = []

    for item in vacuums:
        item = vacuums[item]
        entities.append(RobovacBatterySensor(item))

        # Look up model class to determine which optional sensors to create.
        # ROBOVAC_MODELS is keyed by the 5-char prefix (e.g. "T2277").
        model_prefix = (item.get(CONF_MODEL) or "")[:5]
        model_class = ROBOVAC_MODELS.get(model_prefix)
        if model_class is None:
            continue

        commands = getattr(model_class, "commands", {})

        # Error sensor — any model that has an ERROR command
        if RobovacCommand.ERROR in commands:
            error_dps = str(commands[RobovacCommand.ERROR]["code"])
            entities.append(RobovacErrorSensor(item, error_dps))

        # Per-consumable sensors — proto models that use DPS 168
        consumables_cmd = commands.get(RobovacCommand.CONSUMABLES, {})
        if isinstance(consumables_cmd, dict) and consumables_cmd.get("code") == 168:
            dps = str(consumables_cmd["code"])
            for key, label, icon in _PROTO_CONSUMABLES:
                entities.append(RobovacConsumableSensor(item, dps, key, label, icon))

        # Firmware sensor — models with a DEVICE_INFO command (DPS 169)
        if RobovacCommand.DEVICE_INFO in commands:
            dps = str(commands[RobovacCommand.DEVICE_INFO]["code"])
            entities.append(RobovacFirmwareSensor(item, dps))

        # WiFi signal sensor — models with a UNISETTING command (DPS 176)
        if RobovacCommand.UNISETTING in commands:
            dps = str(commands[RobovacCommand.UNISETTING]["code"])
            entities.append(RobovacWifiSignalSensor(item, dps))

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Battery sensor (unchanged)
# ---------------------------------------------------------------------------


class RobovacBatterySensor(SensorEntity):
    """Representation of a Eufy RoboVac Battery Sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_should_poll = True

    def __init__(self, item: dict) -> None:
        self.robovac = item
        self.robovac_id = item[CONF_ID]
        self._attr_unique_id = f"{item[CONF_ID]}_battery"
        self._attr_name = "Battery"
        self._attr_device_info = _device_info(item)

    async def async_update(self) -> None:
        try:
            # Get the vacuum entity from hass data
            vacuum_entity: RoboVacEntity | None = self.hass.data[DOMAIN][CONF_VACS].get(self.robovac_id)

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
            battery_dps_code = vacuum_entity.get_dps_code(TuyaCodes.BATTERY_LEVEL)

            # Get battery value using the correct DPS code
            battery_value = vacuum_entity.tuyastatus.get(battery_dps_code)

            if battery_value is not None:
                try:
                    # Some models might send stringified numbers or floats
                    self._attr_native_value = int(float(battery_value))
                    self._attr_available = True
                    _LOGGER.debug(
                        "Battery for %s: %s%% (DPS code: %s)",
                        self.robovac_id,
                        self._attr_native_value,
                        battery_dps_code
                    )
                except (ValueError, TypeError) as ex:
                    _LOGGER.error(
                        "Invalid battery value %s for %s: %s",
                        battery_value,
                        self.robovac_id,
                        ex
                    )
                    self._attr_available = False
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


# ---------------------------------------------------------------------------
# Error sensor
# ---------------------------------------------------------------------------


class RobovacErrorSensor(SensorEntity):
    """Sensor showing the current error/warning message(s) for a RoboVac.

    Decodes DPS 177 (T2277 proto) or DPS 106 (legacy integer) via the
    model's getRoboVacHumanReadableValue, returning "no_error" when clear
    or a comma-separated list of active messages otherwise.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_error"
        self._attr_name = "Error"
        self._attr_device_info = _device_info(item)

    async def async_update(self) -> None:
        try:
            vacuum_entity = self.hass.data[DOMAIN][CONF_VACS].get(self.robovac_id)
            if not vacuum_entity or not vacuum_entity.tuyastatus:
                self._attr_available = False
                return
            raw = vacuum_entity.tuyastatus.get(self._dps_code)
            if raw is None:
                self._attr_available = False
                return
            if vacuum_entity.vacuum is not None:
                decoded = vacuum_entity.vacuum.getRoboVacHumanReadableValue(
                    RobovacCommand.ERROR, raw
                )
            else:
                decoded = str(raw)
            self._attr_native_value = decoded
            self._attr_available = True
        except Exception as ex:
            _LOGGER.error("Failed to update error sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


# ---------------------------------------------------------------------------
# Consumable sensors (one entity per consumable component)
# ---------------------------------------------------------------------------


class RobovacConsumableSensor(SensorEntity):
    """Sensor showing runtime hours for one consumable component (DPS 168).

    The device tracks cumulative hours since the last manual reset per
    component (side brush, rolling brush, filter, dustbag, etc.).
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_native_unit_of_measurement = "h"

    def __init__(
        self, item: dict, dps_code: str, key: str, label: str, icon: str
    ) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._key = key
        self._attr_unique_id = f"{item[CONF_ID]}_consumable_{key}"
        self._attr_name = label
        self._attr_icon = icon
        self._attr_device_info = _device_info(item)

    async def async_update(self) -> None:
        try:
            vacuum_entity = self.hass.data[DOMAIN][CONF_VACS].get(self.robovac_id)
            if not vacuum_entity or not vacuum_entity.tuyastatus:
                self._attr_available = False
                return
            raw = vacuum_entity.tuyastatus.get(self._dps_code)
            if raw is None:
                self._attr_available = False
                return
            hours = decode_consumable_response(raw)
            value = hours.get(self._key)
            if value is None:
                self._attr_available = False
                return
            self._attr_native_value = value
            self._attr_available = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update consumable sensor %s for %s: %s",
                self._key, self.robovac_id, ex,
            )
            self._attr_available = False


# ---------------------------------------------------------------------------
# Firmware / device-info sensor
# ---------------------------------------------------------------------------


class RobovacFirmwareSensor(SensorEntity):
    """Sensor showing the current firmware version string (DPS 169).

    State: firmware version (e.g. "2.0.0").
    Extra attributes: product_name, device_mac, hardware, wifi_name.

    Disabled by default — enable via the HA entity registry when needed.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:chip"
    _attr_entity_registry_enabled_default = False

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_firmware"
        self._attr_name = "Firmware"
        self._attr_device_info = _device_info(item)
        self._attr_extra_state_attributes: dict = {}

    async def async_update(self) -> None:
        try:
            vacuum_entity = self.hass.data[DOMAIN][CONF_VACS].get(self.robovac_id)
            if not vacuum_entity or not vacuum_entity.tuyastatus:
                self._attr_available = False
                return
            raw = vacuum_entity.tuyastatus.get(self._dps_code)
            if raw is None:
                self._attr_available = False
                return
            info = decode_device_info(raw)
            if not info:
                self._attr_available = False
                return
            self._attr_native_value = info.get("software")
            self._attr_extra_state_attributes = {
                k: info[k]
                for k in ("product_name", "device_mac", "hardware", "wifi_name", "wifi_ip")
                if k in info
            }
            self._attr_available = True
        except Exception as ex:
            _LOGGER.error("Failed to update firmware sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


# ---------------------------------------------------------------------------
# WiFi signal sensor
# ---------------------------------------------------------------------------


class RobovacWifiSignalSensor(SensorEntity):
    """Sensor showing WiFi signal strength as a percentage (DPS 176).

    State: 0–100 % signal strength.
    Extra attributes: wifi_ssid, wifi_frequency, multi_map, custom_clean_mode,
      map_valid.

    Disabled by default — enable via the HA entity registry when needed.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:wifi"
    _attr_entity_registry_enabled_default = False

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_wifi_signal"
        self._attr_name = "WiFi Signal"
        self._attr_device_info = _device_info(item)
        self._attr_extra_state_attributes: dict = {}

    async def async_update(self) -> None:
        try:
            vacuum_entity = self.hass.data[DOMAIN][CONF_VACS].get(self.robovac_id)
            if not vacuum_entity or not vacuum_entity.tuyastatus:
                self._attr_available = False
                return
            raw = vacuum_entity.tuyastatus.get(self._dps_code)
            if raw is None:
                self._attr_available = False
                return
            info = decode_unisetting_response(raw)
            signal = info.get("wifi_signal_pct")
            if signal is None:
                self._attr_available = False
                return
            self._attr_native_value = signal
            self._attr_extra_state_attributes = {
                k: info[k]
                for k in (
                    "wifi_ssid", "wifi_frequency", "multi_map",
                    "custom_clean_mode", "map_valid",
                )
                if k in info
            }
            self._attr_available = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update WiFi signal sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False
