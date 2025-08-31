"""Tests for the RoboVac sensor component."""

import pytest
from unittest.mock import MagicMock

from homeassistant.const import PERCENTAGE, CONF_ID
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from custom_components.robovac.sensor import RobovacBatterySensor


@pytest.mark.asyncio
async def test_battery_sensor_init(mock_vacuum_data):
    """Test battery sensor initialization."""
    # Arrange & Act
    sensor = RobovacBatterySensor(mock_vacuum_data)

    # Assert
    assert sensor._attr_has_entity_name is True
    assert sensor._attr_device_class == SensorDeviceClass.BATTERY
    assert sensor._attr_native_unit_of_measurement == PERCENTAGE
    assert sensor._attr_should_poll is True
    assert sensor._attr_unique_id == f"{mock_vacuum_data[CONF_ID]}_battery"
    assert sensor._attr_name == "Battery"
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_battery_sensor_update_success():
    """Test battery sensor update with available vacuum entity."""
    # Arrange
    mock_data = {
        CONF_ID: "test_robovac_id",
        "name": "Test RoboVac",
    }

    sensor = RobovacBatterySensor(mock_data)

    # Create mock vacuum entity
    mock_vacuum_entity = MagicMock()
    mock_vacuum_entity.battery_level = 85

    # Create mock hass data structure
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_robovac_id": mock_vacuum_entity}}}

    # Set hass reference
    sensor.hass = mock_hass

    # Act
    await sensor.async_update()

    # Assert
    assert sensor._attr_native_value == 85
    assert sensor._attr_available is True


@pytest.mark.asyncio
async def test_battery_sensor_update_no_vacuum():
    """Test battery sensor update with no vacuum entity available."""
    # Arrange
    mock_data = {
        CONF_ID: "test_robovac_id",
        "name": "Test RoboVac",
    }

    sensor = RobovacBatterySensor(mock_data)

    # Create mock hass data structure with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacs": {}}}

    # Set hass reference
    sensor.hass = mock_hass

    # Act
    await sensor.async_update()

    # Assert
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_battery_sensor_update_exception():
    """Test battery sensor update handling exceptions."""
    # Arrange
    mock_data = {
        CONF_ID: "test_robovac_id",
        "name": "Test RoboVac",
    }

    sensor = RobovacBatterySensor(mock_data)

    # Create mock hass that raises an exception
    mock_hass = MagicMock()
    mock_hass.data = {
        "robovac": {"vacs": MagicMock(side_effect=Exception("Test exception"))}
    }

    # Set hass reference
    sensor.hass = mock_hass

    # Act
    await sensor.async_update()

    # Assert
    assert sensor._attr_available is False
