"""Reported status transitions on the X8 Hybrid and LR30 Hybrid+."""

from unittest.mock import patch

import pytest
from homeassistant.components.vacuum import VacuumActivity
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
)

from custom_components.robovac.vacuum import RoboVacEntity


@pytest.mark.parametrize("model", ["T2181", "T2261"])
def test_translated_status_transitions(model: str) -> None:
    """Use the actual model translation of DPS 15, not raw device strings."""
    data = {
        CONF_NAME: "Test vacuum",
        CONF_ID: "test-vacuum",
        CONF_MODEL: model,
        CONF_IP_ADDRESS: "192.0.2.1",
        CONF_ACCESS_TOKEN: "test-key",
        CONF_DESCRIPTION: "Test vacuum",
        CONF_MAC: "00:00:00:00:00:00",
    }
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        entity = RoboVacEntity(data)
    assert entity.vacuum is not None

    for raw_status, running, expected in (
        ("Running", True, VacuumActivity.CLEANING),
        ("standby", False, VacuumActivity.PAUSED),
        ("Recharge", False, VacuumActivity.RETURNING),
        ("Charging", False, VacuumActivity.DOCKED),
        ("completed", False, VacuumActivity.DOCKED),
    ):
        entity.vacuum._dps = {"2": running, "5": "auto", "15": raw_status}
        entity.update_entity_values()
        assert entity.activity == expected, (model, raw_status, entity.tuya_state)


@pytest.mark.parametrize("model", ["T2181", "T2261"])
def test_standby_without_pause_signal_remains_idle(model: str) -> None:
    data = {
        CONF_NAME: "Test vacuum",
        CONF_ID: "test-vacuum",
        CONF_MODEL: model,
        CONF_IP_ADDRESS: "192.0.2.1",
        CONF_ACCESS_TOKEN: "test-key",
        CONF_DESCRIPTION: "Test vacuum",
        CONF_MAC: "00:00:00:00:00:00",
    }
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        entity = RoboVacEntity(data)
    assert entity.vacuum is not None
    entity.vacuum._dps = {"5": "auto", "15": "standby"}
    entity.update_entity_values()
    assert entity.activity == VacuumActivity.IDLE
