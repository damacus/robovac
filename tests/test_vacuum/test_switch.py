"""Tests for native DPS-backed RoboVac switches."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.robovac.switch import RobovacBooleanDpsSwitch


@pytest.mark.asyncio
async def test_boolean_dps_switch_reads_and_writes(mock_vacuum_data: Any) -> None:
    """The T2276 boolean switches read and write their mapped DPS."""
    switch = RobovacBooleanDpsSwitch(
        mock_vacuum_data,
        "118",
        "boost_iq",
        "BoostIQ",
        "mdi:weather-windy",
    )
    device = MagicMock()
    device.async_set = AsyncMock()
    vacuum = MagicMock()
    vacuum.vacuum = device
    vacuum.tuyastatus = {"118": True}
    hass = MagicMock()
    hass.data = {"robovac": {"vacuums": {mock_vacuum_data["id"]: vacuum}}}
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()

    await switch.async_update()
    assert switch.is_on is True

    with patch("custom_components.robovac.switch.async_call_later"):
        await switch.async_turn_off()

    device.async_set.assert_awaited_once_with({"118": False})
    assert vacuum.tuyastatus["118"] is False
    assert switch.is_on is False
