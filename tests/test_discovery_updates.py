"""Offline regressions for UDP discovery updates to config entries."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_IP_ADDRESS

from custom_components.robovac import async_setup
from custom_components.robovac.const import CONF_AUTODISCOVERY, CONF_VACS, DOMAIN


@pytest.mark.asyncio
@pytest.mark.parametrize("discovered_ip", [None, "", "old-ip", "new-ip"])
async def test_discovery_updates_only_valid_changed_ip_without_mutating_entry(
    discovered_ip: str | None,
) -> None:
    """Do not replace a usable IP with an empty broadcast or mutate entry.data."""
    original = {
        "username": "fixture-user",
        CONF_VACS: {
            "device-1": {
                CONF_IP_ADDRESS: "old-ip",
                CONF_AUTODISCOVERY: True,
            },
            "device-2": {CONF_IP_ADDRESS: "other-ip"},
        },
    }
    entry = SimpleNamespace(
        data=original, entry_id="fixture-entry", state=SimpleNamespace(recoverable=True)
    )
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_entries.return_value = [entry]
    hass.config_entries.async_reload = AsyncMock()

    with patch("custom_components.robovac.TuyaLocalDiscovery") as discovery:
        discovery.return_value.start = AsyncMock()
        assert await async_setup(hass, entry)
        callback = discovery.call_args.args[0]
        await callback({"gwId": "device-1", "ip": discovered_ip})

    assert original[CONF_VACS]["device-1"][CONF_IP_ADDRESS] == "old-ip"
    assert original[CONF_VACS]["device-2"][CONF_IP_ADDRESS] == "other-ip"
    if discovered_ip and discovered_ip != "old-ip":
        hass.config_entries.async_update_entry.assert_called_once()
        updated = hass.config_entries.async_update_entry.call_args.kwargs["data"]
        assert updated["username"] == "fixture-user"
        assert updated[CONF_VACS]["device-1"][CONF_IP_ADDRESS] == discovered_ip
        assert updated[CONF_VACS]["device-1"] is not original[CONF_VACS]["device-1"]
        assert updated[CONF_VACS] is not original[CONF_VACS]
        assert updated[CONF_VACS]["device-2"] == original[CONF_VACS]["device-2"]
        assert updated[CONF_VACS]["device-2"] is original[CONF_VACS]["device-2"]
        hass.config_entries.async_reload.assert_not_awaited()
    else:
        hass.config_entries.async_update_entry.assert_not_called()
        hass.config_entries.async_reload.assert_not_awaited()
    assert DOMAIN in hass.data


@pytest.mark.asyncio
async def test_discovery_does_not_update_manual_ip() -> None:
    original = {
        CONF_VACS: {
            "device-1": {
                CONF_IP_ADDRESS: "old-ip",
                CONF_AUTODISCOVERY: False,
            }
        }
    }
    entry = SimpleNamespace(
        data=original, entry_id="fixture-entry", state=SimpleNamespace(recoverable=True)
    )
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_entries.return_value = [entry]
    hass.config_entries.async_reload = AsyncMock()
    with patch("custom_components.robovac.TuyaLocalDiscovery") as discovery:
        discovery.return_value.start = AsyncMock()
        await async_setup(hass, entry)
        await discovery.call_args.args[0]({"gwId": "device-1", "ip": "new-ip"})
    hass.config_entries.async_update_entry.assert_not_called()
    hass.config_entries.async_reload.assert_not_awaited()
    assert original[CONF_VACS]["device-1"][CONF_IP_ADDRESS] == "old-ip"
