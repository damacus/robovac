"""Tests for the DPS-backed water level select (T2276 DPS 105)."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.robovac.select import RobovacWaterLevelSelect
from custom_components.robovac.vacuums.base import RobovacCommand
from custom_components.robovac.vacuums.T2276 import T2276

VALUES = {"low": "Low", "medium": "Mid", "high": "High"}


def _select(mock_vacuum_data: Any, status: dict[str, Any]) -> tuple[RobovacWaterLevelSelect, Any, Any]:
    select = RobovacWaterLevelSelect(mock_vacuum_data, "105", VALUES)
    device = MagicMock()
    device.async_set = AsyncMock()
    vacuum = MagicMock()
    vacuum.vacuum = device
    vacuum.tuyastatus = status
    hass = MagicMock()
    hass.data = {"robovac": {"vacuums": {mock_vacuum_data["id"]: vacuum}}}
    select.hass = hass
    select.async_write_ha_state = MagicMock()
    return select, device, vacuum


def test_t2276_water_level_values() -> None:
    """The model maps the options to the strings the robot reports."""
    command = T2276.commands[RobovacCommand.WATER_LEVEL]
    assert command["code"] == 105
    assert command["values"] == VALUES


@pytest.mark.asyncio
async def test_water_level_select_reads_raw_value(mock_vacuum_data: Any) -> None:
    """The select shows the option that matches the raw DPS value."""
    select, _, _ = _select(mock_vacuum_data, {"105": "Mid"})

    await select.async_update()

    assert select.options == ["Low", "Medium", "High"]
    assert select.current_option == "Medium"
    assert select.available is True


@pytest.mark.asyncio
async def test_water_level_select_unavailable_without_value(mock_vacuum_data: Any) -> None:
    """The select is unavailable when the device reports no value."""
    select, _, _ = _select(mock_vacuum_data, {})

    await select.async_update()

    assert select.available is False
    assert select.current_option is None


@pytest.mark.asyncio
async def test_water_level_select_writes_device_value(mock_vacuum_data: Any) -> None:
    """Choosing an option writes the device string to the DPS."""
    select, device, vacuum = _select(mock_vacuum_data, {"105": "Low"})

    with patch("custom_components.robovac.select.async_call_later"):
        await select.async_select_option("High")

    device.async_set.assert_awaited_once_with({"105": "High"})
    assert vacuum.tuyastatus["105"] == "High"
    assert select.current_option == "High"


@pytest.mark.asyncio
async def test_water_level_select_ignores_unknown_option(mock_vacuum_data: Any) -> None:
    """An unknown option does not write to the device."""
    select, device, _ = _select(mock_vacuum_data, {"105": "Low"})

    await select.async_select_option("Overflowing")

    device.async_set.assert_not_awaited()
