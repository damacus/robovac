"""Tests to analyze DPS codes for all models."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import TuyaCodes
from custom_components.robovac.vacuums import ROBOVAC_MODELS


def test_analyze_model_dps_codes() -> None:
    """Analyze DPS codes for all models to determine which ones differ from defaults."""
    # Dictionary to store results
    model_dps_analysis = {}

    # Default codes from TuyaCodes
    default_codes = {
        "STATUS": TuyaCodes.STATUS,
        "BATTERY_LEVEL": TuyaCodes.BATTERY_LEVEL,
        "ERROR_CODE": TuyaCodes.ERROR_CODE,
        "MODE": TuyaCodes.MODE,
        "FAN_SPEED": TuyaCodes.FAN_SPEED,
        "CLEANING_AREA": TuyaCodes.CLEANING_AREA,
        "CLEANING_TIME": TuyaCodes.CLEANING_TIME,
        "AUTO_RETURN": TuyaCodes.AUTO_RETURN,
        "DO_NOT_DISTURB": TuyaCodes.DO_NOT_DISTURB,
        "BOOST_IQ": TuyaCodes.BOOST_IQ,
    }

    # Check each model
    for model_code in ROBOVAC_MODELS:
        # Initialize the vacuum with mock parameters
        with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
            vacuum = RoboVac(
                model_code=model_code,
                device_id="test_id",
                host="192.168.1.1",
                local_key="test_key",
            )

            # Get DPS codes for this model
            dps_codes = vacuum.getDpsCodes()

            # Check if any codes differ from defaults
            non_default_codes = {}
            for code_name, code_value in dps_codes.items():
                if code_name in default_codes and code_value != default_codes[code_name]:
                    non_default_codes[code_name] = code_value

            # Store result for this model
            model_dps_analysis[model_code] = {
                "has_non_default_codes": bool(non_default_codes),
                "non_default_codes": non_default_codes
            }

    # Print model analysis for debugging
    print("\nModel DPS Code Analysis:")
    print("========================")

    models_with_defaults = []
    models_with_non_defaults = []

    for model_code, analysis in model_dps_analysis.items():
        if analysis["has_non_default_codes"]:
            models_with_non_defaults.append(model_code)
            print(f"{model_code}: Has non-default codes")
            for name, value in analysis["non_default_codes"].items():
                default = default_codes.get(name, "N/A")
                print(f"  - {name}: {value} (default: {default})")
        else:
            models_with_defaults.append(model_code)

    print("\nModels using default codes:")
    for model in models_with_defaults:
        print(f"  - {model}")

    print("\nModels with non-default codes:")
    for model in models_with_non_defaults:
        print(f"  - {model}")

    # This doesn't assert anything, it's just an analysis
    # You can add assertions based on what you expect
    assert True
