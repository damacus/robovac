"""Tests for the RoboVac sensor component."""

from typing import Any
import pytest
from unittest.mock import patch, MagicMock

from homeassistant.const import PERCENTAGE, CONF_ID
from homeassistant.components.sensor import SensorDeviceClass

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
from custom_components.robovac.vacuums.base import TuyaCodes

# ============================================================================
# Fixtures for common test scenarios
# ============================================================================


@pytest.fixture
def mock_hass_with_valid_vacuum() -> Any:
    """Mock hass with a fully functional vacuum entity."""
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {
        str(TuyaCodes.BATTERY_LEVEL): 85,
        "177": "base64_error_data",
        "178": "base64_notification_data",
        "168": "base64_consumable_data",
        "154": "base64_clean_param_data",
        "176": "base64_wifi_data",
        "179": "base64_analysis_data",
    }
    mock_vacuum.vacuum = MagicMock()
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    return mock_hass


@pytest.fixture
def mock_hass_empty() -> Any:
    """Mock hass with no vacuums."""
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    return mock_hass


@pytest.fixture
def mock_hass_no_tuyastatus() -> Any:
    """Mock hass with vacuum but no tuyastatus."""
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    return mock_hass


@pytest.mark.asyncio
async def test_battery_sensor_init(mock_vacuum_data: Any) -> None:
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
async def test_battery_sensor_update_success(mock_vacuum_data: Any) -> None:
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

    def mock_get_dps_code(name: Any) -> str:
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
async def test_battery_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
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
async def test_battery_sensor_update_exception(mock_vacuum_data: Any) -> None:
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
async def test_battery_sensor_get_dps_code_alias(mock_vacuum_data: Any) -> None:
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


def test_sensor_classes_can_be_instantiated(mock_vacuum_data: Any) -> None:
    """Test that all sensor classes can be instantiated."""
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
async def test_error_sensor_init(mock_vacuum_data: Any) -> None:
    """Test error sensor initialization."""

    sensor = RobovacErrorSensor(mock_vacuum_data, "177")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]
    assert sensor._attr_has_entity_name is True


@pytest.mark.asyncio
async def test_notification_sensor_init(mock_vacuum_data: Any) -> None:
    """Test notification sensor initialization."""

    sensor = RobovacNotificationSensor(mock_vacuum_data, "178")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_consumable_sensor_init(mock_vacuum_data: Any) -> None:
    """Test consumable sensor initialization."""

    sensor = RobovacConsumableSensor(
        mock_vacuum_data, "168", "side_brush", "Side Brush", "mdi:brush"
    )
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]
    assert sensor._attr_name == "Side Brush"
    assert sensor._attr_icon == "mdi:brush"


@pytest.mark.asyncio
async def test_clean_type_sensor_init(mock_vacuum_data: Any) -> None:
    """Test clean type sensor initialization."""

    sensor = RobovacCleanTypeSensor(mock_vacuum_data, "154")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_clean_record_sensor_init(mock_vacuum_data: Any) -> None:
    """Test clean record sensor initialization."""

    sensor = RobovacLastCleanRecordSensor(mock_vacuum_data, "164")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_work_status_v2_sensor_init(mock_vacuum_data: Any) -> None:
    """Test work status v2 sensor initialization."""

    sensor = RobovacWorkStatusV2Sensor(mock_vacuum_data, "173")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_last_clean_area_sensor_init(mock_vacuum_data: Any) -> None:
    """Test last clean area sensor initialization."""

    sensor = RobovacLastCleanAreaSensor(mock_vacuum_data, "179")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_last_clean_duration_sensor_init(mock_vacuum_data: Any) -> None:
    """Test last clean duration sensor initialization."""

    sensor = RobovacLastCleanDurationSensor(mock_vacuum_data, "179")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_firmware_sensor_init(mock_vacuum_data: Any) -> None:
    """Test firmware sensor initialization."""

    sensor = RobovacFirmwareSensor(mock_vacuum_data, "169")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_wifi_signal_sensor_init(mock_vacuum_data: Any) -> None:
    """Test WiFi signal sensor initialization."""

    sensor = RobovacWifiSignalSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_wifi_ssid_sensor_init(mock_vacuum_data: Any) -> None:
    """Test WiFi SSID sensor initialization."""

    sensor = RobovacWifiSsidSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_wifi_frequency_sensor_init(mock_vacuum_data: Any) -> None:
    """Test WiFi frequency sensor initialization."""

    sensor = RobovacWifiFrequencySensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_multimap_sensor_init(mock_vacuum_data: Any) -> None:
    """Test multimap sensor initialization."""

    sensor = RobovacMultiMapSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_custom_clean_mode_sensor_init(mock_vacuum_data: Any) -> None:
    """Test custom clean mode sensor initialization."""

    sensor = RobovacCustomCleanModeSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_map_valid_sensor_init(mock_vacuum_data: Any) -> None:
    """Test map valid sensor initialization."""

    sensor = RobovacMapValidSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_children_lock_sensor_init(mock_vacuum_data: Any) -> None:
    """Test children lock sensor initialization."""

    sensor = RobovacChildrenLockSensor(mock_vacuum_data, "176")
    assert sensor is not None
    assert sensor.robovac_id == mock_vacuum_data[CONF_ID]


@pytest.mark.asyncio
async def test_error_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
    """Test error sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_error_sensor_update_no_tuyastatus(mock_vacuum_data: Any) -> None:
    """Test error sensor update when tuyastatus not available."""

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
async def test_error_sensor_update_no_dps_code(mock_vacuum_data: Any) -> None:
    """Test error sensor update when DPS code not in tuyastatus."""

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
async def test_notification_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
    """Test notification sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacNotificationSensor(mock_data, "178")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_consumable_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
    """Test consumable sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacConsumableSensor(mock_data, "168", "side_brush", "Side Brush", "mdi:brush")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_clean_type_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
    """Test clean type sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacCleanTypeSensor(mock_data, "154")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_wifi_signal_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
    """Test WiFi signal sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacWifiSignalSensor(mock_data, "176")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_last_clean_area_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
    """Test last clean area sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanAreaSensor(mock_data, "179")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_firmware_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
    """Test firmware sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacFirmwareSensor(mock_data, "169")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_work_status_v2_sensor_update_no_vacuum() -> None:
    """Test work status v2 sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacWorkStatusV2Sensor(mock_data, "173")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_last_clean_record_sensor_update_no_vacuum(mock_vacuum_data: Any) -> None:
    """Test last clean record sensor update when vacuum entity not found."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanRecordSensor(mock_data, "164")

    # Mock hass with no vacuum entity
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_error_sensor_update_successful(mock_vacuum_data: Any) -> None:
    """Test error sensor update with successful decode."""

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
async def test_notification_sensor_update_successful(mock_vacuum_data: Any) -> None:
    """Test notification sensor update with successful decode."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacNotificationSensor(mock_data, "178")

    # Mock vacuum entity with notification data
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"178": "AA=="}

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_error_code",
        return_value="no_error"
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value is None  # no_error returns None


@pytest.mark.asyncio
async def test_wifi_signal_sensor_update_no_data_first_time(mock_vacuum_data: Any) -> None:
    """Test WiFi signal sensor when no data available on first update."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacWifiSignalSensor(mock_data, "176")

    # Mock vacuum entity with empty tuyastatus
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = None

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    # First update with no data
    await sensor.async_update()
    assert sensor._attr_available is False
    assert not sensor._has_had_data


@pytest.mark.asyncio
async def test_last_clean_duration_sensor_update_no_data_on_subsequent(mock_vacuum_data: Any) -> None:
    """Test last clean duration sensor keeps previous state if no new data."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanDurationSensor(mock_data, "179")
    sensor._has_had_data = True  # Already had data
    sensor._attr_available = True
    sensor._attr_native_value = 60

    # Mock vacuum with no data
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {}

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()
    # Should keep previous state since we already had data
    assert sensor._has_had_data
    assert sensor._attr_native_value == 60

# ============================================================================
# Successful Update Path Tests (Scenario #3)
# ============================================================================


@pytest.mark.asyncio
async def test_error_sensor_successful_update_with_error(mock_vacuum_data: Any) -> None:
    """Test error sensor successfully updates with actual error data."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # Setup proper mocks
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"177": "error_data"}
    mock_vacuum.vacuum = MagicMock()
    mock_vacuum.vacuum.getRoboVacHumanReadableValue.return_value = "Battery low"

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == "Battery low"
    assert sensor._has_had_data is True


@pytest.mark.asyncio
async def test_error_sensor_successful_update_no_error(mock_vacuum_data: Any) -> None:
    """Test error sensor updates with no error state."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # Setup proper mocks
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"177": "error_data"}
    mock_vacuum.vacuum = MagicMock()
    mock_vacuum.vacuum.getRoboVacHumanReadableValue.return_value = "no_error"

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value is None  # no_error becomes None
    assert sensor._has_had_data is True


@pytest.mark.asyncio
async def test_notification_sensor_successful_update(mock_hass_with_valid_vacuum: Any) -> None:
    """Test notification sensor successfully decodes and updates."""

    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacNotificationSensor(mock_data, "178")
    sensor.hass = mock_hass_with_valid_vacuum

    with patch(
        "custom_components.robovac.sensor.decode_error_code",
        return_value="Task finished"
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == "Task finished"
    assert sensor._has_had_data is True


@pytest.mark.asyncio
async def test_battery_sensor_successful_update(mock_hass_with_valid_vacuum: Any) -> None:
    """Test battery sensor successfully updates with valid data."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacBatterySensor(mock_data)
    sensor.hass = mock_hass_with_valid_vacuum

    mock_hass_with_valid_vacuum.data["robovac"]["vacuums"]["test_id"].get_dps_code.return_value = str(
        TuyaCodes.BATTERY_LEVEL
    )

    await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == 85

# ============================================================================
# Missing DPS Code Tests (Scenario #5.2)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize("sensor_class,dps_code", [
    (RobovacErrorSensor, "177"),
    (RobovacNotificationSensor, "178"),
    (RobovacConsumableSensor, "168"),
    (RobovacCleanTypeSensor, "154"),
])
async def test_sensor_missing_dps_code(sensor_class: Any, dps_code: Any) -> None:
    """Test sensors handle missing DPS code in tuyastatus."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}

    if sensor_class == RobovacConsumableSensor:
        sensor = sensor_class(mock_data, dps_code, "side_brush", "Side Brush", "mdi:brush")
    else:
        sensor = sensor_class(mock_data, dps_code)

    # Vacuum with empty tuyastatus (no DPS code)
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass
    sensor._has_had_data = False  # First update

    await sensor.async_update()

    assert sensor._attr_available is False

# ============================================================================
# Malformed Data Error Handling Tests (Scenario #5.3)
# ============================================================================


@pytest.mark.asyncio
async def test_battery_sensor_malformed_data(mock_vacuum_data: Any) -> None:
    """Test battery sensor handles malformed data gracefully."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacBatterySensor(mock_data)

    # Vacuum with malformed battery value
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {str(TuyaCodes.BATTERY_LEVEL): "invalid_number"}
    mock_vacuum.get_dps_code.return_value = str(TuyaCodes.BATTERY_LEVEL)

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_battery_sensor_none_value(mock_vacuum_data: Any) -> None:
    """Test battery sensor handles None battery value."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacBatterySensor(mock_data)

    # Vacuum with None battery value
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {str(TuyaCodes.BATTERY_LEVEL): None}
    mock_vacuum.get_dps_code.return_value = str(TuyaCodes.BATTERY_LEVEL)

    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is False

# ============================================================================
# State Persistence Tests (Scenario #5.4)
# ============================================================================


@pytest.mark.asyncio
async def test_error_sensor_state_persistence(mock_vacuum_data: Any) -> None:
    """Test error sensor maintains state across updates without new data."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    # First update with data
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"177": "error_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_error_code",
        return_value="Battery low"
    ):
        await sensor.async_update()

    old_value = sensor._attr_native_value
    old_available = sensor._attr_available

    # Second update with no data - should maintain state
    mock_vacuum.tuyastatus = {}
    await sensor.async_update()

    assert sensor._attr_native_value == old_value
    assert sensor._attr_available == old_available
    assert sensor._has_had_data is True


@pytest.mark.asyncio
async def test_firmware_sensor_state_persistence(mock_vacuum_data: Any) -> None:
    """Test firmware sensor maintains state when data becomes unavailable."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacFirmwareSensor(mock_data, "169")

    # First update with data
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"169": "device_info_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_device_info",
        return_value={"software": "1.0.0"}
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    old_value = sensor._attr_native_value

    # Second update without DPS code - should keep old state
    mock_vacuum.tuyastatus = {}
    await sensor.async_update()

    assert sensor._attr_native_value == old_value
    assert sensor._has_had_data is True


@pytest.mark.asyncio
async def test_last_clean_area_sensor_value_accumulation(mock_vacuum_data: Any) -> None:
    """Test last clean area sensor accumulates data properly."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanAreaSensor(mock_data, "179")

    # First update
    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"179": "data1"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_analysis_response",
        return_value={"clean_area_m2": 50.5}
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == 50.5
    assert sensor._has_had_data is True

    # Second update with new data
    mock_vacuum.tuyastatus = {"179": "data2"}

    with patch(
        "custom_components.robovac.sensor.decode_analysis_response",
        return_value={"clean_area_m2": 75.3}
    ):
        await sensor.async_update()

    # Should update to new value
    assert sensor._attr_native_value == 75.3


@pytest.mark.asyncio
async def test_consumable_sensor_successful_update(mock_vacuum_data: Any) -> None:
    """Test consumable sensor successfully updates with data."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacConsumableSensor(mock_data, "168", "side_brush", "Side Brush", "mdi:brush")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"168": "consumable_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_consumable_response",
        return_value={"side_brush": 45}
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == 45


@pytest.mark.asyncio
async def test_clean_type_sensor_successful_update(mock_vacuum_data: Any) -> None:
    """Test clean type sensor successfully updates with data."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacCleanTypeSensor(mock_data, "154")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"154": "clean_param_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_clean_param_response",
        return_value={"running_clean_param": {"clean_type": "Sweep and mop"}}
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == "Sweep and mop"


@pytest.mark.asyncio
async def test_work_status_v2_sensor_successful_update() -> None:
    """Test work status v2 sensor successfully updates."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacWorkStatusV2Sensor(mock_data, "173")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"173": "status_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_work_status_v2",
        return_value="Cleaning"
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == "Cleaning"


@pytest.mark.asyncio
async def test_last_clean_record_sensor_successful_update(mock_vacuum_data: Any) -> None:
    """Test last clean record sensor successfully updates."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanRecordSensor(mock_data, "164")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"164": "record_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_clean_record_list",
        return_value=[{"timestamp": 1234567890, "status": "successful"}]
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value is not None


# ============================================================================
# Tests for async_setup_entry and entity creation
# ============================================================================

@pytest.mark.asyncio
async def test_async_setup_entry_basic() -> None:
    """Test async_setup_entry creates battery sensor for each vacuum."""
    from custom_components.robovac.sensor import async_setup_entry
    from homeassistant.config_entries import ConfigEntry

    mock_hass = MagicMock()
    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.data = {
        "vacuums": {
            "vac1": {
                CONF_ID: "vac1",
                "name": "Test Vacuum 1",
                "model": "T2118"
            }
        }
    }

    entities_added = []

    def mock_add_entities(entities):
        entities_added.extend(entities)

    await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

    # Should at least add battery sensor
    assert len(entities_added) >= 1
    assert any(isinstance(e, RobovacBatterySensor) for e in entities_added)


@pytest.mark.asyncio
async def test_async_setup_entry_with_t2277_model() -> None:
    """Test async_setup_entry creates all sensors for T2277 model with full command set."""
    from custom_components.robovac.sensor import async_setup_entry
    from homeassistant.config_entries import ConfigEntry

    mock_hass = MagicMock()
    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.data = {
        "vacuums": {
            "vac1": {
                CONF_ID: "vac1",
                "name": "Test Vacuum",
                "model": "T2277"  # Model with many commands
            }
        }
    }

    entities_added = []

    def mock_add_entities(entities):
        entities_added.extend(entities)

    await async_setup_entry(mock_hass, mock_config_entry, mock_add_entities)

    # T2277 should create many sensors due to command availability
    assert len(entities_added) > 5


@pytest.mark.asyncio
async def test_battery_sensor_string_value() -> None:
    """Test battery sensor handles string battery values."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacBatterySensor(mock_data)

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {str(TuyaCodes.BATTERY_LEVEL): "85"}  # String value
    mock_vacuum.get_dps_code = MagicMock(return_value=str(TuyaCodes.BATTERY_LEVEL))
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == 85


@pytest.mark.asyncio
async def test_battery_sensor_float_value() -> None:
    """Test battery sensor handles float battery values."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacBatterySensor(mock_data)

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {str(TuyaCodes.BATTERY_LEVEL): 85.7}  # Float value
    mock_vacuum.get_dps_code = MagicMock(return_value=str(TuyaCodes.BATTERY_LEVEL))
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == 85


@pytest.mark.asyncio
async def test_battery_sensor_key_error() -> None:
    """Test battery sensor handles KeyError gracefully."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacBatterySensor(mock_data)

    mock_hass = MagicMock()
    # Simulate missing domain key
    mock_hass.data = {}
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_battery_sensor_attribute_error() -> None:
    """Test battery sensor handles AttributeError gracefully."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacBatterySensor(mock_data)

    mock_hass = MagicMock()
    # Simulate missing tuyastatus attribute
    mock_vacuum = MagicMock()
    del mock_vacuum.tuyastatus  # Remove attribute
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is False


# ============================================================================
# Error Sensor additional tests
# ============================================================================

@pytest.mark.asyncio
async def test_error_sensor_with_keyerror() -> None:
    """Test error sensor handles KeyError in data access."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    mock_hass = MagicMock()
    mock_hass.data = {}  # Missing domain data
    sensor.hass = mock_hass

    await sensor.async_update()

    assert sensor._attr_available is False


@pytest.mark.asyncio
async def test_error_sensor_state_after_update() -> None:
    """Test error sensor maintains state through updates."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacErrorSensor(mock_data, "177")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {}  # Empty status first
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    # First update with no data
    await sensor.async_update()
    first_state = sensor._attr_native_value

    # Second update, still no data
    await sensor.async_update()
    second_state = sensor._attr_native_value

    # State should be preserved
    assert first_state == second_state


# ============================================================================
# Firmware Sensor additional tests
# ============================================================================

@pytest.mark.asyncio
async def test_firmware_sensor_with_exception_during_decode() -> None:
    """Test firmware sensor handles exceptions during decode."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacFirmwareSensor(mock_data, "169")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"169": "device_info_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    # Mock decode to raise an exception
    with patch(
        "custom_components.robovac.sensor.decode_device_info",
        side_effect=ValueError("Invalid data")
    ):
        await sensor.async_update()

    assert sensor._attr_available is False


# ============================================================================
# Consumable Sensor additional tests
# ============================================================================

@pytest.mark.asyncio
async def test_consumable_sensor_multiple_types() -> None:
    """Test consumable sensors for different consumable types."""
    consumable_types = ["side_brush", "rolling_brush", "filter_mesh", "scrape", "sensor", "dustbag"]

    for consumable_type in consumable_types:
        mock_data = {CONF_ID: "test_id", "name": "Test"}
        sensor = RobovacConsumableSensor(mock_data, "168", consumable_type, f"{consumable_type.title()}", "mdi:brush")

        mock_vacuum = MagicMock()
        mock_vacuum.tuyastatus = {"168": "consumable_data"}
        mock_hass = MagicMock()
        mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
        sensor.hass = mock_hass

        with patch(
            "custom_components.robovac.sensor.decode_consumable_response",
            return_value={consumable_type: 75}
        ):
            await sensor.async_update()

        assert sensor._attr_available is True
        assert sensor._attr_native_value == 75


@pytest.mark.asyncio
async def test_consumable_sensor_missing_consumable_key() -> None:
    """Test consumable sensor handles missing consumable key in decoded data."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacConsumableSensor(mock_data, "168", "side_brush", "Side Brush", "mdi:brush")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"168": "consumable_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_consumable_response",
        return_value={"rolling_brush": 80}  # Missing side_brush
    ):
        await sensor.async_update()

    assert sensor._attr_available is False


# ============================================================================
# WiFi Sensor additional tests
# ============================================================================

@pytest.mark.asyncio
async def test_wifi_signal_sensor_with_signal_value() -> None:
    """Test wifi signal sensor with valid signal strength."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacWifiSignalSensor(mock_data, "176")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"176": "wifi_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_unisetting_response",
        return_value={"signal_strength": -45}  # dBm value
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == -45


@pytest.mark.asyncio
async def test_wifi_ssid_sensor_decoding() -> None:
    """Test wifi SSID sensor extracts network name."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacWifiSsidSensor(mock_data, "176")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"176": "wifi_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_unisetting_response",
        return_value={"wifi_ssid": "MyNetwork"}
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == "MyNetwork"


# ============================================================================
# Last Clean Sensors additional tests
# ============================================================================

@pytest.mark.asyncio
async def test_last_clean_area_sensor_with_area_value() -> None:
    """Test last clean area sensor calculates from analysis data."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanAreaSensor(mock_data, "179")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"179": "analysis_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_analysis_response",
        return_value={"clean_area_m2": 45.5}
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == 45.5


@pytest.mark.asyncio
async def test_last_clean_duration_sensor_with_time_value() -> None:
    """Test last clean duration sensor extracts time in minutes."""
    mock_data = {CONF_ID: "test_id", "name": "Test"}
    sensor = RobovacLastCleanDurationSensor(mock_data, "179")

    mock_vacuum = MagicMock()
    mock_vacuum.tuyastatus = {"179": "analysis_data"}
    mock_hass = MagicMock()
    mock_hass.data = {"robovac": {"vacuums": {"test_id": mock_vacuum}}}
    sensor.hass = mock_hass

    with patch(
        "custom_components.robovac.sensor.decode_analysis_response",
        return_value={"clean_time_s": 1800}  # 30 minutes
    ):
        await sensor.async_update()

    assert sensor._attr_available is True
    assert sensor._attr_native_value == 30  # Should be converted to minutes
