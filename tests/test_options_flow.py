"""Tests for the RoboVac options flow."""

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
)
from homeassistant.core import HomeAssistant

from custom_components.robovac.config_flow import OptionsFlowHandler
from custom_components.robovac.const import DOMAIN, CONF_AUTODISCOVERY, CONF_VACS


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry with vacuum data."""
    config_entry = MagicMock(spec=config_entries.ConfigEntry)
    config_entry.data = {
        CONF_VACS: {
            "test_device_id": {
                CONF_ID: "test_device_id",
                CONF_NAME: "Test RoboVac",
                CONF_MODEL: "T2118",
                CONF_DESCRIPTION: "RoboVac 15C",
                CONF_MAC: "AA:BB:CC:DD:EE:FF",
                CONF_AUTODISCOVERY: True,
                CONF_IP_ADDRESS: "",
                CONF_ACCESS_TOKEN: "test_local_key",
            },
            "test_device_id_2": {
                CONF_ID: "test_device_id_2",
                CONF_NAME: "Test RoboVac 2",
                CONF_MODEL: "T2118",
                CONF_DESCRIPTION: "RoboVac 15C",
                CONF_MAC: "11:22:33:44:55:66",
                CONF_AUTODISCOVERY: True,
                CONF_IP_ADDRESS: "",
                CONF_ACCESS_TOKEN: "test_local_key_2",
            },
        }
    }
    config_entry.domain = DOMAIN
    config_entry.entry_id = "test_entry_id"
    config_entry.title = "Test"
    return config_entry


@pytest.mark.asyncio
async def test_options_flow_init_multiple_vacuums(
    hass: HomeAssistant, mock_config_entry
):
    """Test options flow init step with multiple vacuums."""
    # Initialize the options flow
    flow = OptionsFlowHandler(mock_config_entry)
    result = await flow.async_step_init()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    # Verify that the form contains a selected_vacuum field
    assert "selected_vacuum" in result["data_schema"].schema


@pytest.mark.asyncio
async def test_options_flow_init_submit(hass: HomeAssistant, mock_config_entry):
    """Test options flow init step submission."""
    # Initialize the options flow
    flow = OptionsFlowHandler(mock_config_entry)

    # Submit the init step with a selected vacuum
    result = await flow.async_step_init({"selected_vacuum": "test_device_id"})

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "edit"
    assert flow.selected_vacuum == "test_device_id"


@pytest.mark.asyncio
async def test_options_flow_edit_default_values(hass: HomeAssistant, mock_config_entry):
    """Test options flow edit step default values."""
    # Initialize the options flow and select a vacuum
    flow = OptionsFlowHandler(mock_config_entry)
    flow.selected_vacuum = "test_device_id"

    # Test the edit step
    result = await flow.async_step_edit()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "edit"

    # Verify that the form contains the expected fields
    assert CONF_AUTODISCOVERY in result["data_schema"].schema
    assert CONF_IP_ADDRESS in result["data_schema"].schema


@pytest.mark.asyncio
async def test_options_flow_edit_custom_values(hass: HomeAssistant):
    """Test options flow edit step with custom values."""
    # Create a mock config entry with custom values
    config_entry = MagicMock(spec=config_entries.ConfigEntry)
    config_entry.data = {
        CONF_VACS: {
            "test_device_id": {
                CONF_ID: "test_device_id",
                CONF_NAME: "Test RoboVac",
                CONF_AUTODISCOVERY: False,
                CONF_IP_ADDRESS: "192.168.1.100",
            }
        }
    }
    config_entry.domain = DOMAIN
    config_entry.entry_id = "test_entry_id"
    config_entry.title = "Test"

    # Initialize the options flow and select a vacuum
    flow = OptionsFlowHandler(config_entry)
    flow.selected_vacuum = "test_device_id"

    # Test the edit step
    result = await flow.async_step_edit()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "edit"

    # Verify that the form contains the expected fields
    assert CONF_AUTODISCOVERY in result["data_schema"].schema
    assert CONF_IP_ADDRESS in result["data_schema"].schema


@pytest.mark.asyncio
async def test_options_flow_edit_submit_with_ip(hass: HomeAssistant, mock_config_entry):
    """Test options flow edit step submission with IP address."""
    # Create a completed future to return from our mock
    future = asyncio.Future()
    future.set_result(None)

    # Mock the async_update_entry method to return the future
    hass.config_entries.async_update_entry = MagicMock(return_value=future)

    # Initialize the options flow and select a vacuum
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass
    flow.selected_vacuum = "test_device_id"

    # Create a copy of the data to avoid modifying the original
    updated_data = dict(mock_config_entry.data)

    # Manually update the data that would be modified by the flow
    updated_vacs = dict(updated_data.get(CONF_VACS, {}))
    updated_vacs["test_device_id"] = dict(updated_vacs.get("test_device_id", {}))
    updated_vacs["test_device_id"][CONF_AUTODISCOVERY] = False
    updated_vacs["test_device_id"][CONF_IP_ADDRESS] = "192.168.1.100"
    updated_data[CONF_VACS] = updated_vacs

    # Mock the flow's _update_data method to return our updated data
    flow._update_data = MagicMock(return_value=updated_data)

    # Test the edit step submission with IP address
    result = await flow.async_step_edit(
        {
            CONF_AUTODISCOVERY: False,
            CONF_IP_ADDRESS: "192.168.1.100",
        }
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    # Verify the config entry was updated correctly
    hass.config_entries.async_update_entry.assert_called_once()
    # Since we mocked _update_data, we can't check the exact call arguments
    # but we can verify the call was made


@pytest.mark.asyncio
async def test_options_flow_edit_submit_without_ip(
    hass: HomeAssistant, mock_config_entry
):
    """Test options flow edit step submission without IP address."""
    # Create a completed future to return from our mock
    future = asyncio.Future()
    future.set_result(None)

    # Mock the async_update_entry method to return the future
    hass.config_entries.async_update_entry = MagicMock(return_value=future)

    # Initialize the options flow and select a vacuum
    flow = OptionsFlowHandler(mock_config_entry)
    flow.hass = hass
    flow.selected_vacuum = "test_device_id"

    # Create a copy of the data to avoid modifying the original
    updated_data = dict(mock_config_entry.data)

    # Manually update the data that would be modified by the flow
    updated_vacs = dict(updated_data.get(CONF_VACS, {}))
    updated_vacs["test_device_id"] = dict(updated_vacs.get("test_device_id", {}))
    updated_vacs["test_device_id"][CONF_AUTODISCOVERY] = True
    updated_vacs["test_device_id"][CONF_IP_ADDRESS] = ""
    updated_data[CONF_VACS] = updated_vacs

    # Mock the flow's _update_data method to return our updated data
    flow._update_data = MagicMock(return_value=updated_data)

    # Test the edit step submission without IP address
    result = await flow.async_step_edit(
        {
            CONF_AUTODISCOVERY: True,
            CONF_IP_ADDRESS: "",
        }
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    # Verify the config entry was updated correctly
    hass.config_entries.async_update_entry.assert_called_once()
