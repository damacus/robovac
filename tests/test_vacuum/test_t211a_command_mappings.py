"""Tests for T211A (Omni C28) command mappings and registration."""

from unittest.mock import patch

import pytest
from homeassistant.components.vacuum import VacuumEntityFeature

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums import ROBOVAC_MODELS
from custom_components.robovac.vacuums.T2320 import T2320
from custom_components.robovac.vacuums.base import RoboVacEntityFeature, RobovacCommand


def test_t211a_registered_in_robovac_models() -> None:
    """Test T211A is registered in ROBOVAC_MODELS."""
    assert ROBOVAC_MODELS["T211A"].commands == T2320.commands


@pytest.fixture
def mock_t211a_robovac() -> RoboVac:
    """Create a mock T211A RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T211A",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t211a_ha_features_match_station_omni_profile(
    mock_t211a_robovac: RoboVac,
) -> None:
    """Test T211A exposes the HA controls used by station-capable models."""
    assert mock_t211a_robovac.getHomeAssistantFeatures() == (
        VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )


def test_t211a_robovac_features_match_station_omni_profile(
    mock_t211a_robovac: RoboVac,
) -> None:
    """Test T211A exposes local feature flags implemented for Omni station models."""
    assert mock_t211a_robovac.getRoboVacFeatures() == (
        RoboVacEntityFeature.DO_NOT_DISTURB | RoboVacEntityFeature.BOOST_IQ
    )


def test_t211a_mode_command_values(mock_t211a_robovac: RoboVac) -> None:
    """Test T211A MODE command uses station-aware protobuf values."""
    assert (
        mock_t211a_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto")
        == "BBoCCAE="
    )
    assert (
        mock_t211a_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause")
        == "AggN"
    )


def test_t211a_model_has_omni_station_commands(mock_t211a_robovac: RoboVac) -> None:
    """Test T211A has the local command surface for Omni station features."""
    commands = mock_t211a_robovac.model_details.commands

    assert RobovacCommand.START_PAUSE in commands
    assert RobovacCommand.MODE in commands
    assert RobovacCommand.STATUS in commands
    assert RobovacCommand.RETURN_HOME in commands
    assert RobovacCommand.CLEAN_PARAM in commands
    assert RobovacCommand.FAN_SPEED in commands
    assert RobovacCommand.LOCATE in commands
    assert RobovacCommand.BATTERY in commands
    assert RobovacCommand.CONSUMABLES in commands
    assert RobovacCommand.ERROR in commands
    assert RobovacCommand.ACTIVE_ERRORS in commands


def test_t211a_dps_codes_match_local_station_profile(
    mock_t211a_robovac: RoboVac,
) -> None:
    """Test T211A uses DPS codes for local station/mop feature support."""
    dps_codes = mock_t211a_robovac.getDpsCodes()

    assert dps_codes["START_PAUSE"] == "2"
    assert dps_codes["MODE"] == "152"
    assert dps_codes["STATUS"] == "173"
    assert dps_codes["RETURN_HOME"] == "153"
    assert dps_codes["CLEAN_PARAM"] == "154"
    assert dps_codes["FAN_SPEED"] == "158"
    assert dps_codes["LOCATE"] == "160"
    assert dps_codes["BATTERY_LEVEL"] == "163"
    assert dps_codes["CONSUMABLES"] == "168"
    assert dps_codes["ERROR_CODE"] == "177"
    assert dps_codes["ACTIVE_ERRORS"] == "178"
    assert dps_codes["ROOM_META"] == "165"


def test_t211a_exposes_config_entity_flags() -> None:
    """Test T211A opts into local clean type, mop level, and room controls."""
    model = ROBOVAC_MODELS["T211A"]

    assert getattr(model, "expose_config_entities") is True
    assert getattr(model, "clean_type_select_keys") == (
        "sweep_only",
        "mop_only",
        "sweep_and_mop",
    )
    assert getattr(model, "expose_room_select") is True
    assert getattr(model, "consumable_sensor_keys") == (
        "side_brush",
        "rolling_brush",
        "filter_mesh",
        "scrape",
        "sensor",
        "mop",
    )
