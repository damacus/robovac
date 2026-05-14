# Copyright 2022 Brendan McCluskey
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Eufy Robovac vacuum platform.

This module provides the vacuum entity integration for Eufy Robovac devices.
"""
from __future__ import annotations
import asyncio
import base64
from datetime import timedelta
from enum import StrEnum
import json
import logging
import time
from typing import Any, cast

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VACS, DOMAIN, PING_RATE, REFRESH_RATE, TIMEOUT
from .errors import getErrorMessage
from .proto_decode import (
    decode_clean_param_response,
    merge_clean_param_layers,
    patch_clean_param_dps154,
)
from .vacuums.base import RobovacCommand, RoboVacEntityFeature, TuyaCodes, TUYA_CONSUMABLES_CODES
from .robovac import ModelNotSupportedException, RoboVac
from .tuyalocalapi import TuyaException

ATTR_BATTERY_ICON = "battery_icon"
ATTR_ERROR = "error"
ATTR_FAN_SPEED = "fan_speed"
ATTR_FAN_SPEED_LIST = "fan_speed_list"
ATTR_STATUS = "status"
ATTR_ERROR_CODE = "error_code"
ATTR_MODEL_CODE = "model_code"
ATTR_CLEANING_AREA = "cleaning_area"
ATTR_CLEANING_TIME = "cleaning_time"
ATTR_AUTO_RETURN = "auto_return"
ATTR_DO_NOT_DISTURB = "do_not_disturb"
ATTR_BOOST_IQ = "boost_iq"
ATTR_CONSUMABLES = "consumables"
ATTR_MODE = "mode"
ATTR_CLEAN_TYPE = "clean_type"
ATTR_CLEAN_TYPE_LABEL = "clean_type_label"
ATTR_MOP_LEVEL = "mop_level"
ATTR_EDGE_HUGGING_MOPPING = "edge_hugging_mopping"
ATTR_CLEAN_CARPET = "clean_carpet"

_CLEAN_TYPE_LABELS = {
    "sweep_only": "Sweep only",
    "mop_only": "Mop only",
    "sweep_and_mop": "Vacuum and mop",
    "sweep_then_mop": "Vacuum then mop",
}


def _clean_type_label(clean_type: str | None) -> str | None:
    if not clean_type:
        return None
    if clean_type in _CLEAN_TYPE_LABELS:
        return _CLEAN_TYPE_LABELS[clean_type]
    return clean_type.replace("_", " ").title()


def _lookup_activity(
    mapping: dict[str, VacuumActivity], state: Any
) -> VacuumActivity | None:
    """Map Tuya human-readable status to VacuumActivity; keys may differ by case."""
    s = str(state)
    if s in mapping:
        return mapping[s]
    folded = s.casefold()
    for key, activity in mapping.items():
        if str(key).casefold() == folded:
            return activity
    return None


def _activity_from_mode(mode: str | None) -> VacuumActivity | None:
    """Map decoded mode DPS to VacuumActivity when status DPS is idle/station-only."""
    if not mode:
        return None
    normalized = str(mode).casefold()
    if normalized in {"auto", "cleaning"}:
        return VacuumActivity.CLEANING
    if normalized in {"pause", "paused"}:
        return VacuumActivity.PAUSED
    if normalized in {"return", "returning", "docking"}:
        return VacuumActivity.RETURNING
    if normalized in {"standby", "stop", "idle"}:
        return VacuumActivity.IDLE
    return None


def _activity_from_return_progress(progress: str | None) -> VacuumActivity | None:
    """Map decoded return/dock progress to VacuumActivity."""
    if not progress:
        return None
    normalized = str(progress).casefold()
    if normalized in {"docked", "charging"}:
        return VacuumActivity.DOCKED
    if normalized in {"cleaning", "auto"}:
        return VacuumActivity.CLEANING
    if normalized in {"returning", "return"}:
        return VacuumActivity.RETURNING
    return None


_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=REFRESH_RATE)
UPDATE_RETRIES = 3

# ⚡ Bolt optimization: Pre-calculate valid VacuumActivity values into a set
# to avoid O(n) list comprehension on every property getter access
VACUUM_ACTIVITY_VALUES = {activity.value for activity in VacuumActivity}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize my test integration 2 config entry."""
    vacuums = config_entry.data[CONF_VACS]
    for item in vacuums:
        item = vacuums[item]
        entity = RoboVacEntity(item)
        hass.data[DOMAIN][CONF_VACS][item[CONF_ID]] = entity
        async_add_entities([entity])


class RoboVacEntity(StateVacuumEntity):
    """Home Assistant vacuum entity for Tuya-based robotic vacuum cleaners.

    This class implements the Home Assistant VacuumEntity interface for controlling
    and monitoring Tuya-based robotic vacuum cleaners. It provides support for
    standard vacuum operations like start/stop/pause, cleaning modes, fan speeds,
    and status reporting.

    The entity automatically maps device-specific values to Home Assistant standards
    and handles model-specific features and command mappings.
    """

    _attr_should_poll = True

    _attr_access_token: str | None = None
    _attr_ip_address: str | None = None
    _attr_model_code: str | None = None
    _attr_cleaning_area: str | None = None
    _attr_cleaning_time: str | None = None
    _attr_auto_return: str | None = None
    _attr_do_not_disturb: str | None = None
    _attr_boost_iq: str | None = None
    _attr_consumables: str | None = None
    _attr_mode: str | None = None
    _attr_robovac_supported: int | None = None
    _attr_activity_mapping: dict[str, VacuumActivity] | None = None
    _attr_error_code: int | str | None = None
    _attr_tuya_state: int | str | None = None

    @property
    def robovac_supported(self) -> int | None:
        """Return the supported features of the vacuum cleaner."""
        return self._attr_robovac_supported

    @property
    def activity_mapping(self) -> dict[str, VacuumActivity] | None:
        """Return the mapping of statuses to Home Assistant VacuumActivity."""
        return self._attr_activity_mapping

    @property
    def mode(self) -> str | None:
        """Return the cleaning mode of the vacuum cleaner."""
        return self._attr_mode

    @property
    def consumables(self) -> str | None:
        """Return the consumables status of the vacuum cleaner."""
        return self._attr_consumables

    @property
    def cleaning_area(self) -> str | None:
        """Return the cleaning area of the vacuum cleaner."""
        return self._attr_cleaning_area

    @property
    def cleaning_time(self) -> str | None:
        """Return the cleaning time of the vacuum cleaner."""
        return self._attr_cleaning_time

    @property
    def auto_return(self) -> str | None:
        """Return the auto_return mode of the vacuum cleaner."""
        return self._attr_auto_return

    @property
    def do_not_disturb(self) -> str | None:
        """Return the do_not_disturb mode of the vacuum cleaner."""
        return self._attr_do_not_disturb

    @property
    def boost_iq(self) -> str | None:
        """Return the boost_iq mode of the vacuum cleaner."""
        return self._attr_boost_iq

    @property
    def tuya_state(self) -> str | int | None:
        """Return the state of the vacuum cleaner.

        This property is for backward compatibility with tests.
        """
        return self._attr_tuya_state

    @tuya_state.setter
    def tuya_state(self, value: str | int | None) -> None:
        """Set the state of the vacuum cleaner.

        This setter is for backward compatibility with tests.
        """
        self._attr_tuya_state = value

    @property
    def error_code(self) -> int | str | None:
        """Return the error code of the vacuum cleaner.

        This property is for backward compatibility with tests.
        """
        return self._attr_error_code

    @error_code.setter
    def error_code(self, value: int | str | None) -> None:
        """Set the error code of the vacuum cleaner.

        This setter is for backward compatibility with tests.
        """
        self._attr_error_code = value

    @property
    def model_code(self) -> str | None:
        """Return the model code of the vacuum cleaner."""
        return self._attr_model_code

    @property
    def access_token(self) -> str | None:
        """Return the fan speed of the vacuum cleaner."""
        return self._attr_access_token

    @property
    def ip_address(self) -> str | None:
        """Return the ip address of the vacuum cleaner."""
        return self._attr_ip_address

    def _is_value_true(self, value: Any) -> bool:
        """Check if a value is considered 'true', either as a boolean or string.

        Args:
            value: The value to check.

        Returns:
            bool: True if the value is considered 'true', False otherwise.
        """
        if value is True:
            return True
        if isinstance(value, str):
            return value == "True" or value.lower() == "true"
        return False

    def _get_mode_command_data(self, mode: str) -> dict[str, str | bool] | None:
        """Helper method to get mode command data for the vacuum.

        Converts a human-readable cleaning mode to the appropriate DPS command
        data structure for sending to the vacuum device.

        Args:
            mode: The cleaning mode to set (e.g., "auto", "spot", "edge", "small_room")

        Returns:
            dict[str, str | bool] | None: Dictionary with DPS code as key and model-specific
                                          command value as value, or None if vacuum not initialized
        """
        if self.vacuum is None:
            return None

        return {
            self.get_dps_code("MODE"): self.vacuum.getRoboVacCommandValue(RobovacCommand.MODE, mode)
        }

    @property
    def activity(self) -> VacuumActivity | None:
        """Return the activity of the vacuum cleaner.

        This property is used by Home Assistant to determine the state of the vacuum.
        As of Home Assistant Core 2025.1, this property should be used instead of directly
        setting the state property.
        """
        mode_activity = _activity_from_mode(self._attr_mode)
        return_progress_activity = self._return_progress_activity()
        if (
            return_progress_activity == VacuumActivity.RETURNING
            and mode_activity not in (None, VacuumActivity.RETURNING)
        ):
            return_progress_activity = None
        if return_progress_activity == VacuumActivity.DOCKED:
            return return_progress_activity
        if self._attr_tuya_state is None or self._attr_tuya_state == 0:
            if return_progress_activity is not None:
                _LOGGER.debug(
                    "Using return progress activity %s without status state",
                    return_progress_activity,
                )
                return return_progress_activity
            if mode_activity is not None:
                _LOGGER.debug("Using mode activity %s without status state", mode_activity)
                return mode_activity
            if self.tuyastatus:
                return VacuumActivity.IDLE
            # 0 is a default set when we don't have a state
            return None
        elif (
            self.error_code is not None
            and self.error_code not in [0, "no_error", "No error"]
        ):
            _LOGGER.debug(
                "State changed to error. Error message: {}".format(
                    getErrorMessage(self.error_code)
                )
            )
            return VacuumActivity.ERROR
        elif self._attr_tuya_state in VACUUM_ACTIVITY_VALUES:
            if return_progress_activity is not None:
                _LOGGER.debug(
                    "Using return progress activity %s over activity state %s",
                    return_progress_activity,
                    self._attr_tuya_state,
                )
                return return_progress_activity
            if self._attr_tuya_state == VacuumActivity.IDLE and mode_activity not in (
                None,
                VacuumActivity.IDLE,
            ):
                _LOGGER.debug(
                    "Using mode activity %s over idle activity state",
                    mode_activity,
                )
                return mode_activity
            # Particularly at system startup, the state may be set to a
            # VacuumActivity value directly, so we can return it as is.
            return cast(VacuumActivity, self._attr_tuya_state)
        elif self.activity_mapping is not None:
            # Use the activity mapping from the model details
            activity = _lookup_activity(self.activity_mapping, self._attr_tuya_state)
            mode_activity = _activity_from_mode(self._attr_mode)

            if return_progress_activity is not None:
                _LOGGER.debug(
                    "Using return progress activity %s over status %s",
                    return_progress_activity,
                    self._attr_tuya_state,
                )
                return return_progress_activity
            if activity == VacuumActivity.IDLE and mode_activity not in (None, VacuumActivity.IDLE):
                _LOGGER.debug(
                    "Using mode activity %s over idle status %s",
                    mode_activity,
                    self._attr_tuya_state,
                )
                return mode_activity
            if activity is not None:
                _LOGGER.debug(
                    "Used activity mapping, changing status %s to activity %s",
                    self._attr_tuya_state,
                    activity
                )
                return activity
            else:
                _LOGGER.debug(
                    "Activity mapping lookup failed for status %s - no mapping found",
                    self._attr_tuya_state
                )
                return None
        elif self._attr_tuya_state == "Charging" or self._attr_tuya_state == "completed" or self._attr_tuya_state == "Completed" or self._attr_tuya_state == "recharging":
            return VacuumActivity.DOCKED
        elif self._attr_tuya_state == "Recharge" or self._attr_tuya_state == "going_to_recharge":
            return VacuumActivity.RETURNING
        elif self._attr_tuya_state == "Sleeping" or self._attr_tuya_state == "standby":
            return VacuumActivity.IDLE
        elif self._attr_tuya_state == "Paused":
            return VacuumActivity.PAUSED
        else:
            _LOGGER.debug(
                "State changed to cleaning. Raw Tuya state: %s",
                self._attr_tuya_state
            )
            return VacuumActivity.CLEANING

    def _return_progress_activity(self) -> VacuumActivity | None:
        """Return activity from models that expose return/dock progress on RETURN_HOME DPS."""
        if self.tuyastatus is None or self.vacuum is None:
            return None
        raw = self.tuyastatus.get(self.get_dps_code("RETURN_HOME"))
        if raw is None or isinstance(raw, bool):
            return None
        progress = self.vacuum.getRoboVacHumanReadableValue(RobovacCommand.RETURN_HOME, raw)
        return _activity_from_return_progress(progress)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device-specific state attributes of this vacuum."""
        data: dict[str, Any] = {}

        if self._attr_error_code is not None and self._attr_error_code not in [0, "no_error"]:
            data[ATTR_ERROR] = getErrorMessage(self._attr_error_code)
        if (
            self.robovac_supported is not None
            and self.robovac_supported & RoboVacEntityFeature.CLEANING_AREA
            and self.cleaning_area
        ):
            data[ATTR_CLEANING_AREA] = self.cleaning_area
        if (
            self.robovac_supported is not None
            and self.robovac_supported & RoboVacEntityFeature.CLEANING_TIME
            and self.cleaning_time
        ):
            data[ATTR_CLEANING_TIME] = self.cleaning_time
        if (
            self.robovac_supported is not None
            and self.robovac_supported & RoboVacEntityFeature.AUTO_RETURN
            and self.auto_return
        ):
            data[ATTR_AUTO_RETURN] = self.auto_return
        if (
            self.robovac_supported is not None
            and self.robovac_supported & RoboVacEntityFeature.DO_NOT_DISTURB
            and self.do_not_disturb
        ):
            data[ATTR_DO_NOT_DISTURB] = self.do_not_disturb
        if (
            self.robovac_supported is not None
            and self.robovac_supported & RoboVacEntityFeature.BOOST_IQ
            and self.boost_iq
        ):
            data[ATTR_BOOST_IQ] = self.boost_iq
        if (
            self.robovac_supported is not None
            and self.robovac_supported & RoboVacEntityFeature.CONSUMABLES
            and self.consumables
        ):
            data[ATTR_CONSUMABLES] = self.consumables
        if self.mode:
            data[ATTR_MODE] = self.mode
        if self._attr_clean_type is not None:
            data[ATTR_CLEAN_TYPE] = self._attr_clean_type
        if self._attr_clean_type_label is not None:
            data[ATTR_CLEAN_TYPE_LABEL] = self._attr_clean_type_label
        if self._attr_mop_level is not None:
            data[ATTR_MOP_LEVEL] = self._attr_mop_level
        if self._attr_edge_hugging_mopping is not None:
            data[ATTR_EDGE_HUGGING_MOPPING] = self._attr_edge_hugging_mopping
        if self._attr_clean_carpet is not None:
            data[ATTR_CLEAN_CARPET] = self._attr_clean_carpet
        return data

    def __init__(self, item: dict[str, Any]) -> None:
        """Initialize the RoboVac vacuum entity.

        Establishes connection to the physical vacuum device via Tuya local API
        and configures the Home Assistant entity with model-specific features.

        Args:
            item: Configuration dictionary containing vacuum connection details:
                  - id: Unique identifier for the vacuum
                  - name: Display name for the vacuum
                  - model: Model code (e.g., "T2080", "L60")
                  - ip_address: Local IP address of the vacuum
                  - access_token: Tuya access token for authentication
                  - device_id: Tuya device identifier
        """
        super().__init__()

        # Initialize basic attributes
        self._attr_name = item[CONF_NAME]
        self._attr_unique_id = item[CONF_ID]
        self._attr_model_code = item[CONF_MODEL]
        self._attr_ip_address = item[CONF_IP_ADDRESS]
        self._attr_access_token = item[CONF_ACCESS_TOKEN]
        self.vacuum: RoboVac | None = None
        self.update_failures = 0
        self.tuyastatus: dict[str, Any] | None = None
        self._last_no_data_warning_time: float = 0
        self._no_data_warning_logged: bool = False
        self._consumables_codes_cache: list[str] | None = None
        self._dps_codes_memo: dict[str, str] = {}
        self._last_consumable_data: str | None = None

        # Initialize the RoboVac connection
        try:
            # Extract model code prefix for device identification
            model_code_prefix = ""
            if self.model_code is not None:
                model_code_prefix = self.model_code[0:5]

            # Create the RoboVac instance
            self.vacuum = RoboVac(
                device_id=self.unique_id,
                host=self.ip_address,
                local_key=self.access_token,
                timeout=TIMEOUT,
                ping_interval=PING_RATE,
                model_code=model_code_prefix,
                update_entity_state=self.pushed_update_handler,
            )
            _LOGGER.debug(
                "Initialized RoboVac connection for %s (model: %s)",
                self._attr_name,
                self._attr_model_code
            )
        except ModelNotSupportedException:
            _LOGGER.error(
                "Model %s is not supported",
                self._attr_model_code
            )
            self._attr_error_code = "UNSUPPORTED_MODEL"

        # Set supported features if vacuum was initialized successfully
        if self.vacuum is not None:
            # Get the supported features from the vacuum
            features = int(self.vacuum.getHomeAssistantFeatures())
            self._attr_supported_features = VacuumEntityFeature(features)
            self._attr_robovac_supported = self.vacuum.getRoboVacFeatures()
            self._attr_activity_mapping = self.vacuum.getRoboVacActivityMapping()
            self._attr_fan_speed_list = self.vacuum.getFanSpeeds()

            _LOGGER.debug(
                "Vacuum %s supports features: %s",
                self._attr_name,
                self._attr_supported_features
            )
        else:
            # Set default values if vacuum initialization failed
            self._attr_supported_features = VacuumEntityFeature(0)
            self._attr_robovac_supported = 0
            self._attr_fan_speed_list = []
            _LOGGER.warning(
                "Vacuum %s initialization failed, features not available",
                self._attr_name
            )

        # Initialize additional attributes
        self._attr_mode = None
        self._attr_consumables = None
        self._attr_clean_type: str | None = None
        self._attr_clean_type_label: str | None = None
        self._attr_mop_level: str | None = None
        self._attr_edge_hugging_mopping: bool | None = None
        self._attr_clean_carpet: str | None = None

        # Set up device info for Home Assistant device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, item[CONF_ID])},
            name=item[CONF_NAME],
            manufacturer="Eufy",
            model=item[CONF_DESCRIPTION],
            connections={
                (CONNECTION_NETWORK_MAC, item[CONF_MAC]),
            },
        )

    async def async_update(self) -> None:
        """Synchronize state from the vacuum.

        This method is called periodically by Home Assistant to update the entity state.
        It retrieves the current state from the vacuum via the Tuya API and updates
        the entity attributes accordingly.

        If the vacuum is not supported or the IP address is not set, the method returns
        early. If the update fails, it increments a failure counter and sets an error
        code after a certain number of retries.
        """
        # Skip update if the model is not supported
        if self._attr_error_code == "UNSUPPORTED_MODEL":
            _LOGGER.debug("Skipping update for unsupported model: %s", self._attr_model_code)
            return

        # Skip update if the IP address is not set
        if not self.ip_address:
            _LOGGER.warning("Cannot update vacuum %s: IP address not set", self._attr_name)
            self._attr_error_code = "IP_ADDRESS"
            return

        # Skip update if vacuum object is not initialized
        if self.vacuum is None:
            _LOGGER.warning("Cannot update %s: vacuum not initialized", self._attr_name)
            self._attr_error_code = "INITIALIZATION_FAILED"
            return

        # Try to update the vacuum state
        try:
            await self.vacuum.async_get()
            self.update_failures = 0
            self.update_entity_values()
            _LOGGER.debug("Successfully updated vacuum %s", self._attr_name)
        except TuyaException as e:
            self.update_failures += 1
            _LOGGER.warning(
                "Failed to update vacuum %s. Failure count: %d/%d. Error: %s",
                self._attr_name,
                self.update_failures,
                UPDATE_RETRIES,
                str(e)
            )

            # Set error code after maximum retries
            if self.update_failures >= UPDATE_RETRIES:
                self._attr_error_code = "CONNECTION_FAILED"
                _LOGGER.error(
                    "Maximum update retries reached for vacuum %s. Marking as unavailable",
                    self._attr_name
                )

    async def pushed_update_handler(self) -> None:
        """Handle updates pushed from the vacuum.

        This method is called when the vacuum sends an update via the Tuya API.
        It updates the entity values and writes the state to Home Assistant.
        """
        self.update_entity_values()
        self.async_write_ha_state()

    def update_entity_values(self) -> None:
        """Update entity values from the vacuum's data points.

        This method updates all the entity attributes based on the current
        state of the vacuum's data points (DPS). It handles different vacuum models
        and ensures that all values are properly typed and formatted.

        The method is called both during periodic updates and when pushed updates
        are received from the vacuum.
        """
        # Skip if vacuum is not initialized
        if self.vacuum is None:
            _LOGGER.warning("Cannot update entity values: vacuum not initialized")
            return

        # Get the current data points from the vacuum
        self.tuyastatus = self.vacuum._dps

        if self.tuyastatus is None or not self.tuyastatus:
            current_time = time.time()
            # Only log warning when state changes or after 5 minutes
            if not self._no_data_warning_logged or (current_time - self._last_no_data_warning_time) >= 300:
                _LOGGER.warning("Vacuum %s has no data points available", self.name)
                self._last_no_data_warning_time = current_time
                self._no_data_warning_logged = True
            return

        # Reset warning state when data is available
        if self._no_data_warning_logged:
            _LOGGER.info("Data points now available, resuming normal updates")
            self._no_data_warning_logged = False

        _LOGGER.debug("Updating entity values from data points: %s", self.tuyastatus)

        # Update common attributes for all models
        self._update_state_and_error()
        self._update_mode_and_fan_speed()
        self._update_clean_param_attributes()

        # Update model-specific attributes
        self._update_cleaning_stats()

    def get_dps_code(self, code_name: str | TuyaCodes) -> str:
        """Get the DPS code for a specific function.

        First checks for model-specific DPS codes, then falls back to defaults.

        Args:
            code_name: The name of the code to retrieve, e.g., "BATTERY" or "BATTERY_LEVEL"
                       or a TuyaCodes enum member.

        Returns:
            The DPS code as a string
        """
        # If passed an enum member, get its name
        if isinstance(code_name, TuyaCodes):
            lookup_name = code_name.name
        else:
            # Map aliases to standard DPS names used in TuyaCodes and model dps_codes
            mapping = {
                "BATTERY": "BATTERY_LEVEL",
                "ERROR": "ERROR_CODE",
            }
            lookup_name = mapping.get(code_name, code_name)

        # ⚡ Bolt optimization: The DPS code string for a given lookup_name is static
        # for a specific model. By caching the extracted DPS string, we avoid rebuilding the
        # dictionary and performing the lookup on every data update and command dispatch.
        if lookup_name in self._dps_codes_memo:
            return self._dps_codes_memo[lookup_name]

        result = ""
        if self.vacuum is not None:
            try:
                model_dps_codes = self.vacuum.getDpsCodes()
                if isinstance(model_dps_codes, dict) and lookup_name in model_dps_codes:
                    result = str(model_dps_codes[lookup_name])
            except Exception as ex:
                _LOGGER.debug("Error getting model-specific DPS code for %s: %s", lookup_name, ex)

        if not result:
            # Fallback to defaults in TuyaCodes
            try:
                enum_value = getattr(TuyaCodes, lookup_name, None)
                if enum_value:
                    result = str(enum_value.value)
            except Exception:
                pass

        self._dps_codes_memo[lookup_name] = result
        return result

    def _get_consumables_codes(self) -> list[str]:
        """Get the consumables DPS codes.

        First checks for model-specific codes, then falls back to defaults.

        Returns:
            A list of DPS codes for consumables
        """
        # ⚡ Bolt optimization: Use cached consumables codes to avoid rebuilding the list
        # and splitting strings on every update cycle.
        if self._consumables_codes_cache is not None:
            return self._consumables_codes_cache

        if self.vacuum is None:
            return TUYA_CONSUMABLES_CODES

        # Get model-specific DPS codes
        model_dps_codes = self.vacuum.getDpsCodes()

        # Return model-specific code if available, otherwise use default
        if "CONSUMABLES" in model_dps_codes:
            # Model-specific consumables can be a list or comma-separated string
            consumables = model_dps_codes["CONSUMABLES"]
            if isinstance(consumables, str):
                self._consumables_codes_cache = [code.strip() for code in consumables.split(",")]
            else:
                self._consumables_codes_cache = list(consumables)
            return self._consumables_codes_cache

        # Fall back to default codes
        self._consumables_codes_cache = TUYA_CONSUMABLES_CODES
        return TUYA_CONSUMABLES_CODES

    def _update_state_and_error(self) -> None:
        """Update the state and error code attributes."""
        if self.tuyastatus is None:
            return

        # Get state and error code from data points using model-specific DPS codes
        tuya_state = self.tuyastatus.get(self.get_dps_code("STATUS"))
        error_code = self.tuyastatus.get(self.get_dps_code("ERROR_CODE"))

        # Update state attribute
        if tuya_state is not None and self.vacuum is not None:
            self._attr_tuya_state = self.vacuum.getRoboVacHumanReadableValue(RobovacCommand.STATUS, tuya_state)
            _LOGGER.debug(
                "in _update_state_and_error, tuya_state: %s, self._attr_tuya_state: %s.",
                tuya_state,
                self._attr_tuya_state
            )
        else:
            self._attr_tuya_state = 0

        # Update error code attribute
        if error_code is not None and self.vacuum is not None:
            self._attr_error_code = self.vacuum.getRoboVacHumanReadableValue(RobovacCommand.ERROR, error_code)
            _LOGGER.debug(
                "in _update_state_and_error, error_code: %s, self._attr_error_code: %s.",
                error_code,
                self._attr_error_code
            )
        else:
            self._attr_error_code = 0

    def _update_clean_param_attributes(self) -> None:
        """Decode DPS 154 (clean params) for vacuum card / automations."""
        if self.tuyastatus is None or self.vacuum is None:
            return
        if RobovacCommand.CLEAN_PARAM not in self.vacuum.getSupportedCommands():
            self._attr_clean_type = None
            self._attr_clean_type_label = None
            self._attr_mop_level = None
            self._attr_edge_hugging_mopping = None
            self._attr_clean_carpet = None
            return

        raw = self.tuyastatus.get(self.get_dps_code("CLEAN_PARAM"))
        if raw is None or raw == "":
            return

        try:
            raw_str = raw if isinstance(raw, str) else str(raw)
            decoded = decode_clean_param_response(raw_str)
            params = merge_clean_param_layers(decoded)
            clean_type = params.get("clean_type")
            if clean_type is None:
                return
            self._attr_clean_type = str(clean_type)
            self._attr_clean_type_label = _clean_type_label(str(clean_type))
            if "mop_level" in params:
                self._attr_mop_level = str(params["mop_level"])
            if "edge_hugging_mopping" in params:
                self._attr_edge_hugging_mopping = bool(params["edge_hugging_mopping"])
            if "clean_carpet" in params:
                self._attr_clean_carpet = str(params["clean_carpet"])
        except Exception as ex:
            _LOGGER.debug("Clean param decode failed for %s: %s", self.name, ex)

    def _update_mode_and_fan_speed(self) -> None:
        """Update the mode and fan speed attributes."""
        if self.tuyastatus is None:
            return

        # Get mode and fan speed from data points using model-specific DPS codes
        mode = self.tuyastatus.get(self.get_dps_code("MODE"))
        fan_speed = self.tuyastatus.get(self.get_dps_code("FAN_SPEED"))

        # Update mode attribute
        if mode is not None and self.vacuum is not None:
            self._attr_mode = self.vacuum.getRoboVacHumanReadableValue(RobovacCommand.MODE, mode)
            _LOGGER.debug(
                "in _update_mode_and_fan_speed, mode: %s, self._attr_mode: %s.",
                mode,
                self._attr_mode
            )
        else:
            self._attr_mode = ""

        # Update fan speed attribute
        self._attr_fan_speed = fan_speed if fan_speed is not None else ""

        # Format fan speed for display
        if isinstance(self.fan_speed, str):
            if self.fan_speed == "No_suction":
                self._attr_fan_speed = "No Suction"
            elif self.fan_speed == "Boost_IQ":
                self._attr_fan_speed = "Boost IQ"
            elif self.fan_speed == "Quiet":
                self._attr_fan_speed = (
                    "Pure" if "Pure" in self._attr_fan_speed_list else "Quiet"
                )

    def _update_cleaning_stats(self) -> None:
        """Update cleaning statistics and settings attributes.

        Note: auto_return, do_not_disturb, and boost_iq are device settings that
        exist independently of cleaning_time. They are updated unconditionally
        whenever tuyastatus is available.
        """
        if self.tuyastatus is None:
            return

        # Update cleaning area using model-specific DPS code
        cleaning_area = self.tuyastatus.get(self.get_dps_code("CLEANING_AREA"))
        if cleaning_area is not None:
            self._attr_cleaning_area = str(cleaning_area)

        # Update cleaning time using model-specific DPS code
        cleaning_time = self.tuyastatus.get(self.get_dps_code("CLEANING_TIME"))
        if cleaning_time is not None:
            self._attr_cleaning_time = str(cleaning_time)

        # Update device settings — these are independent of cleaning_time and
        # must not be nested inside the cleaning_time block or they will only
        # update when cleaning_time is present in the payload.
        auto_return = self.tuyastatus.get(self.get_dps_code("AUTO_RETURN"))
        self._attr_auto_return = str(auto_return) if auto_return is not None else None

        do_not_disturb = self.tuyastatus.get(self.get_dps_code("DO_NOT_DISTURB"))
        self._attr_do_not_disturb = str(do_not_disturb) if do_not_disturb is not None else None

        boost_iq = self.tuyastatus.get(self.get_dps_code("BOOST_IQ"))
        self._attr_boost_iq = str(boost_iq) if boost_iq is not None else None

        # Handle consumables
        if (
            isinstance(self.robovac_supported, int)
            and self.robovac_supported & RoboVacEntityFeature.CONSUMABLES
            and self.tuyastatus is not None
        ):
            # Use model-specific consumables codes
            for CONSUMABLE_CODE in self._get_consumables_codes():
                if (
                    CONSUMABLE_CODE in self.tuyastatus
                    and self.tuyastatus.get(CONSUMABLE_CODE) is not None
                ):
                    consumable_data = self.tuyastatus.get(CONSUMABLE_CODE)
                    if isinstance(consumable_data, str):
                        # ⚡ Bolt optimization: Avoid expensive base64 decode and json.loads on
                        # every state update by memoizing the parsed result based on the raw base64 string.
                        if self._last_consumable_data != consumable_data:
                            self._last_consumable_data = consumable_data
                            try:
                                consumables = json.loads(
                                    base64.b64decode(consumable_data).decode("ascii")
                                )
                                if (
                                    isinstance(consumables, dict)
                                    and isinstance(consumables.get("consumable"), dict)
                                    and "duration" in consumables["consumable"]
                                ):
                                    self._attr_consumables = consumables["consumable"]["duration"]
                            except Exception as e:
                                _LOGGER.warning("Failed to decode consumable data: %s", str(e))

    async def async_locate(self, **kwargs: Any) -> None:
        """Locate the vacuum cleaner.

        Args:
            **kwargs: Additional arguments passed from Home Assistant.
        """
        _LOGGER.debug("Locate Pressed")
        if self.vacuum is None:
            _LOGGER.error("Cannot locate vacuum: vacuum not initialized")
            return

        locate_code = self.get_dps_code("LOCATE")
        if self.tuyastatus is not None and self.tuyastatus.get(locate_code):
            await self.vacuum.async_set({locate_code: False})
        else:
            await self.vacuum.async_set({locate_code: True})

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock.

        Args:
            **kwargs: Additional arguments passed from Home Assistant.
        """
        _LOGGER.debug("Return home Pressed")
        if self.vacuum is None:
            _LOGGER.error("Cannot return to base: vacuum not initialized")
            return

        payload: dict[str, Any] = {
            self.get_dps_code("RETURN_HOME"): self.vacuum.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return")
        }

        mode_return_value = self.vacuum.getRoboVacCommandValue(RobovacCommand.MODE, "return")
        if mode_return_value != "return":
            payload[self.get_dps_code("MODE")] = mode_return_value

        # For models with boolean START_PAUSE (e.g. T2128, T2276), DPS 2 is the
        # execution trigger — without it, the device ACKs but doesn't physically act.
        start_value = self.vacuum.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start")
        if start_value != "start":
            payload[self.get_dps_code("START_PAUSE")] = start_value

        await self.vacuum.async_set(payload)

    async def async_start(self, **kwargs: Any) -> None:
        """Start the vacuum cleaner in auto mode.

        Args:
            **kwargs: Additional arguments passed from Home Assistant.
        """
        self._attr_mode = "auto"
        if self.vacuum is None:
            _LOGGER.error("Cannot start vacuum: vacuum not initialized")
            return

        payload: dict[str, Any] = {
            self.get_dps_code("MODE"): self.vacuum.getRoboVacCommandValue(RobovacCommand.MODE, "auto")
        }

        # For models with boolean START_PAUSE (e.g. T2118, T2128), also toggle start
        start_value = self.vacuum.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start")
        if start_value != "start":
            payload[self.get_dps_code("START_PAUSE")] = start_value

        await self.vacuum.async_set(payload)

    async def async_pause(self, **kwargs: Any) -> None:
        """Pause the vacuum cleaner.

        Args:
            **kwargs: Additional arguments passed from Home Assistant.
        """
        if self.vacuum is None:
            _LOGGER.error("Cannot pause vacuum: vacuum not initialized")
            return

        payload: dict[str, Any] = {
            self.get_dps_code("START_PAUSE"): self.vacuum.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause")
        }

        mode_pause_value = self.vacuum.getRoboVacCommandValue(RobovacCommand.MODE, "pause")
        if mode_pause_value != "pause":
            payload[self.get_dps_code("MODE")] = mode_pause_value

        await self.vacuum.async_set(payload)

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop the vacuum cleaner.

        Args:
            **kwargs: Additional arguments passed from Home Assistant.
        """
        await self.async_return_to_base()

    async def async_clean_spot(self, **kwargs: Any) -> None:
        """Perform a spot clean.

        Args:
            **kwargs: Additional arguments passed from Home Assistant.
        """
        _LOGGER.debug("Spot Clean Pressed")
        if self.vacuum is None:
            _LOGGER.error("Cannot clean spot: vacuum not initialized")
            return

        await self.vacuum.async_set({
            self.get_dps_code("MODE"): self.vacuum.getRoboVacCommandValue(RobovacCommand.MODE, "spot")
        })

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed.

        Args:
            fan_speed: The fan speed to set.
            **kwargs: Additional arguments passed from Home Assistant.
        """
        _LOGGER.debug("Fan Speed Selected: %s", fan_speed)
        if self.vacuum is None:
            _LOGGER.error("Cannot set fan speed: vacuum not initialized")
            return

        normalized_fan_speed = fan_speed.lower().replace(" ", "_")

        _LOGGER.debug("Normalized Fan Speed: %s", normalized_fan_speed)

        await self.vacuum.async_set({
            self.get_dps_code("FAN_SPEED"): self.vacuum.getRoboVacCommandValue(
                RobovacCommand.FAN_SPEED, normalized_fan_speed
            )
        })
        self.update_entity_values()
        if self.hass:
            self.async_write_ha_state()

    @property
    def clean_type(self) -> str | None:
        """Decoded global clean type from DPS 154 (snake_case), if available."""
        return self._attr_clean_type

    @property
    def mop_level(self) -> str | None:
        """Decoded mop water level from DPS 154, if available."""
        return self._attr_mop_level

    @property
    def edge_hugging_mopping(self) -> bool | None:
        """Edge-hugging mop mode from DPS 154, if present in the last decode."""
        return self._attr_edge_hugging_mopping

    async def async_set_clean_param(
        self,
        *,
        clean_type: str | None = None,
        mop_level: str | None = None,
        edge_hugging_mopping: bool | None = None,
    ) -> None:
        """Write DPS 154 by patching the current protobuf payload."""
        if self.vacuum is None:
            raise HomeAssistantError("Vacuum not initialized")
        if RobovacCommand.CLEAN_PARAM not in self.vacuum.getSupportedCommands():
            raise HomeAssistantError("Clean parameters are not supported on this model")
        dps = self.get_dps_code("CLEAN_PARAM")
        raw = self.tuyastatus.get(dps) if self.tuyastatus else None
        if raw is None or raw == "":
            raw = getattr(self.vacuum.model_details, "default_clean_param_dps154", None)
        if raw is None or raw == "":
            raise HomeAssistantError("Clean parameter DPS is empty; wait for the next poll")
        raw_str = raw if isinstance(raw, str) else str(raw)
        try:
            new_b64 = patch_clean_param_dps154(
                raw_str,
                clean_type=clean_type,
                mop_level=mop_level,
                edge_hugging_mopping=edge_hugging_mopping,
            )
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err
        await self.vacuum.async_set({dps: new_b64})
        if self.tuyastatus is None:
            self.tuyastatus = {}
        self.tuyastatus[dps] = new_b64
        if hasattr(self.vacuum, "_dps"):
            self.vacuum._dps[dps] = new_b64
        self.update_entity_values()
        if self.hass:
            self.async_write_ha_state()

    async def async_set_mop_level(self, mop_level: str) -> None:
        """Set mop water level (low / middle / high) via DPS 154."""
        await self.async_set_clean_param(mop_level=mop_level)

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list | None = None,
        **kwargs: Any
    ) -> None:
        """Send a command to a vacuum cleaner.

        Args:
            command: The command to send.
            params: Optional parameters for the command.
            **kwargs: Additional arguments passed from Home Assistant.
        """
        _LOGGER.debug("Send Command %s Pressed", command)
        if self.vacuum is None:
            _LOGGER.error("Cannot send command: vacuum not initialized")
            return

        # Mode commands
        mode_commands = {
            "edgeClean": "edge",
            "smallRoomClean": "small_room",
            "autoClean": "auto"
        }

        if command in mode_commands:
            command_data = self._get_mode_command_data(mode_commands[command])
            if command_data:
                await self.vacuum.async_set(command_data)
        elif command == "autoReturn":
            # Toggle the auto return setting
            new_value = not self._is_value_true(self.auto_return)
            await self.vacuum.async_set({
                self.get_dps_code("AUTO_RETURN"): new_value
            })
        elif command == "doNotDisturb":
            # Toggle the do not disturb setting
            new_value = not self._is_value_true(self.do_not_disturb)
            await self.vacuum.async_set({
                self.get_dps_code("DO_NOT_DISTURB"): new_value
            })
        elif command == "boostIQ":
            # Toggle the boost IQ setting
            new_value = not self._is_value_true(self.boost_iq)
            await self.vacuum.async_set({
                self.get_dps_code("BOOST_IQ"): new_value
            })
        elif command in ("roomClean", "room_clean") and params is not None and isinstance(params, dict):
            room_ids = params.get("roomIds") or params.get("room_ids", [1])
            count = params.get("count", 1)
            clean_request = {"roomIds": room_ids, "cleanTimes": count}
            method_call = {
                "method": "selectRoomsClean",
                "data": clean_request,
                "timestamp": round(time.time() * 1000),
            }
            json_str = json.dumps(method_call, separators=(",", ":"))
            base64_str = base64.b64encode(json_str.encode("utf8")).decode("utf8")
            _LOGGER.debug("roomClean call %s", json_str)
            await self.vacuum.async_set({TuyaCodes.ROOM_CLEAN: base64_str})
            # Wait for the vacuum to ACK DPS 124 before sending the start command.
            # Without this delay, DPS 2 arrives before the room selection is processed
            # and the vacuum ignores the start command.
            await asyncio.sleep(1)
            await self.vacuum.async_set({TuyaCodes.START_PAUSE: True})

    async def async_will_remove_from_hass(self) -> None:
        """Handle removal from Home Assistant."""
        if self.vacuum is None:
            _LOGGER.debug("Cannot disable vacuum: vacuum not initialized")
            return

        await self.vacuum.async_disable()
