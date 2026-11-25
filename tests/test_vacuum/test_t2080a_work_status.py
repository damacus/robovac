"""S1 Pro work-status regressions from local and cloud telemetry."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.vacuum import VacuumActivity
from homeassistant.const import CONF_MODEL

from custom_components.robovac.vacuum import RoboVacEntity
from custom_components.robovac.vacuums.T2080 import T2080
from custom_components.robovac.vacuums.T2080A import T2080A
from custom_components.robovac.vacuums.base import RobovacCommand


FAULT_STATUS = "EgoAEAIaAggBMgIIAToECAEQAQ=="
COMPLETED_STATUS = "BhADGgIIAQ=="
WASHING_STATUS = "BhAJOgIQAQ=="


@pytest.fixture
def s1_entity(mock_vacuum_data):
    """Create the real S1 Pro translator without opening a device connection."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        entity = RoboVacEntity({**mock_vacuum_data, CONF_MODEL: "T2080A"})
    entity.vacuum._dps = {"6": 29, "7": 26, "8": 100, "158": "Standard"}
    entity.vacuum.async_get = AsyncMock()
    entity.hass = MagicMock()

    async def run_job(function, *args):
        return function(*args)

    entity.hass.async_add_executor_job = AsyncMock(side_effect=run_job)
    return entity


@pytest.mark.parametrize("minutes", [0, 1, 2, 5, 29, 34])
def test_elapsed_minutes_do_not_override_completed_status(s1_entity, minutes):
    """DPS 6 is cleaning time and must not masquerade as an activity enum."""
    s1_entity.vacuum._dps.update({"6": minutes, "153": COMPLETED_STATUS})
    s1_entity.update_entity_values()
    assert s1_entity.activity == VacuumActivity.DOCKED


@pytest.mark.parametrize("raw", [FAULT_STATUS, "CAoAEAIyAggB"])
def test_multiple_fault_payloads_report_error(s1_entity, raw):
    """Both the observed EB14-era payload and the existing fault map to error."""
    s1_entity.vacuum._dps["153"] = raw
    s1_entity.update_entity_values()
    assert s1_entity.activity == VacuumActivity.ERROR


def test_error_recovers_to_mop_washing_after_cleaning(s1_entity):
    """Replaying the observed before/after values clears the generic error."""
    s1_entity.vacuum._dps["153"] = FAULT_STATUS
    s1_entity.update_entity_values()
    assert s1_entity.activity == VacuumActivity.ERROR
    s1_entity.vacuum._dps["153"] = WASHING_STATUS
    s1_entity.update_entity_values()
    assert s1_entity.activity == VacuumActivity.DOCKED


def test_unrecognized_status_stays_unknown(s1_entity):
    """An unrecognized payload is not evidence that a robot has faulted."""
    s1_entity.vacuum._dps["153"] = "unrecognized-payload"
    s1_entity.update_entity_values()
    assert s1_entity.activity is None


def test_s1_pro_status_alias_does_not_change_legacy_profile():
    """Extending T2080A must not mutate the shared T2080 command dictionary."""
    assert FAULT_STATUS not in T2080.commands[RobovacCommand.STATUS]["values"]
    assert T2080A.commands[RobovacCommand.STATUS]["values"] is not T2080.commands[RobovacCommand.STATUS]["values"]
    assert T2080A.activity_mapping is not T2080.activity_mapping


@pytest.mark.asyncio
async def test_cloud_status_is_read_when_local_response_omits_it(s1_entity):
    session = MagicMock()
    session.get_device.return_value = {"isOnline": True, "dps": {"153": FAULT_STATUS}}
    s1_entity._build_tuya_session_sync = MagicMock(return_value=session)

    await s1_entity.async_update()
    assert s1_entity.activity == VacuumActivity.ERROR
    await s1_entity.async_update()
    s1_entity._build_tuya_session_sync.assert_called_once_with()
    assert session.get_device.call_count == 2
    session.get_device.assert_called_with(str(s1_entity.unique_id))


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [
    {"isOnline": False, "dps": {"153": COMPLETED_STATUS}},
    {"isOnline": True, "dps": {}},
    {"isOnline": True, "dps": {"153": None}},
    {"isOnline": True, "dps": {"153": 29}},
])
async def test_failed_or_missing_cloud_status_does_not_retain_docked(s1_entity, response):
    s1_entity.vacuum._dps["153"] = COMPLETED_STATUS
    session = MagicMock()
    session.get_device.return_value = response
    s1_entity._build_tuya_session_sync = MagicMock(return_value=session)

    await s1_entity.async_update()
    assert s1_entity.activity is None


@pytest.mark.asyncio
async def test_cloud_exception_clears_stale_status_and_retries_session(s1_entity):
    s1_entity.vacuum._dps["153"] = COMPLETED_STATUS
    session = MagicMock()
    session.get_device.side_effect = TimeoutError("test timeout")
    s1_entity._build_tuya_session_sync = MagicMock(return_value=session)

    await s1_entity.async_update()
    assert s1_entity.activity is None
    assert s1_entity._s1_status_session is None

    session.get_device.side_effect = None
    session.get_device.return_value = {"isOnline": True, "dps": {"153": WASHING_STATUS}}
    await s1_entity.async_update()
    assert s1_entity.activity == VacuumActivity.DOCKED
    assert s1_entity._build_tuya_session_sync.call_count == 2


@pytest.mark.asyncio
async def test_other_models_do_not_poll_s1_cloud_status(mock_vacuum_data):
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        entity = RoboVacEntity(mock_vacuum_data)
    entity.vacuum._dps = {}
    entity.vacuum.async_get = AsyncMock()
    entity._build_tuya_session_sync = MagicMock()

    await entity.async_update()
    entity._build_tuya_session_sync.assert_not_called()
