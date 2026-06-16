"""Regression tests for legacy DPS 2 start/pause command mappings."""

from importlib import import_module
from typing import Any
from unittest.mock import patch

import pytest


LEGACY_DPS2_MODELS = (
    "T1250",
    "T2080",
    "T2103",
    "T2117",
    "T2118",
    "T2119",
    "T2120",
    "T2123",
    "T2128",
    "T2130",
    "T2132",
    "T2150",
    "T2181",
    "T2190",
    "T2192",
    "T2193",
    "T2194",
    "T2210",
    "T2212",
    "T2250",
    "T2251",
    "T2252",
    "T2253",
    "T2254",
    "T2255",
    "T2259",
    "T2261",
    "T2262",
    "T2268",
    "T2270",
    "T2272",
    "T2273",
    "T2276",
    "T2320",
    "T2351",
)


def _robovac_context() -> tuple[Any, Any, Any]:
    """Return current robovac modules after tests that reload them."""
    robovac_module = import_module("custom_components.robovac.robovac")
    vacuums_module = import_module("custom_components.robovac.vacuums")
    base_module = import_module("custom_components.robovac.vacuums.base")
    return robovac_module.RoboVac, vacuums_module.ROBOVAC_MODELS, base_module.RobovacCommand


@pytest.mark.parametrize("model_code", LEGACY_DPS2_MODELS)
def test_legacy_dps2_start_pause_maps_to_booleans(model_code: str) -> None:
    """Legacy DPS 2 start/pause controls must send booleans, not strings."""
    robo_vac, _, robovac_command = _robovac_context()

    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = robo_vac(
            model_code=model_code,
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

    assert robovac.getRoboVacCommandValue(robovac_command.START_PAUSE, "start") is True
    assert robovac.getRoboVacCommandValue(robovac_command.START_PAUSE, "pause") is False


def _command_code(command: Any) -> str | None:
    """Return the command DPS code as a string."""
    if isinstance(command, dict) and "code" in command:
        return str(command["code"])
    if not isinstance(command, dict):
        return str(command)
    return None


def test_no_model_has_bare_dps2_start_pause_mapping() -> None:
    """Guard against DPS 2 models omitting explicit boolean start/pause values."""
    _, robovac_models, robovac_command = _robovac_context()
    bare_models = []

    for model_code, model_details in robovac_models.items():
        command = model_details.commands.get(robovac_command.START_PAUSE)
        if _command_code(command) != "2":
            continue

        values = command.get("values") if isinstance(command, dict) else None
        if not isinstance(values, dict) or values.get("start") is not True or values.get("pause") is not False:
            bare_models.append(model_code)

    assert bare_models == []


def test_legacy_status_maps_recharge_value() -> None:
    """Guard legacy status maps against missing Recharge values."""
    _, robovac_models, robovac_command = _robovac_context()
    missing_recharge = []
    legacy_status_values = {"Charging", "completed", "Running", "standby"}

    for model_code, model_details in robovac_models.items():
        command = model_details.commands.get(robovac_command.STATUS)
        if not isinstance(command, dict) or _command_code(command) != "15":
            continue

        values = command.get("values")
        if not isinstance(values, dict) or not legacy_status_values <= set(values):
            continue

        if values.get("Recharge") != "Returning to Dock":
            missing_recharge.append(model_code)

    assert missing_recharge == []
