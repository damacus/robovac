#!/usr/bin/env python3
"""
Analyze all robovac models to identify which ones use non-default DPS codes.
This script helps identify models that need custom DPS code mapping.
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import TuyaCodes
from custom_components.robovac.vacuums import ROBOVAC_MODELS


def analyze_model_dps_codes() -> None:
    """Analyze DPS codes for all models to determine which ones differ from defaults."""
    # Dictionary to store results
    model_dps_analysis = {}

    # Default codes from TuyaCodes
    default_codes = {
        "STATE": TuyaCodes.STATUS,
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
    for model_code in sorted(ROBOVAC_MODELS):
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

    # Print model analysis
    print("\nModel DPS Code Analysis:")
    print("========================")

    models_with_defaults = []
    models_with_non_defaults = []

    for model_code in sorted(model_dps_analysis.keys()):
        analysis = model_dps_analysis[model_code]
        if analysis["has_non_default_codes"]:
            models_with_non_defaults.append(model_code)
            print(f"\n{model_code}: Has non-default codes")
            for name, value in analysis["non_default_codes"].items():
                default = default_codes.get(name, "N/A")
                print(f"  - {name}: {value} (default: {default})")
        else:
            models_with_defaults.append(model_code)

    print("\nModels using default codes:")
    for model in sorted(models_with_defaults):
        print(f"  - {model}")

    print("\nModels with non-default codes:")
    for model in sorted(models_with_non_defaults):
        print(f"  - {model}")


if __name__ == "__main__":
    analyze_model_dps_codes()
