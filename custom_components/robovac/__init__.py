# Copyright 2022 Brendan McCluskey
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""The Eufy Robovac integration."""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from .const import CONF_AUTODISCOVERY, CONF_VACS, DOMAIN

from .tuyalocaldiscovery import TuyaLocalDiscovery

PLATFORMS = [Platform.VACUUM, Platform.SENSOR, Platform.SELECT, Platform.SWITCH]
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Eufy Robovac component.

    This function initializes the component and sets up the discovery service.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.

    Returns:
        True if setup was successful.
    """
    hass.data.setdefault(DOMAIN, {CONF_VACS: {}})

    async def update_device(device: Dict[str, Any]) -> None:
        entry = async_get_config_entry_for_device(hass, device["gwId"])

        if entry is None:
            return

        if not entry.state.recoverable:
            return

        device_id = device["gwId"]
        discovered_ip = device.get("ip")
        vacuum = entry.data[CONF_VACS].get(device_id)
        if (
            vacuum is not None
            and discovered_ip
            and vacuum.get(CONF_AUTODISCOVERY, True)
            and vacuum.get(CONF_IP_ADDRESS) != discovered_ip
        ):
            updated_vacuums = entry.data[CONF_VACS].copy()
            updated_vacuums[device_id] = {**vacuum, CONF_IP_ADDRESS: discovered_ip}
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_VACS: updated_vacuums}
            )
            _LOGGER.debug("Updated ip address of %s to %s", device_id, discovered_ip)

    tuyalocaldiscovery = TuyaLocalDiscovery(update_device)
    try:
        await tuyalocaldiscovery.start()
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, tuyalocaldiscovery.close)
    except Exception:
        _LOGGER.exception("failed to set up discovery")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eufy Robovac from a config entry."""
    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def async_get_config_entry_for_device(
    hass: HomeAssistant, device_id: str
) -> Optional[ConfigEntry]:
    """Find the config entry for a specific device ID.

    Args:
        hass: The Home Assistant instance.
        device_id: The device ID to find.

    Returns:
        The config entry if found, None otherwise.
    """
    current_entries = hass.config_entries.async_entries(DOMAIN)
    for entry in current_entries:
        if device_id in entry.data[CONF_VACS]:
            return entry
    return None
