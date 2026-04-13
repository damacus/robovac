"""Tests for the RoboVac class."""

import pytest
from unittest.mock import patch

from homeassistant.components.vacuum import VacuumEntityFeature

from custom_components.robovac.robovac import (
    RoboVac,
    ModelNotSupportedException,
)
from custom_components.robovac.vacuums.base import RoboVacEntityFeature


def test_init_unsupported_model() -> None:
    """Test initialization with unsupported model raises exception."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        with pytest.raises(ModelNotSupportedException):
            RoboVac(
                model_code="UNSUPPORTED",
                device_id="test_id",
                host="192.168.1.100",
                local_key="test_key",
                timeout=30,
                ping_interval=15,
                update_entity_state=None,
            )


def test_get_home_assistant_features() -> None:
    """Test getHomeAssistantFeatures returns correct features for different models."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac_15c = RoboVac(
            model_code="T2118",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        expected_features = (
            VacuumEntityFeature.CLEAN_SPOT
            | VacuumEntityFeature.FAN_SPEED
            | VacuumEntityFeature.LOCATE
            | VacuumEntityFeature.PAUSE
            | VacuumEntityFeature.RETURN_HOME
            | VacuumEntityFeature.SEND_COMMAND
            | VacuumEntityFeature.START
            | VacuumEntityFeature.STATE
            | VacuumEntityFeature.STOP
        )

        assert robovac_15c.getHomeAssistantFeatures() == expected_features

        robovac_l70 = RoboVac(
            model_code="T2190",  # L70 model (has map)
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        expected_features_with_map = expected_features | VacuumEntityFeature.MAP

        assert robovac_l70.getHomeAssistantFeatures() == expected_features_with_map


def test_get_robovac_features() -> None:
    """Test getRoboVacFeatures returns correct features for different models."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac_15c = RoboVac(
            model_code="T2118",  # 15C model
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        expected_c_features = (
            RoboVacEntityFeature.EDGE | RoboVacEntityFeature.SMALL_ROOM
        )

        assert robovac_15c.getRoboVacFeatures() == expected_c_features

        robovac_g30 = RoboVac(
            model_code="T2250",  # G30 model
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        expected_g_features = (
            RoboVacEntityFeature.CLEANING_TIME
            | RoboVacEntityFeature.CLEANING_AREA
            | RoboVacEntityFeature.DO_NOT_DISTURB
            | RoboVacEntityFeature.AUTO_RETURN
        )

        assert robovac_g30.getRoboVacFeatures() == expected_g_features

        robovac_l70 = RoboVac(
            model_code="T2190",  # L70 model
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        expected_l_features = (
            RoboVacEntityFeature.CLEANING_TIME
            | RoboVacEntityFeature.CLEANING_AREA
            | RoboVacEntityFeature.DO_NOT_DISTURB
            | RoboVacEntityFeature.AUTO_RETURN
            | RoboVacEntityFeature.ROOM
            | RoboVacEntityFeature.ZONE
            | RoboVacEntityFeature.BOOST_IQ
            | RoboVacEntityFeature.MAP
            | RoboVacEntityFeature.CONSUMABLES
        )

        assert robovac_l70.getRoboVacFeatures() == expected_l_features


def test_get_fan_speeds() -> None:
    """Test getFanSpeeds returns correct fan speeds for different series.

    getFanSpeeds() returns title-cased keys as display names for the UI.
    This ensures user-friendly names are shown regardless of device values.
    """
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        test_cases = [
            # Model code, expected fan speeds (title-cased keys), and the dictionary to mock
            (
                "T2118",
                ["No Suction", "Standard", "Boost Iq", "Max"],
                {
                    "no_suction": "No_suction",
                    "standard": "Standard",
                    "boost_iq": "Boost_IQ",
                    "max": "Max",
                }
            ),
            (
                "T2250",
                ["Standard", "Turbo", "Max", "Boost Iq"],
                {
                    "standard": "Standard",
                    "turbo": "Turbo",
                    "max": "Max",
                    "boost_iq": "Boost_IQ",
                }
            ),
            (
                "T2190",
                ["Quiet", "Standard", "Turbo", "Max"],
                {
                    "quiet": "Quiet",
                    "standard": "Standard",
                    "turbo": "Turbo",
                    "max": "Max",
                }
            ),
            (
                "T2261",
                ["Pure", "Standard", "Turbo", "Max"],
                {
                    "pure": "Pure",
                    "standard": "Standard",
                    "turbo": "Turbo",
                    "max": "Max",
                }
            ),
            (
                "T2267",
                ["Quiet", "Standard", "Turbo", "Max"],
                {
                    "quiet": "Quiet",
                    "standard": "Standard",
                    "turbo": "Turbo",
                    "max": "Max",
                }
            ),
        ]

        for model_code, expected_speeds, fan_speed_dict in test_cases:
            robovac = RoboVac(
                model_code=model_code,
                device_id="test_id",
                host="192.168.1.100",
                local_key="test_key",
            )

            # Mock the _get_command_values method to return our test dictionary
            with patch.object(
                robovac, "_get_command_values", return_value=fan_speed_dict
            ):
                assert robovac.getFanSpeeds() == expected_speeds


def test_get_command_values_nonexistent_command() -> None:
    """Test _get_command_values with non-existent command returns None."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac = RoboVac(
            model_code="T2118",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        # Test with non-existent command name
        values = robovac._get_command_values("NONEXISTENT_COMMAND")
        assert values is None


def test_get_command_values_no_values_dict() -> None:
    """Test _get_command_values when command has no values dict."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac = RoboVac(
            model_code="T2118",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        # Add a command without values
        robovac.model_details.commands["TEST_CMD"] = {"code": 999}
        values = robovac._get_command_values("TEST_CMD")
        assert values is None


def test_get_fan_speeds_no_fan_command() -> None:
    """Test getFanSpeeds returns empty list when model doesn't support fan speed."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac = RoboVac(
            model_code="T2118",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        # Mock _get_command_values to return None (no fan speed support)
        with patch.object(robovac, "_get_command_values", return_value=None):
            fan_speeds = robovac.getFanSpeeds()
            assert fan_speeds == []


def test_get_robovac_command_value_with_decode_dps() -> None:
    """Test getRoboVacCommandValue with proto-based decode_dps."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac = RoboVac(
            model_code="T2277",  # T2277 has decode_dps
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        # T2277 should have decode_dps method
        assert hasattr(robovac.model_details, 'decode_dps')


def test_get_supported_commands() -> None:
    """Test getSupportedCommands returns list of supported commands."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac = RoboVac(
            model_code="T2118",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        commands = robovac.getSupportedCommands()
        assert isinstance(commands, list)
        assert len(commands) > 0
        assert "MODE" in commands or "BATTERY" in commands  # Should have at least some common commands


def test_get_dps_codes() -> None:
    """Test getDpsCodes returns dict of DPS codes."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        robovac = RoboVac(
            model_code="T2118",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        dps_codes = robovac.getDpsCodes()
        assert isinstance(dps_codes, dict)
        assert len(dps_codes) > 0


