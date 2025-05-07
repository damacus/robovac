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

"""Config flow for Eufy Robovac integration."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from typing import Any, Optional

import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_COUNTRY_CODE,
    CONF_DESCRIPTION,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_TIME_ZONE,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_AUTODISCOVERY, CONF_VACS, DOMAIN
from .countries import (
    get_phone_code_by_country_code,
    get_phone_code_by_region,
    get_region_by_country_code,
    get_region_by_phone_code,
)
from .eufywebapi import EufyLogon
from .tuyawebapi import TuyaAPISession

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


def get_eufy_vacuums(self: dict[str, Any]) -> requests.Response:
    """Login to Eufy and get the vacuum details.

    Returns:
        Response: The API response containing vacuum information

    Raises:
        CannotConnect: If connection to the API fails
        InvalidAuth: If authentication fails
    """
    eufy_session = EufyLogon(self["username"], self["password"])
    response = eufy_session.get_user_info()

    # Check if response is valid
    if response is None:
        raise CannotConnect
    if response.status_code != 200:
        raise CannotConnect

    user_response = response.json()
    if user_response["res_code"] != 1:
        raise InvalidAuth

    response = eufy_session.get_device_info(
        user_response["user_info"]["request_host"],
        user_response["user_info"]["id"],
        user_response["access_token"],
    )

    # Check if response is valid
    if response is None:
        raise CannotConnect

    device_response = response.json()

    response = eufy_session.get_user_settings(
        user_response["user_info"]["request_host"],
        user_response["user_info"]["id"],
        user_response["access_token"],
    )

    # Check if response is valid
    if response is None:
        raise CannotConnect

    settings_response = response.json()

    self[CONF_CLIENT_ID] = user_response["user_info"]["id"]
    if (
        "tuya_home" in settings_response["setting"]["home_setting"]
        and "tuya_region_code"
        in settings_response["setting"]["home_setting"]["tuya_home"]
    ):
        self[CONF_REGION] = settings_response["setting"]["home_setting"]["tuya_home"][
            "tuya_region_code"
        ]
        if user_response["user_info"]["phone_code"]:
            self[CONF_COUNTRY_CODE] = user_response["user_info"]["phone_code"]
        else:
            self[CONF_COUNTRY_CODE] = get_phone_code_by_region(self[CONF_REGION])
    elif user_response["user_info"]["phone_code"]:
        self[CONF_REGION] = get_region_by_phone_code(
            user_response["user_info"]["phone_code"]
        )
        self[CONF_COUNTRY_CODE] = user_response["user_info"]["phone_code"]
    elif user_response["user_info"]["country"]:
        self[CONF_REGION] = get_region_by_country_code(
            user_response["user_info"]["country"]
        )
        self[CONF_COUNTRY_CODE] = get_phone_code_by_country_code(
            user_response["user_info"]["country"]
        )
    else:
        self[CONF_REGION] = "EU"
        self[CONF_COUNTRY_CODE] = "44"

    self[CONF_TIME_ZONE] = user_response["user_info"]["timezone"]

    tuya_client = TuyaAPISession(
        username="eh-" + self[CONF_CLIENT_ID],
        region=self[CONF_REGION],
        timezone=self[CONF_TIME_ZONE],
        phone_code=self[CONF_COUNTRY_CODE],
    )

    items = device_response["devices"]
    self[CONF_VACS] = {}
    for item in items:
        if item["product"]["appliance"] == "Cleaning":
            try:
                device = tuya_client.get_device(item["id"])

                vac_details = {
                    CONF_ID: item["id"],
                    CONF_MODEL: item["product"]["product_code"],
                    CONF_NAME: item["alias_name"],
                    CONF_DESCRIPTION: item["name"],
                    CONF_MAC: item["wifi"]["mac"],
                    CONF_IP_ADDRESS: "",
                    CONF_AUTODISCOVERY: True,
                    CONF_ACCESS_TOKEN: device["localKey"],
                }
                self[CONF_VACS][item["id"]] = vac_details
            except Exception:
                _LOGGER.debug(
                    "Skipping vacuum {}: found on Eufy but not on Tuya. Eufy details:".format(
                        item["id"]
                    )
                )
                _LOGGER.debug(json.dumps(item, indent=2))

    # Ensure we're returning a valid Response object as declared in the return type
    if response is None:
        raise CannotConnect
    return response


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    await hass.async_add_executor_job(get_eufy_vacuums, data)
    return data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Eufy Robovac."""

    data: Optional[dict[str, Any]]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            # Return form for user input
            return self.async_show_form(
                step_id="user", data_schema=USER_SCHEMA
            )  # type: ignore[return-value]
        errors = {}
        try:
            unique_id = user_input[CONF_USERNAME]
            valid_data = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception: {}".format(e))
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            # return await self.async_step_repo(valid_data)
            # Create the config entry with validated data
            return self.async_create_entry(
                title=unique_id, data=valid_data
            )  # type: ignore[return-value]
        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )  # type: ignore[return-value]

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self.selected_vacuum = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.selected_vacuum = user_input["selected_vacuum"]
            return await self.async_step_edit()

        vacuums_config = self.config_entry.data[CONF_VACS]
        vacuum_list = {}
        for vacuum_id in vacuums_config:
            vacuum_list[vacuum_id] = vacuums_config[vacuum_id]["name"]

        devices_schema = vol.Schema(
            {vol.Required("selected_vacuum"): vol.In(vacuum_list)}
        )

        return self.async_show_form(
            step_id="init", data_schema=devices_schema, errors=errors
        )  # type: ignore[return-value]

    async def async_step_edit(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the edit step."""
        errors: dict[str, str] = {}

        vacuums = self.config_entry.data[CONF_VACS]

        if user_input is not None:
            updated_vacuums = deepcopy(vacuums)
            updated_vacuums[self.selected_vacuum][CONF_AUTODISCOVERY] = user_input[
                CONF_AUTODISCOVERY
            ]
            if user_input[CONF_IP_ADDRESS]:
                updated_vacuums[self.selected_vacuum][CONF_IP_ADDRESS] = user_input[
                    CONF_IP_ADDRESS
                ]

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={CONF_VACS: updated_vacuums},
            )

            return self.async_create_entry(title="", data={})  # type: ignore[return-value]

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_AUTODISCOVERY,
                    default=vacuums[self.selected_vacuum].get(CONF_AUTODISCOVERY, True),
                ): bool,
                vol.Optional(
                    CONF_IP_ADDRESS,
                    default=vacuums[self.selected_vacuum].get(CONF_IP_ADDRESS),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="edit", data_schema=options_schema, errors=errors
        )  # type: ignore[return-value]
