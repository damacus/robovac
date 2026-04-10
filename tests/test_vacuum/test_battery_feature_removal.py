"""Tests for battery feature removal from vacuum models.

This test suite validates that VacuumEntityFeature.BATTERY has been removed
from all vacuum models while maintaining backward compatibility with battery
command mappings and battery sensor functionality.
"""

import pytest
from homeassistant.components.vacuum import VacuumEntityFeature

from custom_components.robovac.vacuums import ROBOVAC_MODELS
from custom_components.robovac.vacuums.base import RobovacCommand


class TestBatteryFeatureRemoval:
    """Test suite for battery feature removal."""

    def test_no_vacuum_model_has_battery_feature(self) -> None:
        """Test that VacuumEntityFeature.BATTERY is not in any model's features.

        This test ensures all vacuum models have been updated to remove the
        deprecated BATTERY feature in preparation for Home Assistant 2026.8.
        """
        for model_code, model_class in ROBOVAC_MODELS.items():
            model_instance = model_class()
            features = model_instance.homeassistant_features

            # BATTERY feature should NOT be present
            assert not (
                features & VacuumEntityFeature.BATTERY
            ), f"{model_code} still has VacuumEntityFeature.BATTERY"

    def test_battery_command_mappings_still_exist(self) -> None:
        """Test that RobovacCommand.BATTERY still exists in model commands.

        Battery command mappings should be preserved for backward compatibility
        even though the feature flag is removed. Battery reporting continues
        via the dedicated battery sensor component.
        """
        models_with_battery_command = 0

        for model_code, model_class in ROBOVAC_MODELS.items():
            model_instance = model_class()
            commands = model_instance.commands

            # Check if model has BATTERY command
            if RobovacCommand.BATTERY in commands:
                models_with_battery_command += 1
                # Verify the command has a valid code
                battery_command = commands[RobovacCommand.BATTERY]
                assert "code" in battery_command, (
                    f"{model_code} BATTERY command missing 'code' field"
                )
                assert isinstance(
                    battery_command["code"], int
                ), f"{model_code} BATTERY command code is not an integer"

        # At least some models should have battery commands
        assert (
            models_with_battery_command > 0
        ), "No models have BATTERY command mappings"

    def test_battery_feature_not_combined_with_other_features(self) -> None:
        """Test that BATTERY feature is not combined with other features.

        Verify that no model has BATTERY feature combined with other features
        using bitwise OR operations.
        """
        for model_code, model_class in ROBOVAC_MODELS.items():
            model_instance = model_class()
            features = model_instance.homeassistant_features

            # Check if BATTERY bit is set
            battery_bit_set = bool(features & VacuumEntityFeature.BATTERY)
            assert (
                not battery_bit_set
            ), f"{model_code} has BATTERY feature in homeassistant_features"

    def test_other_features_preserved(self) -> None:
        """Test that other features are preserved after battery removal.

        Ensure that removing BATTERY feature didn't accidentally remove
        other important features like FAN_SPEED, LOCATE, etc.
        """
        for model_code, model_class in ROBOVAC_MODELS.items():
            model_instance = model_class()
            features = model_instance.homeassistant_features

            # Check that at least some expected features are present
            has_expected_features = bool(features & (
                VacuumEntityFeature.START
                | VacuumEntityFeature.STOP
                | VacuumEntityFeature.STATE
            ))

            assert (
                has_expected_features
            ), f"{model_code} missing basic vacuum features"

    def test_all_models_have_features_defined(self) -> None:
        """Test that all models have homeassistant_features defined.

        Verify that every model has a non-zero homeassistant_features value.
        """
        for model_code, model_class in ROBOVAC_MODELS.items():
            model_instance = model_class()
            features = model_instance.homeassistant_features

            assert (
                features > 0
            ), f"{model_code} has no homeassistant_features defined"

    def test_battery_feature_flag_value(self) -> None:
        """Test that we understand the BATTERY feature flag value.

        This test documents the BATTERY feature flag value for reference.
        """
        # VacuumEntityFeature.BATTERY should have a specific bit value
        battery_feature = VacuumEntityFeature.BATTERY
        assert battery_feature > 0, "BATTERY feature should have a positive value"
        assert isinstance(
            battery_feature, int
        ), "BATTERY feature should be an integer"
