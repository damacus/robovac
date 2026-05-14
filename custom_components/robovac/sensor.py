from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
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
    decode_clean_param_response,
    merge_clean_param_layers,
    decode_clean_record_list,
    decode_consumable_response,
    decode_device_info,
    decode_error_code,
    decode_unisetting_response,
    decode_work_status_v2,
    decode_analysis_response,
)

if TYPE_CHECKING:
    from .vacuum import RoboVacEntity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=REFRESH_RATE)

# Consumables exposed as individual sensors for proto-based models (DPS 168).
# Tuple: (decode_key, display_name, icon)
_PROTO_CONSUMABLES = {
    "side_brush": ("Side Brush", "mdi:brush"),
    "rolling_brush": ("Rolling Brush", "mdi:brush-variant"),
    "filter_mesh": ("Filter", "mdi:air-filter"),
    "scrape": ("Scraper", "mdi:squeegee"),
    "sensor": ("Sensor", "mdi:motion-sensor"),
    "mop": ("Mop", "mdi:robot-vacuum"),
    "dustbag": ("Dust Bag", "mdi:trash-can-outline"),
}


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
    entities: list[SensorEntity] = []

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

        # Error sensor — any model that has an ERROR command (DPS 177)
        if RobovacCommand.ERROR in commands:
            error_dps = str(commands[RobovacCommand.ERROR]["code"])
            entities.append(RobovacErrorSensor(item, error_dps))

        # Notification sensor — prompt/notification codes (DPS 178)
        if RobovacCommand.ACTIVE_ERRORS in commands:
            dps = str(commands[RobovacCommand.ACTIVE_ERRORS]["code"])
            entities.append(RobovacNotificationSensor(item, dps))

        # Warning sensor — non-fatal maintenance/station warnings.
        warning_dps = getattr(model_class, "warning_dps_code", None)
        if warning_dps is not None:
            entities.append(RobovacWarningSensor(item, str(warning_dps), model_class))

        # Per-consumable sensors — proto models using DPS 168
        consumables_cmd = commands.get(RobovacCommand.CONSUMABLES, {})
        if isinstance(consumables_cmd, dict) and consumables_cmd.get("code") == 168:
            dps = str(consumables_cmd["code"])
            keys = getattr(model_class, "consumable_sensor_keys", _PROTO_CONSUMABLES)
            for key in keys:
                label, icon = _PROTO_CONSUMABLES[key]
                entities.append(RobovacConsumableSensor(item, dps, key, label, icon))

        # Clean-type sensor — DPS 154. Models that expose first-class config
        # entities already surface these values as selects/switches and vacuum
        # attributes, so avoid creating a duplicate diagnostic sensor.
        if (
            RobovacCommand.CLEAN_PARAM in commands
            and not getattr(model_class, "expose_config_entities", False)
        ):
            dps = str(commands[RobovacCommand.CLEAN_PARAM]["code"])
            entities.append(RobovacCleanTypeSensor(item, dps))

        # Last-clean record sensor — DPS 164
        if RobovacCommand.CLEAN_RECORDS in commands:
            dps = str(commands[RobovacCommand.CLEAN_RECORDS]["code"])
            entities.append(RobovacLastCleanRecordSensor(item, dps))

        # Station-status sensor — DPS 173
        if RobovacCommand.WORK_STATUS_V2 in commands:
            dps = str(commands[RobovacCommand.WORK_STATUS_V2]["code"])
            entities.append(RobovacWorkStatusV2Sensor(item, dps))

        # Last-clean stats sensors — DPS 179 (area + duration)
        if RobovacCommand.LAST_CLEAN in commands:
            dps = str(commands[RobovacCommand.LAST_CLEAN]["code"])
            entities.append(RobovacLastCleanAreaSensor(item, dps))
            entities.append(RobovacLastCleanDurationSensor(item, dps))

        # Firmware sensor — DPS 169
        if RobovacCommand.DEVICE_INFO in commands:
            dps = str(commands[RobovacCommand.DEVICE_INFO]["code"])
            entities.append(RobovacFirmwareSensor(item, dps))

        # WiFi signal + attribute sensors — DPS 176
        if RobovacCommand.UNISETTING in commands:
            dps = str(commands[RobovacCommand.UNISETTING]["code"])
            entities.append(RobovacWifiSignalSensor(item, dps))
            entities.append(RobovacWifiSsidSensor(item, dps))
            entities.append(RobovacWifiFrequencySensor(item, dps))
            entities.append(RobovacMultiMapSensor(item, dps))
            entities.append(RobovacCustomCleanModeSensor(item, dps))
            entities.append(RobovacMapValidSensor(item, dps))
            entities.append(RobovacChildrenLockSensor(item, dps))

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _vacuum_and_status(hass: HomeAssistant, domain: str, conf_vacs: str, robovac_id: str) -> tuple[Any, Any]:
    """Return (vacuum_entity, tuyastatus) or (None, None) if vacuum not found."""
    vacuum_entity = hass.data[domain][conf_vacs].get(robovac_id)
    if not vacuum_entity:
        return None, None
    return vacuum_entity, vacuum_entity.tuyastatus


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
# Error sensors (DPS 177 and DPS 178)
# ---------------------------------------------------------------------------


class RobovacErrorSensor(SensorEntity):
    """Current warning messages from DPS 177.

    Shows "no_error" when clear, or a comma-separated list of active
    warning descriptions decoded from the T2277 error-code table.
    Works for legacy models too (plain integer error codes via the same
    getRoboVacHumanReadableValue path).
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
        self._attr_native_value = "No error"
        self._attr_available = True
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_native_value = "No error"
                    self._attr_available = True
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_native_value = "No error"
                    self._attr_available = True
                return
            if vacuum_entity.vacuum is not None:
                decoded = vacuum_entity.vacuum.getRoboVacHumanReadableValue(
                    RobovacCommand.ERROR, raw
                )
            else:
                decoded = str(raw)
            self._attr_native_value = "No error" if decoded == "no_error" else decoded
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error("Failed to update error sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


class RobovacNotificationSensor(SensorEntity):
    """Informational prompt / notification codes from DPS 178.

    DPS 178 carries PromptCodeList values (small integers such as 40, 76, 79)
    that describe the robot's current operational context — e.g.
    "Returning to dock", "Cannot start while at dock", "Low battery".
    These are NOT hardware faults; use the Error sensor (DPS 177) for faults.
    Shows "no_error" when no active notification.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:bell-outline"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_notification"
        self._attr_name = "Notification"
        self._attr_device_info = _device_info(item)
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            value = decode_error_code(raw)
            self._attr_native_value = None if value == "no_error" else value
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error("Failed to update notification sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


class RobovacWarningSensor(SensorEntity):
    """Non-fatal maintenance/station warnings from model-specific DPS fields."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-outline"

    def __init__(self, item: dict, dps_code: str, model_class: type) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._model_class = model_class
        self._attr_unique_id = f"{item[CONF_ID]}_warning"
        self._attr_name = "Warning"
        self._attr_device_info = _device_info(item)
        self._attr_native_value = "No warning"
        self._attr_extra_state_attributes: dict = {"warnings": []}
        self._attr_available = True
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_native_value = "No warning"
                    self._attr_extra_state_attributes = {"warnings": []}
                    self._attr_available = True
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_native_value = "No warning"
                    self._attr_extra_state_attributes = {"warnings": []}
                    self._attr_available = True
                return
            decoder = getattr(self._model_class, "decode_warning_dps", None)
            warnings = decoder(raw) if decoder else []
            messages = [str(warning["message"]) for warning in warnings]
            self._attr_native_value = "; ".join(messages) if messages else "No warning"
            self._attr_extra_state_attributes = {"warnings": warnings}
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error("Failed to update warning sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


# ---------------------------------------------------------------------------
# Consumable sensors (DPS 168)
# ---------------------------------------------------------------------------


class RobovacConsumableSensor(SensorEntity):
    """Runtime hours for one consumable component (DPS 168).

    The device tracks cumulative hours since the last manual reset per
    component (side brush, rolling brush, filter, dustbag, etc.).
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
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
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            hours = decode_consumable_response(raw)
            value = hours.get(self._key)
            if value is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = value
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update consumable sensor %s for %s: %s",
                self._key, self.robovac_id, ex,
            )
            self._attr_available = False


# ---------------------------------------------------------------------------
# Clean-type sensor (DPS 154)
# ---------------------------------------------------------------------------


class RobovacCleanTypeSensor(SensorEntity):
    """Current cleaning mode from DPS 154 (CleanParamResponse).

    State: active clean_type — sweep_only, mop_only, sweep_and_mop, sweep_then_mop.
    Uses running_clean_param when a clean is in progress, otherwise clean_param.
    Extra attributes: fan speed level, clean_extent, mop_level.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:broom"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_clean_type"
        self._attr_name = "Clean Type"
        self._attr_device_info = _device_info(item)
        self._attr_extra_state_attributes: dict = {}
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            d = decode_clean_param_response(raw)
            if not d:
                if not self._has_had_data:
                    self._attr_available = False
                return
            params = merge_clean_param_layers(d)
            clean_type = params.get("clean_type")
            if clean_type is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = clean_type
            self._attr_extra_state_attributes = {
                k: params[k]
                for k in (
                    "fan",
                    "clean_extent",
                    "mop_level",
                    "edge_hugging_mopping",
                    "clean_times",
                )
                if k in params
            }
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error("Failed to update clean-type sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


# ---------------------------------------------------------------------------
# Last-clean record sensor (DPS 164)
# ---------------------------------------------------------------------------


class RobovacLastCleanRecordSensor(SensorEntity):
    """Timestamp of the most recent clean session from DPS 164.

    State: datetime of the last recorded clean (UTC).
    Extra attributes: total record count in the list.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:history"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_last_clean_record"
        self._attr_name = "Last Clean"
        self._attr_device_info = _device_info(item)
        self._attr_extra_state_attributes: dict = {}
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            records = decode_clean_record_list(raw)
            if not records:
                if not self._has_had_data:
                    self._attr_available = False
                return
            # Find the most recent entry by timestamp
            latest = max(
                (r for r in records if "timestamp" in r),
                key=lambda r: r["timestamp"],
                default=None,
            )
            if latest is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = datetime.fromtimestamp(
                latest["timestamp"], tz=timezone.utc
            )
            self._attr_extra_state_attributes = {"record_count": len(records)}
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update last-clean record sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False


# ---------------------------------------------------------------------------
# Station / dock work-status sensor (DPS 173)
# ---------------------------------------------------------------------------


class RobovacWorkStatusV2Sensor(SensorEntity):
    """Vacuum + station state from DPS 173 (outer-wrapped WorkStatus).

    Used by station-aware firmware that wraps WorkStatus in an outer message
    and may encode sub-state RunState values as nested sub-messages.
    Shows the same status strings as the main vacuum entity (auto, Charging,
    Paused, going_to_wash, etc.).

    Disabled by default — only relevant on models with a station accessory.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:robot-vacuum"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_work_status_v2"
        self._attr_name = "Station Status"
        self._attr_device_info = _device_info(item)
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = decode_work_status_v2(raw)
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update station-status sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False


# ---------------------------------------------------------------------------
# Last-clean stats sensors (DPS 179)
# ---------------------------------------------------------------------------


class RobovacLastCleanAreaSensor(SensorEntity):
    """Floor area covered in the most recent clean session (DPS 179).

    State: cleaned area in m².
    Extra attributes: mode, success, duration_s, room_count.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_native_unit_of_measurement = "m²"
    _attr_icon = "mdi:floor-plan"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_last_clean_area"
        self._attr_name = "Last Clean Area"
        self._attr_device_info = _device_info(item)
        self._attr_extra_state_attributes: dict = {}
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            d = decode_analysis_response(raw)
            area = d.get("clean_area_m2")
            if area is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = area
            self._attr_extra_state_attributes = {
                k: d[k]
                for k in ("mode", "success", "clean_time_s", "room_count", "clean_id")
                if k in d
            }
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update last-clean area sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False


class RobovacLastCleanDurationSensor(SensorEntity):
    """Duration of the most recent clean session (DPS 179).

    State: active cleaning time in seconds (excludes pauses).
    Extra attributes: mode, success, clean_area_m2, room_count.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_last_clean_duration"
        self._attr_name = "Last Clean Duration"
        self._attr_device_info = _device_info(item)
        self._attr_extra_state_attributes: dict = {}
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            d = decode_analysis_response(raw)
            duration = d.get("clean_time_s")
            if duration is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = duration
            self._attr_extra_state_attributes = {
                k: d[k]
                for k in ("mode", "success", "clean_area_m2", "room_count", "clean_id")
                if k in d
            }
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update last-clean duration sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False


# ---------------------------------------------------------------------------
# Firmware / device-info sensor (DPS 169)
# ---------------------------------------------------------------------------


class RobovacFirmwareSensor(SensorEntity):
    """Firmware version string from DPS 169 (DeviceInfo).

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
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            info = decode_device_info(raw)
            if not info:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = info.get("software")
            self._attr_extra_state_attributes = {
                k: info[k]
                for k in ("product_name", "device_mac", "hardware", "wifi_name", "wifi_ip")
                if k in info
            }
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error("Failed to update firmware sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


# ---------------------------------------------------------------------------
# WiFi signal sensor (DPS 176)
# ---------------------------------------------------------------------------


class RobovacWifiSignalSensor(SensorEntity):
    """WiFi signal strength as a percentage from DPS 176 (UnisettingResponse).

    State: 0–100 % signal strength.
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
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            info = decode_unisetting_response(raw)
            signal = info.get("wifi_signal_pct")
            if signal is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = signal
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update WiFi signal sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False


# ---------------------------------------------------------------------------
# WiFi / unisetting attribute sensors (DPS 176) — split from WiFi signal
# ---------------------------------------------------------------------------


class RobovacWifiSsidSensor(SensorEntity):
    """WiFi SSID from DPS 176 (UnisettingResponse). Diagnostic."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:wifi"
    _attr_entity_registry_enabled_default = False

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_wifi_ssid"
        self._attr_name = "WiFi SSID"
        self._attr_device_info = _device_info(item)
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            value = decode_unisetting_response(raw).get("wifi_ssid")
            if value is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = value
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error("Failed to update WiFi SSID sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


class RobovacWifiFrequencySensor(SensorEntity):
    """WiFi frequency band from DPS 176 (UnisettingResponse). Diagnostic."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:wifi"
    _attr_entity_registry_enabled_default = False

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_wifi_frequency"
        self._attr_name = "WiFi Frequency"
        self._attr_device_info = _device_info(item)
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            value = decode_unisetting_response(raw).get("wifi_frequency")
            if value is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = value
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update WiFi frequency sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False


class RobovacMultiMapSensor(SensorEntity):
    """Multi-map switch state from DPS 176 (UnisettingResponse). Diagnostic."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-multiple"
    _attr_entity_registry_enabled_default = False

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_multi_map"
        self._attr_name = "Multi Map"
        self._attr_device_info = _device_info(item)
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = decode_unisetting_response(raw)["multi_map"]
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error("Failed to update multi-map sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


class RobovacCustomCleanModeSensor(SensorEntity):
    """Custom clean mode switch state from DPS 176 (UnisettingResponse).

    Normal (non-diagnostic) sensor — reflects whether the custom room-level
    clean configuration is active.
    """

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_icon = "mdi:auto-fix"

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_custom_clean_mode"
        self._attr_name = "Custom Clean Mode"
        self._attr_device_info = _device_info(item)
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            value = decode_unisetting_response(raw).get("custom_clean_mode")
            if value is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = value
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update custom-clean-mode sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False


class RobovacMapValidSensor(SensorEntity):
    """Map valid flag from DPS 176 (UnisettingResponse). Diagnostic."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-check"
    _attr_entity_registry_enabled_default = False

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_map_valid"
        self._attr_name = "Map Valid"
        self._attr_device_info = _device_info(item)
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            value = decode_unisetting_response(raw).get("map_valid")
            if value is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = value
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error("Failed to update map-valid sensor for %s: %s", self.robovac_id, ex)
            self._attr_available = False


class RobovacChildrenLockSensor(SensorEntity):
    """Children lock switch state from DPS 176 (UnisettingResponse). Diagnostic."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:lock-outline"
    _attr_entity_registry_enabled_default = False

    def __init__(self, item: dict, dps_code: str) -> None:
        self.robovac_id = item[CONF_ID]
        self._dps_code = dps_code
        self._attr_unique_id = f"{item[CONF_ID]}_children_lock"
        self._attr_name = "Children Lock"
        self._attr_device_info = _device_info(item)
        self._has_had_data = False

    async def async_update(self) -> None:
        try:
            vacuum_entity, tuyastatus = _vacuum_and_status(
                self.hass, DOMAIN, CONF_VACS, self.robovac_id
            )
            if vacuum_entity is None:
                self._attr_available = False
                return
            if not tuyastatus:
                if not self._has_had_data:
                    self._attr_available = False
                return
            raw = tuyastatus.get(self._dps_code)
            if raw is None:
                if not self._has_had_data:
                    self._attr_available = False
                return
            self._attr_native_value = decode_unisetting_response(raw)["children_lock"]
            self._attr_available = True
            self._has_had_data = True
        except Exception as ex:
            _LOGGER.error(
                "Failed to update children-lock sensor for %s: %s", self.robovac_id, ex
            )
            self._attr_available = False
