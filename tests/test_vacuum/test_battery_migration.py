"""Test battery migration during Home Assistant config entry setup."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import label_registry as lr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.robovac.const import CONF_VACS, DOMAIN


@pytest.fixture
def config_entry(hass: HomeAssistant, mock_vacuum_data: dict) -> MockConfigEntry:
    """Register a RoboVac config entry without loading it."""
    device_id = mock_vacuum_data[CONF_ID]
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_VACS: {device_id: mock_vacuum_data}})
    entry.add_to_hass(hass)
    return entry


async def _start_robovac(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Load the sensor platform through the config entry without discovery sockets."""
    with (
        patch("custom_components.robovac.TuyaLocalDiscovery.start"),
        patch("custom_components.robovac.PLATFORMS", [Platform.SENSOR]),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


@pytest.mark.parametrize("disabled_by", [None, er.RegistryEntryDisabler.USER])
async def test_legacy_battery_keeps_customisations(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    disabled_by: er.RegistryEntryDisabler | None,
) -> None:
    """Keep the legacy sensor's identity and settings when changing its unique ID."""
    device_id = next(iter(config_entry.data[CONF_VACS]))
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id, identifiers={(DOMAIN, device_id)}
    )
    legacy = entity_registry.async_get_or_create(
        "sensor", DOMAIN, device_id,
        config_entry=config_entry, device_id=device.id,
        suggested_object_id="hallway_charge", disabled_by=disabled_by,
    )
    area = ar.async_get(hass).async_create("Hallway")
    label = lr.async_get(hass).async_create("Robot")
    legacy = entity_registry.async_update_entity(
        legacy.entity_id, name="Hallway battery", icon="mdi:battery-heart",
        hidden_by=er.RegistryEntryHider.USER, area_id=area.id, labels={label.label_id},
    )

    await _start_robovac(hass, config_entry)

    assert entity_registry.async_get_entity_id("sensor", DOMAIN, device_id) is None
    assert entity_registry.async_get_entity_id("sensor", DOMAIN, f"{device_id}_battery") == legacy.entity_id
    migrated = entity_registry.async_get(legacy.entity_id)
    assert migrated is not None
    assert migrated.id == legacy.id
    assert migrated.config_entry_id == config_entry.entry_id
    assert migrated.device_id == device.id
    assert migrated.name == legacy.name
    assert migrated.icon == legacy.icon
    assert migrated.hidden_by == legacy.hidden_by
    assert migrated.area_id == legacy.area_id
    assert migrated.labels == legacy.labels
    assert migrated.disabled_by == disabled_by
    assert (hass.states.get(legacy.entity_id) is not None) == (disabled_by is None)


async def test_duplicate_cleanup_keeps_working_battery(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Remove the obsolete sensor and preserve the working registration."""
    device_id = next(iter(config_entry.data[CONF_VACS]))
    legacy = entity_registry.async_get_or_create(
        "sensor", DOMAIN, device_id, config_entry=config_entry,
        suggested_object_id="obsolete_charge",
    )
    working = entity_registry.async_get_or_create(
        "sensor", DOMAIN, f"{device_id}_battery", config_entry=config_entry,
        suggested_object_id="working_charge",
    )
    working = entity_registry.async_update_entity(working.entity_id, name="Working battery")

    await _start_robovac(hass, config_entry)

    assert entity_registry.async_get(legacy.entity_id) is None
    assert hass.states.get(legacy.entity_id) is None
    assert entity_registry.async_get_entity_id("sensor", DOMAIN, f"{device_id}_battery") == working.entity_id
    current = entity_registry.async_get(working.entity_id)
    assert current is not None
    assert current.id == working.id
    assert current.name == working.name
    assert hass.states.get(working.entity_id) is not None


async def test_fresh_battery_keeps_other_platform_registration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Register a new sensor while leaving another platform's matching unique ID alone."""
    device_id = next(iter(config_entry.data[CONF_VACS]))
    other = entity_registry.async_get_or_create("sensor", "mqtt", device_id)

    await _start_robovac(hass, config_entry)

    assert entity_registry.async_get(other.entity_id) == other
    battery_id = entity_registry.async_get_entity_id("sensor", DOMAIN, f"{device_id}_battery")
    assert battery_id is not None
    assert hass.states.get(battery_id) is not None
