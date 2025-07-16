"""Tests for L60 DPS codes handling."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, call, AsyncMock

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuum import RoboVacEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_ID,
    CONF_MAC,
    CONF_MODEL,
    CONF_IP_ADDRESS,
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
)


@pytest.mark.asyncio
async def test_l60_start_command_uses_correct_dps_value():
    """Test that L60 model sends the correct base64 encoded value for DPS 152 when starting."""
    # Setup mock vacuum data for L60 model
    mock_vacuum_data = {
        CONF_NAME: "Test L60",
        CONF_ID: "test_id",
        CONF_MAC: "test_mac",
        CONF_MODEL: "T2267",  # L60 model code
        CONF_IP_ADDRESS: "192.168.1.1",
        CONF_ACCESS_TOKEN: "test_token",
        CONF_DESCRIPTION: "Test L60 Vacuum",
    }

    # Mock the RoboVac instance with AsyncMock to make it awaitable
    mock_robovac = MagicMock()
    mock_robovac._dps = {}
    mock_robovac.getDpsCodes.return_value = {
        "MODE": "152",
        "STATUS": "153",
        "BATTERY_LEVEL": "163",
        "ERROR_CODE": "177"
    }
    # Mock the getRoboVacCommandValue to return the correct base64 value
    mock_robovac.getRoboVacCommandValue.return_value = "BBoCCAE="
    # Make async_set an AsyncMock so it can be awaited
    mock_robovac.async_set = AsyncMock()

    # Initialize the vacuum entity with mocked RoboVac
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Call async_start method
        await entity.async_start()

        # Verify that async_set was called with the correct base64 encoded value
        # The L60 requires "BBoCCAE=" for DPS 152 instead of "auto"
        mock_robovac.async_set.assert_called_once_with({"152": "BBoCCAE="})
