"""RoboVac floor-plan map camera.

Renders the cloud layout map (see map_fetch.py) as a static image, for
devices whose model has Eufy account credentials configured (CONF_USERNAME/
CONF_PASSWORD on the vacuum's config entry item — not required for normal
operation, only for this optional camera).
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_VACS, DOMAIN
from .eufywebapi import EufyLogon
from .map_fetch import (
    MapFetchError,
    RoboVacMapLayout,
    fetch_and_decode,
    fetch_pose,
)
from .tuyawebapi import TuyaAPISession

_LOGGER = logging.getLogger(__name__)

# The map only changes meaningfully between cleans; this is a manual/
# on-demand-friendly default, not a live video feed.
MAP_UPDATE_INTERVAL = timedelta(minutes=15)

# While the vacuum is on the move the cloud delivers a new pose frame every
# ~2 s. Polling is skipped entirely when it is docked or idle.
ROUTE_POLL_INTERVAL = timedelta(seconds=2)
_ROUTE_ACTIVE_STATES = {"cleaning", "returning"}
_MAP_SCALE = 4
_ROUTE_COLOR = (255, 255, 255)

# high6 bits room id -> RGB. Falls back to magenta for an id not listed
# here, so a new/renamed room is obviously visible rather than silently
# wrong-colored. This is Eufy's own 16-color room palette (ORIGIN_MAP_COLOR
# in the Anker eufy app's decompiled const.py), reused so adjacent rooms
# stay visually distinct instead of an arbitrary short cycle colliding.
_DEFAULT_ROOM_COLORS = [
    (0xF9, 0x42, 0x4F), (0xFD, 0xD0, 0x2B), (0x46, 0xA8, 0x90), (0x20, 0x8C, 0xFF),
    (0xFA, 0x7A, 0x80), (0xA8, 0xE7, 0x72), (0x49, 0xF9, 0xCA), (0x7C, 0xF8, 0xFF),
    (0xF3, 0xA0, 0xA4), (0x79, 0xE4, 0x20), (0x65, 0xEA, 0xF3), (0xA1, 0x88, 0xF8),
    (0xF8, 0xC6, 0xA1), (0xBC, 0xFF, 0x83), (0x5C, 0xDB, 0xFA), (0xEE, 0xBA, 0xFC),
]
_SPECIAL_COLORS = {60: (30, 30, 30), 61: (60, 60, 60), 62: (10, 10, 10), 63: (0, 0, 0)}


def _build_tuya_session(item: dict[str, Any]) -> TuyaAPISession | None:
    """Build a Tuya cloud session from this vacuum item's Eufy credentials."""
    username = item.get(CONF_USERNAME)
    password = item.get(CONF_PASSWORD)
    if not username or not password:
        return None
    eufy = EufyLogon(username, password)
    resp = eufy.get_user_info()
    if resp is None or resp.status_code != 200:
        raise UpdateFailed("Eufy login failed")
    user_response = resp.json()
    if user_response.get("res_code") != 1:
        raise UpdateFailed(f"Eufy login rejected: {user_response.get('res_code')}")
    user_info = user_response.get("user_info", {})
    client_id = user_info.get("id")
    region = item.get("region") or "EU"
    country_code = user_info.get("phone_code") or item.get("country_code") or "31"
    timezone_id = user_info.get("timezone") or "Europe/Amsterdam"
    request_host = user_info.get("request_host")
    access_token = user_response.get("access_token")
    if request_host and client_id and access_token:
        settings_resp = eufy.get_user_settings(request_host, client_id, access_token)
        if settings_resp is not None and settings_resp.status_code == 200:
            region = (
                settings_resp.json()
                .get("setting", {})
                .get("home_setting", {})
                .get("tuya_home", {})
                .get("tuya_region_code", region)
            )
    if not client_id:
        return None
    return TuyaAPISession(
        username=f"eh-{client_id}", region=region, timezone=timezone_id,
        phone_code=country_code,
    )


def _render_png(
    layout: RoboVacMapLayout, path: list[tuple[float, float]] | None = None
) -> bytes:
    """Render a decoded layout as a PNG, scaled up for visibility.

    ``path`` is the robot route in map pixels; it is drawn over the rooms.
    """
    from io import BytesIO

    from PIL import Image, ImageDraw

    scale = _MAP_SCALE
    img = Image.new("RGB", (layout.width, layout.height))
    px = img.load()
    for y in range(layout.height):
        row_base = y * layout.width
        for x in range(layout.width):
            room = layout.pixels[row_base + x] >> 2
            if room in _SPECIAL_COLORS:
                color = _SPECIAL_COLORS[room]
            else:
                color = _DEFAULT_ROOM_COLORS[room % len(_DEFAULT_ROOM_COLORS)]
            px[x, y] = color
    img = img.resize(
        (layout.width * scale, layout.height * scale), Image.NEAREST
    )
    if path:
        draw = ImageDraw.Draw(img)
        points = [((x + 0.5) * scale, (y + 0.5) * scale) for x, y in path]
        if len(points) > 1:
            draw.line(points, fill=_ROUTE_COLOR, width=scale // 2)
        rx, ry = points[-1]
        radius = scale
        draw.ellipse(
            [rx - radius, ry - radius, rx + radius, ry + radius],
            fill=_ROUTE_COLOR, outline=(0, 0, 0),
        )
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class RoboVacMapCoordinator(DataUpdateCoordinator[bytes]):
    """Fetches and decodes the cloud map on a slow interval.

    While the vacuum moves, ``async_poll_route`` adds the live robot route.
    """

    def __init__(self, hass: HomeAssistant, item: dict[str, Any]) -> None:
        super().__init__(
            hass, _LOGGER, name=f"{item[CONF_NAME]} map",
            update_interval=MAP_UPDATE_INTERVAL,
        )
        self._item = item
        self._session: TuyaAPISession | None = None
        self._layout: RoboVacMapLayout | None = None
        self._dock: tuple[int, int] | None = None
        self._record_id = 0
        self._path: list[tuple[float, float]] = []

    async def async_poll_route(self) -> None:
        """Add the newest robot position to the route and re-render the map."""
        if self._session is None or self._layout is None:
            return
        layout = self._layout
        try:
            self._dock, pose = await self.hass.async_add_executor_job(
                fetch_pose, self._session, self._item[CONF_ID], self._dock
            )
        except Exception as err:  # noqa: BLE001 - a missed poll must not break the camera
            _LOGGER.debug("Route poll failed: %s", err)
            return
        if pose is None:
            return
        if pose.record_id != self._record_id:
            # A new clean started: the previous route no longer applies.
            self._record_id = pose.record_id
            self._path = []
        point = (pose.x, pose.y)
        if self._path and self._path[-1] == point:
            return
        self._path.append(point)
        png: bytes = await self.hass.async_add_executor_job(
            _render_png, layout, self._path
        )
        self.async_set_updated_data(png)

    async def _async_update_data(self) -> bytes:
        dev_id = self._item[CONF_ID]
        if self._session is None:
            self._session = await self.hass.async_add_executor_job(
                _build_tuya_session, self._item
            )
        if self._session is None:
            raise UpdateFailed(
                "No Eufy account credentials configured for this vacuum "
                "(set username/password on the config entry to enable the map)"
            )
        try:
            layout = await self.hass.async_add_executor_job(
                fetch_and_decode, self._session, dev_id
            )
            self._layout = layout
            png: bytes = await self.hass.async_add_executor_job(
                _render_png, layout, self._path
            )
            return png
        except MapFetchError as err:
            raise UpdateFailed(str(err)) from err


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RoboVac map camera platform."""
    vacuums = config_entry.data[CONF_VACS]
    entities: list[Camera] = []
    for item in vacuums:
        item = vacuums[item]
        if not item.get(CONF_USERNAME) or not item.get(CONF_PASSWORD):
            continue
        coordinator = RoboVacMapCoordinator(hass, item)
        # Without this, coordinator.data stays None until the first
        # MAP_UPDATE_INTERVAL tick (or a manual homeassistant.update_entity
        # call) -- and the camera_proxy endpoint 500s on a None image in
        # the meantime, for up to 15 minutes after every restart.
        await coordinator.async_config_entry_first_refresh()
        entities.append(RoboVacMapCamera(coordinator, item))
    async_add_entities(entities)


class RoboVacMapCamera(CoordinatorEntity[RoboVacMapCoordinator], Camera):
    """Shows the vacuum's current cloud floor-plan map."""

    _attr_has_entity_name = True
    _attr_name = "Map"

    def __init__(self, coordinator: RoboVacMapCoordinator, item: dict[str, Any]) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._dev_id = item[CONF_ID]
        self._attr_unique_id = f"{self._dev_id}_map"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._dev_id)}, name=item[CONF_NAME],
        )

    async def async_added_to_hass(self) -> None:
        """Start the route poll that runs while the vacuum is moving."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_route_tick, ROUTE_POLL_INTERVAL
            )
        )

    def _vacuum_entity_id(self) -> str | None:
        """Find this device's vacuum entity in the entity registry."""
        registry = er.async_get(self.hass)
        for entry in er.async_entries_for_config_entry(
            registry, self.registry_entry.config_entry_id  # type: ignore[union-attr]
        ):
            if entry.domain == "vacuum" and self._dev_id in entry.unique_id:
                entity_id: str = entry.entity_id
                return entity_id
        return None

    async def _async_route_tick(self, _now: Any) -> None:
        entity_id = self._vacuum_entity_id()
        state = self.hass.states.get(entity_id) if entity_id else None
        if state is not None and state.state in _ROUTE_ACTIVE_STATES:
            await self.coordinator.async_poll_route()

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the most recently rendered map PNG, if any."""
        data: bytes | None = self.coordinator.data
        return data
