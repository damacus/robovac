"""Tests for the RoboVac config flow."""

import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_ACCESS_TOKEN,
    CONF_NAME,
    CONF_ID,
    CONF_MODEL,
    CONF_IP_ADDRESS,
    CONF_DESCRIPTION,
    CONF_MAC,
    CONF_CLIENT_ID,
    CONF_REGION,
    CONF_TIME_ZONE,
    CONF_COUNTRY_CODE,
)
from homeassistant.core import HomeAssistant

from custom_components.robovac.config_flow import (
    OptionsFlowHandler,
)
from custom_components.robovac.const import DOMAIN, CONF_AUTODISCOVERY, CONF_VACS


@pytest.fixture
def mock_eufy_response():
    """Create a mock response from the Eufy API."""
    user_info_response = MagicMock()
    user_info_response.status_code = 200
    user_info_response.json.return_value = {
        "res_code": 1,
        "user_info": {
            "id": "test_client_id",
            "request_host": "test_host",
            "phone_code": "44",
            "country": "GB",
            "timezone": "Europe/London",
        },
        "access_token": "test_access_token",
    }

    device_info_response = MagicMock()
    device_info_response.json.return_value = {
        "devices": [
            {
                "id": "test_device_id",
                "product": {
                    "appliance": "Cleaning",
                    "product_code": "T2118",
                },
                "alias_name": "Test RoboVac",
                "name": "RoboVac 15C",
                "wifi": {"mac": "AA:BB:CC:DD:EE:FF"},
            }
        ]
    }

    settings_response = MagicMock()
    settings_response.json.return_value = {
        "setting": {
            "home_setting": {
                "tuya_home": {
                    "tuya_region_code": "EU",
                }
            }
        }
    }

    return {
        "user_info": user_info_response,
        "device_info": device_info_response,
        "settings": settings_response,
    }


@pytest.fixture
def mock_tuya_device():
    """Create a mock Tuya device response."""
    return {"localKey": "test_local_key"}


@pytest.mark.asyncio
async def test_user_form(hass: HomeAssistant):
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_user_form_cannot_connect(hass: HomeAssistant, mock_eufy_response):
    """Test we handle cannot connect error."""
    # Mock the EufyLogon.get_user_info to return a 400 status code
    mock_eufy_response["user_info"].status_code = 400

    with patch(
        "custom_components.robovac.config_flow.EufyLogon",
        return_value=MagicMock(
            get_user_info=MagicMock(return_value=mock_eufy_response["user_info"])
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_user_form_invalid_auth(hass: HomeAssistant, mock_eufy_response):
    """Test we handle invalid auth error."""
    # Mock the EufyLogon.get_user_info to return a 200 status code but res_code != 1
    mock_eufy_response["user_info"].json.return_value["res_code"] = 0

    with patch(
        "custom_components.robovac.config_flow.EufyLogon",
        return_value=MagicMock(
            get_user_info=MagicMock(return_value=mock_eufy_response["user_info"])
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_user_form_unexpected_exception(hass: HomeAssistant):
    """Test we handle unexpected exception."""
    with patch(
        "custom_components.robovac.config_flow.EufyLogon",
        side_effect=Exception("Unexpected error"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unknown"}


@pytest.mark.asyncio
async def test_user_form_success(
    hass: HomeAssistant, mock_eufy_response, mock_tuya_device
):
    """Test successful form submission."""
    with (
        patch(
            "custom_components.robovac.config_flow.EufyLogon",
            return_value=MagicMock(
                get_user_info=MagicMock(return_value=mock_eufy_response["user_info"]),
                get_device_info=MagicMock(
                    return_value=mock_eufy_response["device_info"]
                ),
                get_user_settings=MagicMock(
                    return_value=mock_eufy_response["settings"]
                ),
            ),
        ),
        patch(
            "custom_components.robovac.config_flow.TuyaAPISession",
            return_value=MagicMock(get_device=MagicMock(return_value=mock_tuya_device)),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username"
    assert result["data"][CONF_USERNAME] == "test-username"
    assert result["data"][CONF_PASSWORD] == "test-password"
    assert result["data"][CONF_CLIENT_ID] == "test_client_id"
    assert result["data"][CONF_REGION] == "EU"
    assert result["data"][CONF_COUNTRY_CODE] == "44"
    assert result["data"][CONF_TIME_ZONE] == "Europe/London"
    assert CONF_VACS in result["data"]
    assert "test_device_id" in result["data"][CONF_VACS]
    assert result["data"][CONF_VACS]["test_device_id"][CONF_ID] == "test_device_id"
    assert result["data"][CONF_VACS]["test_device_id"][CONF_MODEL] == "T2118"
    assert result["data"][CONF_VACS]["test_device_id"][CONF_NAME] == "Test RoboVac"
    assert (
        result["data"][CONF_VACS]["test_device_id"][CONF_DESCRIPTION] == "RoboVac 15C"
    )
    assert result["data"][CONF_VACS]["test_device_id"][CONF_MAC] == "AA:BB:CC:DD:EE:FF"
    assert result["data"][CONF_VACS]["test_device_id"][CONF_IP_ADDRESS] == ""
    assert result["data"][CONF_VACS]["test_device_id"][CONF_AUTODISCOVERY] is True
    assert (
        result["data"][CONF_VACS]["test_device_id"][CONF_ACCESS_TOKEN]
        == "test_local_key"
    )


@pytest.mark.asyncio
async def test_options_flow_init(hass: HomeAssistant):
    """Test options flow init step."""
    # Create a mock config entry using MagicMock instead of actual ConfigEntry
    config_entry = MagicMock(spec=config_entries.ConfigEntry)
    config_entry.data = {
        CONF_VACS: {
            "test_device_id": {
                CONF_ID: "test_device_id",
                CONF_NAME: "Test RoboVac",
                CONF_AUTODISCOVERY: True,
                CONF_IP_ADDRESS: "",
            }
        }
    }
    config_entry.entry_id = "test_entry_id"

    # Initialize the options flow
    flow = OptionsFlowHandler(config_entry)
    result = await flow.async_step_init()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"
    assert "selected_vacuum" in result["data_schema"].schema


@pytest.mark.asyncio
async def test_options_flow_edit(hass: HomeAssistant):
    """Test options flow edit step."""
    # Create a mock config entry using MagicMock instead of actual ConfigEntry
    config_entry = MagicMock(spec=config_entries.ConfigEntry)
    config_entry.data = {
        CONF_VACS: {
            "test_device_id": {
                CONF_ID: "test_device_id",
                CONF_NAME: "Test RoboVac",
                CONF_AUTODISCOVERY: True,
                CONF_IP_ADDRESS: "",
            }
        }
    }
    config_entry.entry_id = "test_entry_id"

    # Initialize the options flow and select a vacuum
    flow = OptionsFlowHandler(config_entry)
    flow.hass = hass
    flow.selected_vacuum = "test_device_id"

    # Test the edit step
    result = await flow.async_step_edit()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "edit"
    assert CONF_AUTODISCOVERY in result["data_schema"].schema
    assert CONF_IP_ADDRESS in result["data_schema"].schema


@pytest.mark.asyncio
async def test_options_flow_edit_submit(hass: HomeAssistant):
    """Test options flow edit step submission."""
    # Create a mock config entry using MagicMock instead of actual ConfigEntry
    config_entry = MagicMock(spec=config_entries.ConfigEntry)
    config_entry.data = {
        CONF_VACS: {
            "test_device_id": {
                CONF_ID: "test_device_id",
                CONF_NAME: "Test RoboVac",
                CONF_AUTODISCOVERY: True,
                CONF_IP_ADDRESS: "",
            }
        }
    }
    config_entry.entry_id = "test_entry_id"

    # Create a completed future to return from our mock
    future = asyncio.Future()
    future.set_result(None)

    # Mock the async_update_entry method to return the future
    hass.config_entries.async_update_entry = MagicMock(return_value=future)

    # Initialize the options flow and select a vacuum
    flow = OptionsFlowHandler(config_entry)
    flow.hass = hass
    flow.selected_vacuum = "test_device_id"

    # Create a copy of the data to avoid modifying the original
    updated_data = dict(config_entry.data)

    # Manually update the data that would be modified by the flow
    updated_vacs = dict(updated_data.get(CONF_VACS, {}))
    updated_vacs["test_device_id"] = dict(updated_vacs.get("test_device_id", {}))
    updated_vacs["test_device_id"][CONF_AUTODISCOVERY] = False
    updated_vacs["test_device_id"][CONF_IP_ADDRESS] = "192.168.1.100"
    updated_data[CONF_VACS] = updated_vacs

    # Mock the flow's _update_data method to return our updated data
    flow._update_data = MagicMock(return_value=updated_data)

    # Test the edit step submission
    result = await flow.async_step_edit(
        {
            CONF_AUTODISCOVERY: False,
            CONF_IP_ADDRESS: "192.168.1.100",
        }
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"] == {}

    # Verify the config entry was updated correctly
    hass.config_entries.async_update_entry.assert_called_once()
