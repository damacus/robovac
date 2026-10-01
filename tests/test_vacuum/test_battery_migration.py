"""Tests for the battery entity registry migration.

Commit 1989921 (#21) changed the battery sensor unique_id from the bare
device ID to ``<device_id>_battery`` without a registry migration. These
tests cover ``_migrate_battery_entity_registry`` for every install shape:

- fresh installs (no legacy registration): no-op
- upgraded installs with only the legacy registration: remove + re-register
  on the legacy slot, preserving entity_id, device, and enabled state
- upgraded installs with both registrations: remove only the orphan
- safety: never touch registrations owned by other platforms
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_ID, CONF_NAME

from custom_components.robovac.const import DOMAIN
from custom_components.robovac.sensor import _migrate_battery_entity_registry

DEVICE_ID = "eb5580d8cb5ce440aan1r7"
OLD_UNIQUE_ID = DEVICE_ID
NEW_UNIQUE_ID = f"{DEVICE_ID}_battery"
OLD_ENTITY_ID = "sensor.vac_battery"


def _item() -> dict:
    """Return a vacuum config item as stored in the config entry."""
    return {CONF_ID: DEVICE_ID, CONF_NAME: "Vac"}


def _registry_with(old_entry: MagicMock | None, new_entity_id: str | None) -> MagicMock:
    """Return a mocked entity registry.

    ``async_get_entity_id`` resolves the legacy lookup first and the
    new-unique_id lookup second (side_effect order matches call order).
    """
    registry = MagicMock()
    registry.async_get_entity_id.side_effect = [OLD_ENTITY_ID, new_entity_id]
    registry.async_get.return_value = old_entry
    return registry


@pytest.mark.asyncio
async def test_noop_when_no_legacy_registration() -> None:
    """Fresh installs (or already-migrated) must not be touched."""
    hass = MagicMock()
    registry = MagicMock()
    registry.async_get_entity_id.return_value = None

    with patch("custom_components.robovac.sensor.er.async_get", return_value=registry):
        await _migrate_battery_entity_registry(hass, _item())

    registry.async_remove.assert_not_called()
    registry.async_get_or_create.assert_not_called()


@pytest.mark.asyncio
async def test_noop_when_legacy_entry_platform_mismatch() -> None:
    """A registration owned by another platform must never be removed."""
    hass = MagicMock()
    foreign = MagicMock(platform="some_other_integration")
    registry = _registry_with(foreign, new_entity_id=None)

    with patch("custom_components.robovac.sensor.er.async_get", return_value=registry):
        await _migrate_battery_entity_registry(hass, _item())

    registry.async_remove.assert_not_called()
    registry.async_get_or_create.assert_not_called()


@pytest.mark.asyncio
async def test_legacy_only_migration_preserves_entity_state() -> None:
    """Legacy-only installs: remove orphan, re-register new id on old slot."""
    hass = MagicMock()
    old_entry = MagicMock(
        platform=DOMAIN,
        device_id="device-123",
        disabled_by=None,
    )
    registry = _registry_with(old_entry, new_entity_id=None)

    with patch("custom_components.robovac.sensor.er.async_get", return_value=registry):
        await _migrate_battery_entity_registry(hass, _item())

    registry.async_remove.assert_called_once_with(OLD_ENTITY_ID)
    registry.async_get_or_create.assert_called_once_with(
        "sensor",
        DOMAIN,
        NEW_UNIQUE_ID,
        suggested_object_id="vac_battery",
        device_id="device-123",
        disabled_by=None,
    )


@pytest.mark.asyncio
async def test_both_present_removes_only_orphan() -> None:
    """Installs with a working new-style entity: remove the orphan only."""
    hass = MagicMock()
    old_entry = MagicMock(
        platform=DOMAIN,
        device_id="device-123",
        disabled_by=None,
    )
    registry = _registry_with(old_entry, new_entity_id="sensor.vac_battery_2")

    with patch("custom_components.robovac.sensor.er.async_get", return_value=registry):
        await _migrate_battery_entity_registry(hass, _item())

    registry.async_remove.assert_called_once_with(OLD_ENTITY_ID)
    registry.async_get_or_create.assert_not_called()


@pytest.mark.asyncio
async def test_migration_preserves_disabled_state() -> None:
    """A user-disabled legacy entity stays disabled after migration."""
    hass = MagicMock()
    old_entry = MagicMock(
        platform=DOMAIN,
        device_id="device-123",
        disabled_by="user",
    )
    registry = _registry_with(old_entry, new_entity_id=None)

    with patch("custom_components.robovac.sensor.er.async_get", return_value=registry):
        await _migrate_battery_entity_registry(hass, _item())

    registry.async_remove.assert_called_once_with(OLD_ENTITY_ID)
    registry.async_get_or_create.assert_called_once_with(
        "sensor",
        DOMAIN,
        NEW_UNIQUE_ID,
        suggested_object_id="vac_battery",
        device_id="device-123",
        disabled_by="user",
    )


@pytest.mark.asyncio
async def test_battery_sensor_still_uses_new_unique_id() -> None:
    """Guard: the sensor entity itself must keep the migrated unique_id."""
    from custom_components.robovac.sensor import RobovacBatterySensor

    sensor = RobovacBatterySensor(_item())
    assert sensor._attr_unique_id == NEW_UNIQUE_ID
