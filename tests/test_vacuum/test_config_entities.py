"""Tests for RoboVac configuration entities."""

from types import SimpleNamespace

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

from custom_components.robovac.const import CONF_VACS
from custom_components.robovac.select import async_setup_entry as async_setup_select_entry
from custom_components.robovac.sensor import async_setup_entry as async_setup_sensor_entry
from custom_components.robovac.switch import async_setup_entry as async_setup_switch_entry


def _vacuum_config(model: str) -> dict[str, str]:
    return {
        CONF_NAME: "Test Vacuum",
        CONF_ID: f"test_{model.lower()}",
        CONF_MODEL: model,
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_key",
        CONF_DESCRIPTION: model,
        CONF_MAC: "aa:bb:cc:dd:ee:ff",
    }


@pytest.mark.asyncio
async def test_t2320_exposes_config_entities() -> None:
    """T2320 exposes X9 Pro clean-param and fan configuration controls."""
    entry = SimpleNamespace(data={CONF_VACS: {"vacuum": _vacuum_config("T2320")}})
    select_entities = []
    switch_entities = []

    await async_setup_select_entry(None, entry, select_entities.extend)
    await async_setup_switch_entry(None, entry, switch_entities.extend)

    assert [entity.name for entity in select_entities] == [
        "Fan speed",
        "Clean type",
        "Mop level",
    ]
    assert [entity.name for entity in switch_entities] == ["Edge mopping"]


@pytest.mark.asyncio
async def test_other_clean_param_models_do_not_get_t2320_config_entities() -> None:
    """Avoid exposing X9-specific config controls on other clean-param models."""
    entry = SimpleNamespace(data={CONF_VACS: {"vacuum": _vacuum_config("T2277")}})
    select_entities = []
    switch_entities = []

    await async_setup_select_entry(None, entry, select_entities.extend)
    await async_setup_switch_entry(None, entry, switch_entities.extend)

    assert select_entities == []
    assert switch_entities == []


@pytest.mark.asyncio
async def test_t2320_does_not_duplicate_clean_type_as_diagnostic_sensor() -> None:
    """T2320 exposes clean type as configuration, not a duplicate sensor."""
    entry = SimpleNamespace(data={CONF_VACS: {"vacuum": _vacuum_config("T2320")}})
    sensor_entities = []

    await async_setup_sensor_entry(None, entry, sensor_entities.extend)

    sensor_names = [entity.name for entity in sensor_entities]
    assert "Clean Type" not in sensor_names
    assert "Warning" in sensor_names


@pytest.mark.asyncio
async def test_other_clean_param_models_keep_clean_type_diagnostic_sensor() -> None:
    """Models without config controls still expose DPS 154 as diagnostics."""
    entry = SimpleNamespace(data={CONF_VACS: {"vacuum": _vacuum_config("T2277")}})
    sensor_entities = []

    await async_setup_sensor_entry(None, entry, sensor_entities.extend)

    assert "Clean Type" in [entity.name for entity in sensor_entities]
