"""Tests for the RoboVac sensor component."""

import pytest
from unittest.mock import patch, MagicMock

from homeassistant.const import PERCENTAGE, CONF_ID
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from custom_components.robovac.sensor import RobovacBatterySensor
from custom_components.robovac.vacuums.base import TuyaCodes


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
    mock_vacuum_entity.tuyastatus = {str(TuyaCodes.BATTERY_LEVEL): 85}
    # Using side_effect to verify input argument if needed, or just return based on it

    def mock_get_dps_code(name):
        if name == TuyaCodes.BATTERY_LEVEL:
            return str(TuyaCodes.BATTERY_LEVEL)
        return ""
    mock_vacuum_entity.get_dps_code.side_effect = mock_get_dps_code

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
async def test_battery_sensor_get_dps_code_alias(mock_vacuum_data):
    """Test get_dps_code with BATTERY alias."""
    # We want to verify that in a real RoboVacEntity it works
    from custom_components.robovac.vacuum import RoboVacEntity
    mock_robovac = MagicMock()
    mock_robovac.getDpsCodes.return_value = {}
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        # Default should be 104 for BATTERY_LEVEL
        assert entity.get_dps_code("BATTERY") == "104"
        assert entity.get_dps_code(TuyaCodes.BATTERY_LEVEL) == "104"
        # Test model-specific
        mock_robovac.getDpsCodes.return_value = {"BATTERY_LEVEL": "163"}
        assert entity.get_dps_code("BATTERY") == "163"
        assert entity.get_dps_code(TuyaCodes.BATTERY_LEVEL) == "163"
