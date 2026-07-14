"""Behavioral coverage for the standalone T2080A / S1 Pro model."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.vacuum import VacuumActivity, VacuumEntityFeature
from homeassistant.const import CONF_MODEL

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.sensor import RobovacBatterySensor
from custom_components.robovac.vacuum import RoboVacEntity
from custom_components.robovac.vacuums import ROBOVAC_MODELS, resolve_model_code
from custom_components.robovac.vacuums.T2080 import T2080
from custom_components.robovac.vacuums.T2080A import T2080A
from custom_components.robovac.vacuums.base import RoboVacEntityFeature, RobovacCommand


def _t2080a_robovac() -> RoboVac:
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        return RoboVac(
            model_code="T2080A",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )


def test_t2080a_is_a_registered_standalone_model() -> None:
    assert ROBOVAC_MODELS["T2080"] is T2080
    assert ROBOVAC_MODELS["T2080A"] is T2080A
    assert T2080A is not T2080
    assert not issubclass(T2080A, T2080)


def test_t2080a_exposes_only_confirmed_features() -> None:
    expected = (
        VacuumEntityFeature.STATE
        | VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.FAN_SPEED
    )

    assert T2080A.homeassistant_features == expected
    assert T2080A.robovac_features == 0
    assert not expected & VacuumEntityFeature.RETURN_HOME
    assert not expected & VacuumEntityFeature.LOCATE
    assert not expected & VacuumEntityFeature.CLEAN_SPOT
    assert not expected & VacuumEntityFeature.SEND_COMMAND
    assert not expected & VacuumEntityFeature.MAP
    assert not expected & VacuumEntityFeature.CLEAN_AREA
    assert not T2080A.robovac_features & RoboVacEntityFeature.ROOM
    assert not T2080A.robovac_features & RoboVacEntityFeature.ZONE
    assert not T2080A.robovac_features & RoboVacEntityFeature.MAP


def test_t2080a_protocol_and_exact_command_surface() -> None:
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ) as init:
        robovac = RoboVac(
            model_code="T2080A",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

    assert init.call_args.kwargs["version"] == (3, 3)
    assert set(robovac.model_details.commands) == {
        RobovacCommand.START_PAUSE,
        RobovacCommand.STATUS,
        RobovacCommand.FAN_SPEED,
        RobovacCommand.BATTERY,
    }
    assert robovac.getDpsCodes() == {
        "START_PAUSE": "160",
        "STATUS": "6",
        "FAN_SPEED": "158",
        "BATTERY_LEVEL": "8",
    }


def test_t2080a_values_and_readback() -> None:
    robovac = _t2080a_robovac()

    assert robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False
    assert robovac.getFanSpeeds() == ["Quiet", "Standard", "Turbo", "Max"]
    assert [
        robovac.getRoboVacHumanReadableValue(RobovacCommand.STATUS, value)
        for value in (0, 1, 2, 5, 34)
    ] == ["Standby", "Cleaning", "Paused", "Returning", "Docked"]
    assert robovac.getRoboVacActivityMapping() == {
        "Standby": VacuumActivity.IDLE,
        "Cleaning": VacuumActivity.CLEANING,
        "Paused": VacuumActivity.PAUSED,
        "Returning": VacuumActivity.RETURNING,
        "Docked": VacuumActivity.DOCKED,
    }


def test_model_resolution_prefers_exact_code_then_legacy_prefix() -> None:
    assert resolve_model_code("T2080A") == "T2080A"
    assert resolve_model_code("T2080A product suffix") == "T2080A"
    assert resolve_model_code("T2278 product suffix") == "T2278"


def test_suffixed_t2080a_preserves_device_and_entity_model(
    mock_vacuum_data,
) -> None:
    configured_model = "T2080A product suffix"
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac = RoboVac(
            model_code=configured_model,
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        entity = RoboVacEntity({**mock_vacuum_data, CONF_MODEL: configured_model})

    assert robovac.model_code == "T2080A"
    assert robovac.model_details is T2080A
    assert entity.vacuum is not None
    assert entity.vacuum.model_code == "T2080A"
    assert entity.vacuum.model_details is T2080A


def test_entity_preserves_full_registered_model_code(mock_vacuum_data) -> None:
    robovac = _t2080a_robovac()
    data = {**mock_vacuum_data, CONF_MODEL: "T2080A"}

    with patch(
        "custom_components.robovac.vacuum.RoboVac", return_value=robovac
    ) as constructor:
        entity = RoboVacEntity(data)

    assert entity.vacuum is robovac
    assert entity.vacuum.model_code == "T2080A"
    assert constructor.call_args.kwargs["model_code"] == "T2080A"


@pytest.mark.asyncio
async def test_t2080a_command_payloads(mock_vacuum_data) -> None:
    robovac = _t2080a_robovac()
    robovac.async_set = AsyncMock(return_value=True)
    data = {**mock_vacuum_data, CONF_MODEL: "T2080A"}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=robovac):
        entity = RoboVacEntity(data)

    await entity.async_start()
    robovac.async_set.assert_awaited_once_with({"160": True})
    assert entity._attr_mode is None

    robovac.async_set.reset_mock()
    await entity.async_pause()
    robovac.async_set.assert_awaited_once_with({"160": False})

    robovac.async_set.reset_mock()
    await entity.async_stop()
    robovac.async_set.assert_awaited_once_with({"160": False})

    robovac.async_set.reset_mock()
    robovac._dps = {}
    await entity.async_set_fan_speed("Standard")
    robovac.async_set.assert_awaited_once_with({"158": "Standard"})


@pytest.mark.asyncio
async def test_t2080a_entity_reads_state_battery_and_fan_without_mode_leak(
    mock_vacuum_data,
) -> None:
    robovac = _t2080a_robovac()
    robovac._dps = {"6": 1, "8": 82, "158": "Turbo", "160": True}
    data = {**mock_vacuum_data, CONF_MODEL: "T2080A"}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=robovac):
        entity = RoboVacEntity(data)

    entity.update_entity_values()

    assert entity.activity == VacuumActivity.CLEANING
    assert entity.fan_speed == "Turbo"
    assert entity.get_dps_code("BATTERY") == "8"
    assert entity.tuyastatus[entity.get_dps_code("BATTERY")] == 82
    assert entity._attr_mode == ""

    battery = RobovacBatterySensor(data)
    battery.hass = MagicMock()
    battery.hass.data = {
        "robovac": {"vacuums": {data["id"]: entity}},
    }
    await battery.async_update()

    assert battery.native_value == 82
    assert battery.available is True
