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

import ast
import base64
import json
import logging
import time
from datetime import timedelta
from typing import Any, Optional

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
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VACS, DOMAIN, PING_RATE, REFRESH_RATE, TIMEOUT
from .errors import getErrorMessage
from .robovac import ModelNotSupportedException, RoboVac
from .tuyalocalapi import TuyaException
from .vacuums.base import (
    RobovacCommand,
    RoboVacEntityFeature,
    TUYA_CONSUMABLES_CODES,
    TuyaCodes,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=REFRESH_RATE)
UPDATE_RETRIES = 3

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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize the Eufy Robovac config entry."""
    vacuums = config_entry.data[CONF_VACS]
    for item in vacuums:
        item = vacuums[item]
        entity = RoboVacEntity(item)
        hass.data[DOMAIN][CONF_VACS][item[CONF_ID]] = entity
        async_add_entities([entity])


class RoboVacEntity(StateVacuumEntity):
    """Eufy Robovac vacuum entity.

    This class represents a Eufy Robovac vacuum cleaner in Home Assistant.
    It handles the communication with the vacuum via the Tuya local API and
    provides the necessary functionality to control and monitor the vacuum.
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
    _attr_error_code: int | str | None = None
    _attr_tuya_state: int | str | None = None

    @property
    def robovac_supported(self) -> int | None:
        """Return the supported features of the vacuum cleaner."""
        return self._attr_robovac_supported

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
        """Set the state of the vacuum cleaner (for test compatibility)."""
        self._attr_tuya_state = value

    @property
    def error_code(self) -> int | str | None:
        """Return the error code of the vacuum cleaner."""
        return self._attr_error_code

    @error_code.setter
    def error_code(self, value: int | str | None) -> None:
        """Set the error code of the vacuum cleaner."""
        self._attr_error_code = value

    @property
    def model_code(self) -> str | None:
        """Return the model code of the vacuum cleaner."""
        return self._attr_model_code

    @property
    def access_token(self) -> str | None:
        """Return the Tuya local key of the vacuum cleaner."""
        return self._attr_access_token

    @property
    def ip_address(self) -> str | None:
        """Return the IP address of the vacuum cleaner."""
        return self._attr_ip_address

    def _is_value_true(self, value: Any) -> bool:
        """Check if a value is considered 'true', either as a boolean or string."""
        if value is True:
            return True
        if isinstance(value, str):
            return value == "True" or value.lower() == "true"
        return False

    @property
    def activity(self) -> VacuumActivity | None:
        """Return the current activity of the vacuum cleaner."""
        if self._attr_tuya_state is None:
            return None
        # If an error code is set and not "no_error", treat as error
        if (
            self.error_code not in [0, "no_error", None]
        ):
            _LOGGER.debug(
                "State changed to error. Error message: %s",
                getErrorMessage(self.error_code),
            )
            return VacuumActivity.ERROR
        # Map Tuya status strings to VacuumActivity
        if self._attr_tuya_state in ["Charging", "completed"]:
            return VacuumActivity.DOCKED
        if self._attr_tuya_state == "Recharge":
            return VacuumActivity.RETURNING
        if self._attr_tuya_state in ["Sleeping", "standby"]:
            return VacuumActivity.IDLE
        if self._attr_tuya_state == "Paused":
            return VacuumActivity.PAUSED
        # Otherwise assume cleaning
        return VacuumActivity.CLEANING

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device-specific state attributes of this vacuum."""
        data: dict[str, Any] = {}

        if self._attr_error_code not in [None, 0, "no_error"]:
            data[ATTR_ERROR] = getErrorMessage(self._attr_error_code)
        if (
            self.robovac_supported
            and self.robovac_supported & RoboVacEntityFeature.CLEANING_AREA
            and self.cleaning_area
        ):
            data[ATTR_CLEANING_AREA] = self.cleaning_area
        if (
            self.robovac_supported
            and self.robovac_supported & RoboVacEntityFeature.CLEANING_TIME
            and self.cleaning_time
        ):
            data[ATTR_CLEANING_TIME] = self.cleaning_time
        if (
            self.robovac_supported
            and self.robovac_supported & RoboVacEntityFeature.AUTO_RETURN
            and self.auto_return
        ):
            data[ATTR_AUTO_RETURN] = self.auto_return
        if (
            self.robovac_supported
            and self.robovac_supported & RoboVacEntityFeature.DO_NOT_DISTURB
            and self.do_not_disturb
        ):
            data[ATTR_DO_NOT_DISTURB] = self.do_not_disturb
        if (
            self.robovac_supported
            and self.robovac_supported & RoboVacEntityFeature.BOOST_IQ
            and self.boost_iq
        ):
            data[ATTR_BOOST_IQ] = self.boost_iq
        if (
            self.robovac_supported
            and self.robovac_supported & RoboVacEntityFeature.CONSUMABLES
            and self.consumables
        ):
            data[ATTR_CONSUMABLES] = self.consumables
        if self.mode:
            data[ATTR_MODE] = self.mode
        return data

    def __init__(self, item: dict[str, Any]) -> None:
        """Initialize Eufy Robovac entity."""
        super().__init__()

        # Initialize basic attributes
        self._attr_battery_level = 0
        self._attr_name = item[CONF_NAME]
        self._attr_unique_id = item[CONF_ID]
        self._attr_model_code = item[CONF_MODEL]
        self._attr_ip_address = item[CONF_IP_ADDRESS]
        self._attr_access_token = item[CONF_ACCESS_TOKEN]
        self.vacuum: Optional[RoboVac] = None
        self.update_failures = 0
        self.tuyastatus: dict[str, Any] | None = None

        # Initialize the RoboVac connection
        try:
            model_code_prefix = ""
            if self.model_code:
                model_code_prefix = self.model_code[:5]

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
                self._attr_model_code,
            )
        except ModelNotSupportedException:
            _LOGGER.error("Model %s is not supported", self._attr_model_code)
            self._attr_error_code = "UNSUPPORTED_MODEL"

        if self.vacuum is not None:
            features = int(self.vacuum.getHomeAssistantFeatures())
            self._attr_supported_features = VacuumEntityFeature(features)
            self._attr_robovac_supported = self.vacuum.getRoboVacFeatures()
            self._attr_fan_speed_list = self.vacuum.getFanSpeeds()
            _LOGGER.debug(
                "Vacuum %s supports features: %s",
                self._attr_name,
                self._attr_supported_features,
            )
        else:
            self._attr_supported_features = VacuumEntityFeature(0)
            self._attr_robovac_supported = 0
            self._attr_fan_speed_list = []
            _LOGGER.warning(
                "Vacuum %s initialization failed, features not available",
                self._attr_name,
            )

        self._attr_mode = None
        self._attr_consumables = None

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
        """Synchronize state from the vacuum."""
        if self._attr_error_code == "UNSUPPORTED_MODEL":
            _LOGGER.debug("Skipping update for unsupported model: %s", self._attr_model_code)
            return

        if not self.ip_address:
            _LOGGER.warning("Cannot update vacuum %s: IP address not set", self._attr_name)
            self._attr_error_code = "IP_ADDRESS"
            return

        if self.vacuum is None:
            _LOGGER.warning("Cannot update %s: vacuum not initialized", self._attr_name)
            self._attr_error_code = "INITIALIZATION_FAILED"
            return

        try:
            await self.vacuum.async_get()
            self.update_failures = 0
            self.update_entity_values()
            _LOGGER.debug("Successfully updated vacuum %s", self._attr_name)
        except TuyaException as exc:
            self.update_failures += 1
            _LOGGER.warning(
                "Failed to update vacuum %s. Failure count: %d/%d. Error: %s",
                self._attr_name,
                self.update_failures,
                UPDATE_RETRIES,
                str(exc),
            )
            if self.update_failures >= UPDATE_RETRIES:
                self._attr_error_code = "CONNECTION_FAILED"
                _LOGGER.error(
                    "Maximum update retries reached for vacuum %s. Marking as unavailable",
                    self._attr_name,
                )

    async def pushed_update_handler(self) -> None:
        """Handle updates pushed from the vacuum."""
        self.update_entity_values()
        self.async_write_ha_state()

    def update_entity_values(self) -> None:
        """Update entity values from the vacuum's data points."""
        if self.vacuum is None:
            _LOGGER.warning("Cannot update entity values: vacuum not initialized")
            return

        self.tuyastatus = self.vacuum._dps
        if self.tuyastatus is None:
            _LOGGER.warning("Cannot update entity values: no data points available")
            return

        _LOGGER.debug("Updating entity values from data points: %s", self.tuyastatus)

        self._update_battery_level()
        self._update_state_and_error()
        self._update_mode_and_fan_speed()
        self._update_cleaning_stats()

    def _get_dps_code(self, code_name: str) -> str:
        """Get the DPS code for a specific function."""
        if self.vacuum is None:
            return getattr(TuyaCodes, code_name, "")

        model_dps_codes = self.vacuum.getDpsCodes()
        if code_name in model_dps_codes:
            return model_dps_codes[code_name]
        return getattr(TuyaCodes, code_name, "")

    def _get_consumables_codes(self) -> list[str]:
        """Get the consumables DPS codes."""
        if self.vacuum is None:
            return TUYA_CONSUMABLES_CODES

        model_dps_codes = self.vacuum.getDpsCodes()
        if "CONSUMABLES" in model_dps_codes:
            consumables = model_dps_codes["CONSUMABLES"]
            if isinstance(consumables, str):
                return [code.strip() for code in consumables.split(",")]
            return consumables

        return TUYA_CONSUMABLES_CODES

    def _update_battery_level(self) -> None:
        """Update battery level from DPS."""
        if self.tuyastatus is None:
            return
        battery_level = self.tuyastatus.get(self._get_dps_code("BATTERY_LEVEL"))
        if battery_level is not None:
            try:
                self._attr_battery_level = max(0, min(100, int(battery_level)))
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid battery level value: %s", battery_level)
                self._attr_battery_level = 0
        else:
            self._attr_battery_level = 0

    def _update_state_and_error(self) -> None:
        """Update status and error code from DPS."""
        if self.tuyastatus is None:
            return
        tuya_state = self.tuyastatus.get(self._get_dps_code("STATUS"))
        error_code = self.tuyastatus.get(self._get_dps_code("ERROR_CODE"))
        self._attr_tuya_state = tuya_state if tuya_state is not None else 0
        self._attr_error_code = error_code if error_code is not None else 0

    def _update_mode_and_fan_speed(self) -> None:
        """Update mode and fan speed from DPS."""
        if self.tuyastatus is None:
            return
        mode = self.tuyastatus.get(self._get_dps_code("MODE"))
        fan_speed = self.tuyastatus.get(self._get_dps_code("FAN_SPEED"))
        self._attr_mode = mode if mode is not None else ""
        self._attr_fan_speed = fan_speed if fan_speed is not None else ""
        if isinstance(self.fan_speed, str):
            if self.fan_speed == "No_suction":
                self._attr_fan_speed = "No Suction"
            elif self.fan_speed == "Boost_IQ":
                self._attr_fan_speed = "Boost IQ"
            elif self.fan_speed == "Quiet":
                self._attr_fan_speed = "Quiet"

    def _update_cleaning_stats(self) -> None:
        """Update consumables and cleaning statistics from DPS."""
        if self.tuyastatus is None:
            return
        cleaning_area = self.tuyastatus.get(self._get_dps_code("CLEANING_AREA"))
        if cleaning_area is not None:
            self._attr_cleaning_area = str(cleaning_area)

        cleaning_time = self.tuyastatus.get(self._get_dps_code("CLEANING_TIME"))
        if cleaning_time is not None:
            self._attr_cleaning_time = str(cleaning_time)

            auto_return = self.tuyastatus.get(self._get_dps_code("AUTO_RETURN"))
            self._attr_auto_return = str(auto_return) if auto_return is not None else None

            do_not_disturb = self.tuyastatus.get(self._get_dps_code("DO_NOT_DISTURB"))
            self._attr_do_not_disturb = (
                str(do_not_disturb) if do_not_disturb is not None else None
            )

            boost_iq = self.tuyastatus.get(self._get_dps_code("BOOST_IQ"))
            self._attr_boost_iq = str(boost_iq) if boost_iq is not None else None

        if (
            isinstance(self.robovac_supported, int)
            and self.robovac_supported & RoboVacEntityFeature.CONSUMABLES
            and self.tuyastatus is not None
        ):
            for consumable_code in self._get_consumables_codes():
                if consumable_code in self.tuyastatus:
                    consumable_data = self.tuyastatus.get(consumable_code)
                    if isinstance(consumable_data, str):
                        try:
                            consumables = ast.literal_eval(
                                base64.b64decode(consumable_data).decode("ascii")
                            )
                            if (
                                "consumable" in consumables
                                and "duration" in consumables["consumable"]
                            ):
                                self._attr_consumables = consumables["consumable"]["duration"]
                        except Exception as exc:
                            _LOGGER.warning("Failed to decode consumable data: %s", str(exc))

    # -----------------------------
    # CONTROL METHODS
    # -----------------------------

    async def async_locate(self, **kwargs: Any) -> None:
        """Beep/locate the vacuum."""
        _LOGGER.info("Locate pressed")
        if self.vacuum is None:
            _LOGGER.error("Cannot locate vacuum: vacuum not initialized")
            return

        locate_code = self._get_dps_code("LOCATE")

        # T2320 uses DPS 153 with base64 token, not a boolean
        if (self.model_code or "").startswith("T2320"):
            await self.vacuum.async_set({locate_code: "AggC"})
            return

        # Fallback: toggle boolean for other models
        if self.tuyastatus is not None and self.tuyastatus.get(locate_code):
            await self.vacuum.async_set({locate_code: False})
        else:
            await self.vacuum.async_set({locate_code: True})

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Send the vacuum back to the dock."""
        _LOGGER.info("Return home pressed")
        if self.vacuum is None:
            _LOGGER.error("Cannot return to base: vacuum not initialized")
            return

        # T2320: use MODE (DP 152) base64 token for dock/home.
        # The correct token for returning home is "AggN".
        if (self.model_code or "").startswith("T2320"):
            mode_code = self._get_dps_code("MODE")
            await self.vacuum.async_set({mode_code: "AggN"})
            return

        # Fallback for other models: legacy RETURN_HOME boolean
        return_home_code = self._get_dps_code("RETURN_HOME")
        await self.vacuum.async_set({return_home_code: True})

    async def async_start(self, **kwargs: Any) -> None:
        """Start cleaning (auto)."""
        if self.vacuum is None:
            _LOGGER.error("Cannot start vacuum: vacuum not initialized")
            return

        if (self.model_code or "").startswith("T2320"):
            # T2320: start/auto is DPS 152 with base64 token.  The app uses "AggG".
            mode_code = self._get_dps_code("MODE")
            self._attr_mode = "auto"
            await self.vacuum.async_set({mode_code: "AggG"})
            return

        # Generic fallback: try MODE string (if supported) or START_PAUSE boolean
        self._attr_mode = "auto"
        mode_code = self._get_dps_code("MODE")
        if mode_code:
            await self.vacuum.async_set({mode_code: self.mode})
        else:
            await self.vacuum.async_set({self._get_dps_code("START_PAUSE"): True})

    async def async_pause(self, **kwargs: Any) -> None:
        """Pause cleaning (stop in place)."""
        if self.vacuum is None:
            _LOGGER.error("Cannot pause vacuum: vacuum not initialized")
            return

        if (self.model_code or "").startswith("T2320"):
            # T2320: pause uses DPS 152 with base64 token "AA==".
            mode_code = self._get_dps_code("MODE")
            await self.vacuum.async_set({mode_code: "AA=="})
            return

        # Fallback: START_PAUSE False for other models
        start_pause_code = self._get_dps_code("START_PAUSE")
        await self.vacuum.async_set({start_pause_code: False})

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop cleaning (mapped to return-to-dock)."""
        # For all models, stopping the robot returns it to the dock.
        await self.async_return_to_base()

    async def async_clean_spot(self, **kwargs: Any) -> None:
        """Perform a spot clean-up."""
        _LOGGER.info("Spot clean pressed")
        if self.vacuum is None:
            _LOGGER.error("Cannot clean spot: vacuum not initialized")
            return

        mode_code = self._get_dps_code("MODE")
        if (self.model_code or "").startswith("T2320"):
            # T2320: spot clean via DPS 152 with base64 token.
            await self.vacuum.async_set({mode_code: "AggO"})
            return

        # Fallback for other models (legacy string)
        await self.vacuum.async_set({mode_code: "Spot"})

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        _LOGGER.info("Fan speed selected")
        if self.vacuum is None:
            _LOGGER.error("Cannot set fan speed: vacuum not initialized")
            return

        if fan_speed == "No Suction":
            fan_speed = "No_suction"
        elif fan_speed == "Boost IQ":
            fan_speed = "Boost_IQ"
        elif fan_speed == "Pure":
            fan_speed = "Quiet"

        fan_speed_code = self._get_dps_code("FAN_SPEED")
        await self.vacuum.async_set({fan_speed_code: fan_speed})

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a command to a vacuum cleaner."""
        _LOGGER.info("Send command %s pressed", command)
        if self.vacuum is None:
            _LOGGER.error("Cannot send command: vacuum not initialized")
            return

        mode_code = self._get_dps_code("MODE")

        # Prefer explicit T2320 tokens when available
        is_t2320 = (self.model_code or "").startswith("T2320")

        if command == "edgeClean":
            await self.vacuum.async_set({mode_code: "Edge"})
        elif command == "smallRoomClean":
            await self.vacuum.async_set({mode_code: "SmallRoom"})
        elif command == "autoClean":
            if is_t2320:
                # Use "AggG" for auto clean on T2320 (matches the app)
                await self.vacuum.async_set({mode_code: "AggG"})
            else:
                await self.vacuum.async_set({mode_code: "auto"})
        elif command == "autoReturn":
            if is_t2320:
                # Return to base uses "AggN" on the X9 Pro
                await self.vacuum.async_set({mode_code: "AggN"})
            else:
                auto_return_code = self._get_dps_code("AUTO_RETURN")
                if self._is_value_true(self.auto_return):
                    await self.vacuum.async_set({auto_return_code: False})
                else:
                    await self.vacuum.async_set({auto_return_code: True})
        elif command == "doNotDisturb":
            do_not_disturb_code = self._get_dps_code("DO_NOT_DISTURB")
            if self._is_value_true(self.do_not_disturb):
                # Turn off DND
                await self.vacuum.async_set({"139": "MEQ4MDAwMDAw"})
                await self.vacuum.async_set({do_not_disturb_code: False})
            else:
                # Turn on DND
                await self.vacuum.async_set({"139": "MTAwMDAwMDAw"})
                await self.vacuum.async_set({do_not_disturb_code: True})
        elif command == "boostIQ":
            boost_iq_code = self._get_dps_code("BOOST_IQ")
            await self.vacuum.async_set({boost_iq_code: not self._is_value_true(self.boost_iq)})
        elif command == "roomClean" and params is not None and isinstance(params, dict):
            room_ids = params.get("roomIds", [1])
            count = params.get("count", 1)
            clean_request = {"roomIds": room_ids, "cleanTimes": count}
            method_call = {
                "method": "selectRoomsClean",
                "data": clean_request,
                "timestamp": round(time.time() * 1000),
            }
            json_str = json.dumps(method_call, separators=(",", ":"))
            base64_str = base64.b64encode(json_str.encode("utf8")).decode("utf8")
            _LOGGER.info("roomClean call %s", json_str)
            await self.vacuum.async_set({TuyaCodes.ROOM_CLEAN: base64_str})

    async def async_will_remove_from_hass(self) -> None:
        """Handle removal from Home Assistant."""
        if self.vacuum is None:
            _LOGGER.debug("Cannot disable vacuum: vacuum not initialized")
            return
        await self.vacuum.async_disable()
