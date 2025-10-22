"""Tests for battery sensor separation and data handling.

This test verifies the fix for issue reported in:
https://github.com/damacus/robovac/issues/29#issuecomment-3431949831

Verifies that battery level is handled by separate sensor entity,
not by the vacuum entity's deprecated _attr_battery_level.
"""

import pytest
from unittest.mock import patch, MagicMock
from homeassistant.const import (
    CONF_ID,
    CONF_NAME,
    CONF_MODEL,
    CONF_IP_ADDRESS,
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
    CONF_MAC,
)

from custom_components.robovac.vacuum import RoboVacEntity


@pytest.fixture
def mock_vacuum_config() -> dict:
    """Create a mock vacuum configuration."""
    return {
        CONF_ID: "test_device_id",
        CONF_NAME: "Test Vacuum",
        CONF_MODEL: "T2277",
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_key",
        CONF_DESCRIPTION: "Test Model Description",
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
    }


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    return hass


@pytest.fixture
def vacuum_entity(mock_vacuum_config, mock_hass):
    """Create a RoboVacEntity instance for testing."""
    with patch("custom_components.robovac.vacuum.RoboVac"):
        entity = RoboVacEntity(mock_vacuum_config)
        entity.hass = mock_hass
        return entity


def test_update_entity_values_with_valid_data(vacuum_entity):
    """Test that entity updates correctly with valid data."""
    # Provide valid tuyastatus data
    vacuum_entity.tuyastatus = {
        "104": 85,  # Battery level
        "15": "Sleeping",  # Status
        "102": "Standard",  # Fan speed
    }

    # Call update_entity_values - should complete without errors
    vacuum_entity.update_entity_values()

    # Verify entity processed the data (tuyastatus gets replaced by vacuum._dps)
    assert vacuum_entity.tuyastatus is not None


def test_battery_sensor_exists_separately(vacuum_entity):
    """Test that battery level is handled by separate sensor, not vacuum entity."""
    # Battery level attribute should not exist on vacuum entity
    assert not hasattr(vacuum_entity, "_attr_battery_level") or vacuum_entity._attr_battery_level is None

    # Battery data should still be available in tuyastatus for sensor to read
    vacuum_entity.tuyastatus = {"104": 85}
    vacuum_entity.update_entity_values()

    # Vacuum entity should not have battery_level attribute set
    assert not hasattr(vacuum_entity, "_attr_battery_level") or vacuum_entity._attr_battery_level is None
