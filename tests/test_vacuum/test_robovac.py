"""Tests for the RoboVac class."""

import pytest
from unittest.mock import patch, MagicMock

from homeassistant.components.vacuum import VacuumEntityFeature

from custom_components.robovac.robovac import (
    RoboVac,
    ModelNotSupportedException,
)
from custom_components.robovac.vacuums.base import RoboVacEntityFeature


def test_init_unsupported_model():
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


def test_get_home_assistant_features():
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
            VacuumEntityFeature.BATTERY
            | VacuumEntityFeature.CLEAN_SPOT
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


def test_get_robovac_features():
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


def test_get_fan_speeds():
    """Test getFanSpeeds returns correct fan speeds for different series."""
    with patch(
        "custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None
    ):
        test_cases = [
            ("T2118", ["No_suction", "Standard", "Boost_IQ", "Max"]),
            ("T2250", ["Standard", "Turbo", "Max", "Boost_IQ"]),
            ("T2190", ["Quiet", "Standard", "Turbo", "Max"]),
            ("T2261", ["Pure", "Standard", "Turbo", "Max"]),
        ]

        for model_code, expected_speeds in test_cases:
            robovac = RoboVac(
                model_code=model_code,
                device_id="test_id",
                host="192.168.1.100",
                local_key="test_key",
            )

            assert robovac.getFanSpeeds() == expected_speeds
