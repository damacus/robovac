"""Tests for the RoboVac sensor component."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_ID, PERCENTAGE
from homeassistant.components.sensor import SensorDeviceClass
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.robovac.const import CONF_VACS, DOMAIN
from custom_components.robovac.sensor import RobovacBatterySensor, async_setup_entry


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


@pytest.mark.asyncio
async def test_async_setup_entry_triggers_initial_update(hass, mock_vacuum_data):
    """Test async_setup_entry triggers an initial update for the battery sensor."""
    # Arrange
    mock_vacuum_entity = MagicMock()
    mock_vacuum_entity.battery_level = 90
    hass.data = {DOMAIN: {CONF_VACS: {mock_vacuum_data[CONF_ID]: mock_vacuum_entity}}}

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_VACS: {mock_vacuum_data[CONF_ID]: mock_vacuum_data}},
    )

    added_entities = []
    update_flag = {}
    mock_update_holder = {}

    def _async_add_entities(entities, update_before_add=False):
        update_flag["value"] = update_before_add
        for entity in entities:
            entity.hass = hass
            if update_before_add:
                entity.async_update = AsyncMock(wraps=entity.async_update)
                mock_update_holder["mock"] = entity.async_update
                hass.loop.create_task(entity.async_update())
        added_entities.extend(entities)

    await async_setup_entry(hass, config_entry, _async_add_entities)
    await hass.async_block_till_done()

    mock_update = mock_update_holder["mock"]
    assert mock_update.await_count == 1

    assert update_flag["value"] is True
    sensor = added_entities[0]
    assert sensor.native_value == 90
