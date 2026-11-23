"""Exercise the X8 Pro SES entities through Home Assistant."""

from datetime import timedelta
from unittest.mock import patch

from homeassistant.const import CONF_ACCESS_TOKEN, CONF_ID, CONF_MODEL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.robovac.const import CONF_VACS, DOMAIN
from custom_components.robovac.robovac import RoboVac


async def test_t2276_native_entities(
    hass: HomeAssistant, mock_vacuum_data: dict
) -> None:
    """Read and control the native entities through their Home Assistant services."""
    robot_data = {
        **mock_vacuum_data,
        CONF_MODEL: "T2276",
        CONF_ACCESS_TOKEN: "0123456789abcdef",
    }
    assert await async_setup_component(hass, "homeassistant", {})
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_VACS: {robot_data[CONF_ID]: robot_data}}
    )
    entry.add_to_hass(hass)
    status: dict = {}

    async def read_status(robot: RoboVac) -> None:
        robot._dps = status.copy()

    async def write_setting(robot: RoboVac, payload: dict) -> None:
        robot._dps.update(payload)
        status.update(payload)

    with (
        patch("custom_components.robovac.TuyaLocalDiscovery.start"),
        # The test environment installs HA core without the camera platform extras.
        patch(
            "custom_components.robovac.PLATFORMS",
            [Platform.VACUUM, Platform.SENSOR, Platform.SELECT, Platform.SWITCH],
        ),
        patch.object(RoboVac, "process_queue"),
        patch.object(RoboVac, "async_get", autospec=True, side_effect=read_status),
        patch.object(RoboVac, "async_set", autospec=True, side_effect=write_setting) as send,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.test_robovac_water_level") is None

        readings = {
            "sensor.test_robovac_cleaning_area": ("84", "m²"),
            "sensor.test_robovac_cleaning_time": ("4260", "s"),
            "sensor.test_robovac_volume": ("70", "%"),
            "sensor.test_robovac_cleaning_type": ("Sweep", None),
            "select.test_robovac_water_level": ("Medium", None),
            "select.test_robovac_fan_speed": ("Turbo", None),
            "switch.test_robovac_do_not_disturb": ("off", None),
            "switch.test_robovac_boostiq": ("on", None),
        }
        now = dt_util.utcnow()
        async_fire_time_changed(hass, now + timedelta(minutes=1))
        await hass.async_block_till_done()
        assert hass.states.get("sensor.test_robovac_cleaning_area").state == "unavailable"

        status.update(
            {
                "15": "Charging",
                "102": "Turbo",
                "105": "Mid",
                "107": False,
                "109": "4260",
                "110": 84,
                "111": 70,
                "113": "Sweep",
                "118": True,
            }
        )
        # The vacuum and auxiliary platforms can poll in either order.
        for minutes in (2, 3):
            async_fire_time_changed(hass, now + timedelta(minutes=minutes))
            await hass.async_block_till_done()

        for entity_id, (expected_state, unit) in readings.items():
            state = hass.states.get(entity_id)
            assert state.state == expected_state
            assert state.attributes.get("unit_of_measurement") == unit

        controls = (
            (
                "select.test_robovac_water_level",
                "select_option",
                {"option": "High"},
                {"105": "High"},
                "High",
            ),
            (
                "select.test_robovac_fan_speed",
                "select_option",
                {"option": "Pure"},
                {"102": "Quiet"},
                "Pure",
            ),
            ("switch.test_robovac_do_not_disturb", "turn_on", {}, {"107": True}, "on"),
            ("switch.test_robovac_boostiq", "turn_off", {}, {"118": False}, "off"),
        )
        for entity_id, service, data, payload, expected_state in controls:
            await hass.services.async_call(
                entity_id.split(".")[0], service, {"entity_id": entity_id, **data}, blocking=True
            )
            assert send.call_args.args[1] == payload
            assert hass.states.get(entity_id).state == expected_state

        async_fire_time_changed(hass, now + timedelta(minutes=4))
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(entry.entry_id)
