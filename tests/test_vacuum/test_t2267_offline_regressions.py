"""Offline battery DPS regression for the T2267 L60."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
)

from custom_components.robovac.sensor import RobovacBatterySensor
from custom_components.robovac.vacuum import RoboVacEntity


@pytest.fixture
def offline_l60():
    """Use the real model and entity without constructing a Tuya transport."""
    item = {
        CONF_NAME: "Offline L60",
        CONF_ID: "offline-id",
        CONF_MAC: "00:00:00:00:00:00",
        CONF_MODEL: "T2267",
        CONF_IP_ADDRESS: "127.0.0.1",
        CONF_ACCESS_TOKEN: "offline-only-placeholder",
        CONF_DESCRIPTION: "Offline L60",
    }
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        entity = RoboVacEntity(item)
    return entity, item


async def _read_battery(entity, item, dps):
    entity.vacuum._dps = dps
    entity.update_entity_values()
    sensor = RobovacBatterySensor(item)
    sensor.hass = SimpleNamespace(data={"robovac": {"vacuums": {item[CONF_ID]: entity}}})
    await sensor.async_update()
    return sensor


@pytest.mark.asyncio
async def test_t2267_battery_161_fallback(offline_l60):
    """The DPS 161 value reported in issue #353 feeds the battery sensor."""
    entity, item = offline_l60
    sensor = await _read_battery(entity, item, {"158": "Standard", "161": 80})
    assert sensor._attr_available is True
    assert sensor._attr_native_value == 80


@pytest.mark.asyncio
async def test_t2267_battery_163_takes_precedence(offline_l60):
    entity, item = offline_l60
    sensor = await _read_battery(entity, item, {"161": 80, "163": 61})
    assert sensor._attr_available is True
    assert sensor._attr_native_value == 61


@pytest.mark.asyncio
async def test_other_models_do_not_use_l60_fallback(offline_l60):
    entity, item = offline_l60
    entity._attr_model_code = "T2277"
    sensor = await _read_battery(entity, item, {"161": 80})
    assert sensor._attr_available is False
