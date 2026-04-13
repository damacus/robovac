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
        # Clear the cache for the specific lookups
        entity._dps_codes_memo.pop("BATTERY_LEVEL", None)
        assert entity.get_dps_code("BATTERY") == "163"
        # Clear the cache again before calling with TuyaCodes.BATTERY_LEVEL
        # because the internal lookup name is "BATTERY_LEVEL" again.
        entity._dps_codes_memo.pop("BATTERY_LEVEL", None)
        assert entity.get_dps_code(TuyaCodes.BATTERY_LEVEL) == "163"


def test_sensor_classes_can_be_instantiated(mock_vacuum_data):
    """Test that all sensor classes can be instantiated."""
    from custom_components.robovac.sensor import (
        RobovacBatterySensor,
        RobovacErrorSensor,
        RobovacNotificationSensor,
        RobovacConsumableSensor,
        RobovacCleanTypeSensor,
        RobovacLastCleanRecordSensor,
        RobovacWorkStatusV2Sensor,
        RobovacLastCleanAreaSensor,
        RobovacLastCleanDurationSensor,
        RobovacFirmwareSensor,
        RobovacWifiSignalSensor,
        RobovacWifiSsidSensor,
        RobovacWifiFrequencySensor,
        RobovacMultiMapSensor,
        RobovacCustomCleanModeSensor,
        RobovacMapValidSensor,
        RobovacChildrenLockSensor,
    )

    # Test battery sensor
    battery_sensor = RobovacBatterySensor(mock_vacuum_data)
    assert battery_sensor is not None
    assert battery_sensor.robovac_id == mock_vacuum_data[CONF_ID]

    # Test error sensor (DPS 177)
    error_sensor = RobovacErrorSensor(mock_vacuum_data, "177")
    assert error_sensor is not None

    # Test notification sensor (DPS 178)
    notif_sensor = RobovacNotificationSensor(mock_vacuum_data, "178")
    assert notif_sensor is not None

    # Test consumable sensor (DPS 168)
    cons_sensor = RobovacConsumableSensor(
        mock_vacuum_data, "168", "side_brush", "Side Brush", "mdi:brush"
    )
    assert cons_sensor is not None

    # Test clean type sensor (DPS 154)
    clean_sensor = RobovacCleanTypeSensor(mock_vacuum_data, "154")
    assert clean_sensor is not None

    # Test clean record sensor (DPS 164)
    record_sensor = RobovacLastCleanRecordSensor(mock_vacuum_data, "164")
    assert record_sensor is not None

    # Test work status v2 sensor (DPS 173)
    status_sensor = RobovacWorkStatusV2Sensor(mock_vacuum_data, "173")
    assert status_sensor is not None

    # Test area sensor (DPS 179)
    area_sensor = RobovacLastCleanAreaSensor(mock_vacuum_data, "179")
    assert area_sensor is not None

    # Test duration sensor (DPS 179)
    duration_sensor = RobovacLastCleanDurationSensor(mock_vacuum_data, "179")
    assert duration_sensor is not None

    # Test firmware sensor (DPS 169)
    firmware_sensor = RobovacFirmwareSensor(mock_vacuum_data, "169")
    assert firmware_sensor is not None

    # Test WiFi sensors (DPS 176)
    wifi_signal_sensor = RobovacWifiSignalSensor(mock_vacuum_data, "176")
    assert wifi_signal_sensor is not None

    wifi_ssid_sensor = RobovacWifiSsidSensor(mock_vacuum_data, "176")
    assert wifi_ssid_sensor is not None

    wifi_freq_sensor = RobovacWifiFrequencySensor(mock_vacuum_data, "176")
    assert wifi_freq_sensor is not None

    # Test multimap sensor
    multimap_sensor = RobovacMultiMapSensor(mock_vacuum_data, "176")
    assert multimap_sensor is not None

    # Test custom clean mode sensor
    clean_mode_sensor = RobovacCustomCleanModeSensor(mock_vacuum_data, "176")
    assert clean_mode_sensor is not None

    # Test map valid sensor
    map_valid_sensor = RobovacMapValidSensor(mock_vacuum_data, "176")
    assert map_valid_sensor is not None

    # Test children lock sensor
    lock_sensor = RobovacChildrenLockSensor(mock_vacuum_data, "176")
    assert lock_sensor is not None


@pytest.mark.asyncio
async def test_error_sensor_init(mock_vacuum_data):
    """Test error sensor initialization."""
    from custom_components.robovac.sensor import RobovacErrorSensor

    sensor = RobovacErrorSensor(mock_vacuum_data, "177")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]
    assert sensor._attr_has_entity_name is True


@pytest.mark.asyncio
async def test_notification_sensor_init(mock_vacuum_data):
    """Test notification sensor initialization."""
    from custom_components.robovac.sensor import RobovacNotificationSensor

    sensor = RobovacNotificationSensor(mock_vacuum_data, "178")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_consumable_sensor_init(mock_vacuum_data):
    """Test consumable sensor initialization."""
    from custom_components.robovac.sensor import RobovacConsumableSensor

    sensor = RobovacConsumableSensor(mock_vacuum_data, "168", "side_brush", "Side Brush", "mdi:brush")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]
    assert sensor._attr_name == "Side Brush"
    assert sensor._attr_icon == "mdi:brush"


@pytest.mark.asyncio
async def test_clean_type_sensor_init(mock_vacuum_data):
    """Test clean type sensor initialization."""
    from custom_components.robovac.sensor import RobovacCleanTypeSensor

    sensor = RobovacCleanTypeSensor(mock_vacuum_data, "154")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_clean_record_sensor_init(mock_vacuum_data):
    """Test clean record sensor initialization."""
    from custom_components.robovac.sensor import RobovacLastCleanRecordSensor

    sensor = RobovacLastCleanRecordSensor(mock_vacuum_data, "164")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_work_status_v2_sensor_init(mock_vacuum_data):
    """Test work status v2 sensor initialization."""
    from custom_components.robovac.sensor import RobovacWorkStatusV2Sensor

    sensor = RobovacWorkStatusV2Sensor(mock_vacuum_data, "173")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_last_clean_area_sensor_init(mock_vacuum_data):
    """Test last clean area sensor initialization."""
    from custom_components.robovac.sensor import RobovacLastCleanAreaSensor

    sensor = RobovacLastCleanAreaSensor(mock_vacuum_data, "179")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_last_clean_duration_sensor_init(mock_vacuum_data):
    """Test last clean duration sensor initialization."""
    from custom_components.robovac.sensor import RobovacLastCleanDurationSensor

    sensor = RobovacLastCleanDurationSensor(mock_vacuum_data, "179")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_firmware_sensor_init(mock_vacuum_data):
    """Test firmware sensor initialization."""
    from custom_components.robovac.sensor import RobovacFirmwareSensor

    sensor = RobovacFirmwareSensor(mock_vacuum_data, "169")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_wifi_signal_sensor_init(mock_vacuum_data):
    """Test WiFi signal sensor initialization."""
    from custom_components.robovac.sensor import RobovacWifiSignalSensor

    sensor = RobovacWifiSignalSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_wifi_ssid_sensor_init(mock_vacuum_data):
    """Test WiFi SSID sensor initialization."""
    from custom_components.robovac.sensor import RobovacWifiSsidSensor

    sensor = RobovacWifiSsidSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_wifi_frequency_sensor_init(mock_vacuum_data):
    """Test WiFi frequency sensor initialization."""
    from custom_components.robovac.sensor import RobovacWifiFrequencySensor

    sensor = RobovacWifiFrequencySensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_multimap_sensor_init(mock_vacuum_data):
    """Test multimap sensor initialization."""
    from custom_components.robovac.sensor import RobovacMultiMapSensor

    sensor = RobovacMultiMapSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_custom_clean_mode_sensor_init(mock_vacuum_data):
    """Test custom clean mode sensor initialization."""
    from custom_components.robovac.sensor import RobovacCustomCleanModeSensor

    sensor = RobovacCustomCleanModeSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_map_valid_sensor_init(mock_vacuum_data):
    """Test map valid sensor initialization."""
    from custom_components.robovac.sensor import RobovacMapValidSensor

    sensor = RobovacMapValidSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_children_lock_sensor_init(mock_vacuum_data):
    """Test children lock sensor initialization."""
    from custom_components.robovac.sensor import RobovacChildrenLockSensor

    sensor = RobovacChildrenLockSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_error_sensor_update_no_vacuum():
    """Test error sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacErrorSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_error_sensor_update_no_tuyastatus():
    """Test error sensor update when tuyastatus not available."""
    from custom_components.robovac.sensor import RobovacErrorSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # Mock vacuum entity without tuyastatus
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = None
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    # First update with no data
    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_error_sensor_update_no_dps_code():
    """Test error sensor update when DPS code not in tuyastatus."""
    from custom_components.robovac.sensor import RobovacErrorSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # Mock vacuum entity with empty tuyastatus
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_notification_sensor_update_no_vacuum():
    """Test notification sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacNotificationSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacNotificationSensor(mock_data, "178")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_consumable_sensor_update_no_vacuum():
    """Test consumable sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacConsumableSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacConsumableSensor(mock_data, "168", "side_brush", "Side Brush", "mdi:brush")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_clean_type_sensor_update_no_vacuum():
    """Test clean type sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacCleanTypeSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacCleanTypeSensor(mock_data, "154")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_wifi_signal_sensor_update_no_vacuum():
    """Test WiFi signal sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacWifiSignalSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacWifiSignalSensor(mock_data, "176")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_last_clean_area_sensor_update_no_vacuum():
    """Test last clean area sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacLastCleanAreaSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanAreaSensor(mock_data, "179")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_firmware_sensor_update_no_vacuum():
    """Test firmware sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacFirmwareSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacFirmwareSensor(mock_data, "169")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_work_status_v2_sensor_update_no_vacuum():
    """Test work status v2 sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacWorkStatusV2Sensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacWorkStatusV2Sensor(mock_data, "173")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_last_clean_record_sensor_update_no_vacuum():
    """Test last clean record sensor update when vacuum entity not found."""
    from custom_components.robovac.sensor import RobovacLastCleanRecordSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanRecordSensor(mock_data, "164")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_error_sensor_update_exception_handling():
    """Test error sensor handles exceptions gracefully."""
    from custom_components.robovac.sensor import RobovacErrorSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # Mock hass that raises exception
    mock_hass = MagicMock()
    mock_hass.data = MagicMock(side_effect=Exception("Test exception"))
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_notification_sensor_update_exception_handling():
    """Test notification sensor handles exceptions gracefully."""
    from custom_components.robovac.sensor import RobovacNotificationSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacNotificationSensor(mock_data, "178")

    # Mock hass that raises exception
    mock_hass = MagicMock()
    mock_hass.data = MagicMock(side_effect=Exception("Test exception"))
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_consumable_sensor_update_exception_handling():
    """Test consumable sensor handles exceptions gracefully."""
    from custom_components.robovac.sensor import RobovacConsumableSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacConsumableSensor(mock_data, "168", "side_brush", "Side Brush", "mdi:brush")

    # Mock hass that raises exception
    mock_hass = MagicMock()
    mock_hass.data = MagicMock(side_effect=Exception("Test exception"))
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_error_sensor_update_successful():
    """Test error sensor update with successful decode."""
    from custom_components.robovac.sensor import RobovacErrorSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # Mock vacuum entity with error data
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"177": "AA=="}  # Some error code
    mock_vacuum.vacuum.getRoboVacHumanReadableValue.return_value = "no_error"

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is True
    assert sensor._attr_native_value is None  # no_error returns None


@pytest.mark.asyncio
async def test_notification_sensor_update_successful():
    """Test notification sensor update with successful decode."""
    from custom_components.robovac.sensor import RobovacNotificationSensor

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacNotificationSensor(mock_data, "178")

    # Mock vacuum entity with notification data
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"178": "AA=="}

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch("custom_components.robovac.sensor.decode_error_code", return_value="no_error"):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value is None  # no_error returns None
