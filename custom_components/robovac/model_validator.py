"""Model validation and identification utilities for Eufy RoboVac integration."""

import logging
from typing import Dict, List, Optional, Tuple
from .vacuums import ROBOVAC_MODELS

_LOGGER = logging.getLogger(__name__)

# Model series mapping based on common patterns
MODEL_SERIES = {
    "C": {
        "name": "C Series",
        "description": "Entry-level models with basic cleaning features",
        "examples": ["T2103", "T2117", "T2118", "T2119", "T2120", "T2123"],
        "features": ["Basic cleaning", "Remote control", "Auto-return"],
    },
    "G": {
        "name": "G Series",
        "description": "Mid-range models with enhanced navigation",
        "examples": ["T2250", "T2251", "T2252", "T2253", "T2254", "T2255"],
        "features": ["BoostIQ", "Drop-sensing", "Boundary strips"],
    },
    "L": {
        "name": "L Series",
        "description": "Advanced models with laser navigation and mapping",
        "examples": ["T2267", "T2268", "T2275", "T2276", "T2277"],
        "features": ["Laser navigation", "App mapping", "Room cleaning", "No-go zones"],
    },
    "X": {
        "name": "X Series",
        "description": "Premium models with advanced features and self-emptying",
        "examples": ["T2276", "T2278", "T2320"],
        "features": ["Self-emptying", "Advanced mapping", "Multi-floor maps", "Voice control"],
    },
}

# Common model name mappings
MODEL_NAME_MAPPINGS = {
    "T2103": "RoboVac 11S",
    "T2117": "RoboVac 15C",
    "T2118": "RoboVac 15C Max",
    "T2119": "RoboVac 12",
    "T2120": "RoboVac 25C",
    "T2123": "RoboVac 30C",
    "T2250": "RoboVac G10 Hybrid",
    "T2251": "RoboVac G15",
    "T2252": "RoboVac G20",
    "T2253": "RoboVac G20 Hybrid",
    "T2254": "RoboVac G30",
    "T2255": "RoboVac G30 Edge",
    "T2267": "RoboVac L60",
    "T2268": "RoboVac L60 Hybrid",
    "T2275": "RoboVac L50 SES",
    "T2276": "RoboVac X8 Pro SES",
    "T2277": "RoboVac L60 SES",
    "T2278": "RoboVac X9 Pro",
    "T2320": "RoboVac X10 Pro Omni",
}


def get_supported_models() -> List[str]:
    """Get list of all supported model codes.

    Returns:
        List of supported model codes (e.g., ['T2103', 'T2117', ...])
    """
    return sorted(ROBOVAC_MODELS.keys())


def is_model_supported(model_code: str) -> bool:
    """Check if a model code is supported.

    Args:
        model_code: The model code to check (e.g., 'T2277')

    Returns:
        True if the model is supported, False otherwise
    """
    return model_code in ROBOVAC_MODELS


def get_model_info(model_code: str) -> Optional[Dict[str, str]]:
    """Get detailed information about a model.

    Args:
        model_code: The model code to look up

    Returns:
        Dictionary with model information or None if not found
    """
    if not is_model_supported(model_code):
        return None

    series = get_model_series(model_code)
    series_info = MODEL_SERIES.get(series, {})

    return {
        "model_code": model_code,
        "friendly_name": MODEL_NAME_MAPPINGS.get(model_code, f"RoboVac {model_code}"),
        "series": series,
        "series_name": series_info.get("name", "Unknown Series"),
        "description": series_info.get("description", ""),
        "features": series_info.get("features", []),
        "supported": True,
    }


def get_model_series(model_code: str) -> str:
    """Determine the series (C, G, L, X) for a given model code.

    Args:
        model_code: The model code to analyze

    Returns:
        The series letter or 'Unknown' if cannot be determined
    """
    # Extract numeric part for pattern matching
    if len(model_code) >= 5 and model_code.startswith('T'):
        numeric_part = model_code[1:]

        # C Series: T2103-T2130 range
        if numeric_part.startswith('21'):
            return "C"
        # G Series: T2250-T2259 range
        elif numeric_part.startswith('225'):
            return "G"
        # L Series: T2260-T2279 range (with some exceptions)
        elif numeric_part.startswith('226') or numeric_part.startswith('227'):
            return "L"
        # X Series: T2280+ and some specific models
        elif (numeric_part.startswith('228')
              or numeric_part.startswith('229')
              or numeric_part.startswith('23')
              or model_code in ['T2276', 'T2278']):  # Special cases
            return "X"

    return "Unknown"


def find_similar_models(model_code: str) -> List[Tuple[str, str]]:
    """Find similar supported models for an unsupported model.

    Args:
        model_code: The unsupported model code

    Returns:
        List of tuples (model_code, reason) for similar models
    """
    similar_models = []

    if not model_code.startswith('T') or len(model_code) < 5:
        return similar_models

    # Find models in the same series
    target_series = get_model_series(model_code)
    if target_series != "Unknown":
        series_models = [m for m in get_supported_models()
                         if get_model_series(m) == target_series]
        for model in series_models[:3]:  # Limit to 3 suggestions
            similar_models.append((model, f"Same {target_series} series"))

    # Find numerically close models
    try:
        target_num = int(model_code[1:])
        for supported_model in get_supported_models():
            supported_num = int(supported_model[1:])
            if abs(target_num - supported_num) <= 10:  # Within 10 numbers
                if (supported_model, f"Same {target_series} series") not in similar_models:
                    similar_models.append((supported_model, "Numerically similar"))
                if len(similar_models) >= 5:  # Limit total suggestions
                    break
    except ValueError:
        pass

    return similar_models


def validate_and_suggest(model_code: str) -> Dict[str, any]:
    """Validate a model and provide suggestions if unsupported.

    Args:
        model_code: The model code to validate

    Returns:
        Dictionary with validation results and suggestions
    """
    result = {
        "model_code": model_code,
        "is_supported": False,
        "model_info": None,
        "suggestions": [],
        "message": "",
    }

    if not model_code:
        result["message"] = "Please provide a model code (e.g., T2277)"
        return result

    # Clean up the input
    model_code = model_code.strip().upper()

    if is_model_supported(model_code):
        result["is_supported"] = True
        result["model_info"] = get_model_info(model_code)
        result["message"] = f"✅ Model {model_code} is fully supported!"
    else:
        similar_models = find_similar_models(model_code)
        result["suggestions"] = similar_models

        if similar_models:
            result["message"] = (
                f"❌ Model {model_code} is not supported yet. "
                f"However, these similar models are supported and might work:"
            )
        else:
            result["message"] = (
                f"❌ Model {model_code} is not supported yet. "
                f"Please create an issue on GitHub to request support."
            )

    return result


def get_troubleshooting_info(model_code: str) -> Dict[str, str]:
    """Get troubleshooting information for a specific model.

    Args:
        model_code: The model code to get troubleshooting info for

    Returns:
        Dictionary with troubleshooting steps and common issues
    """
    series = get_model_series(model_code)

    common_steps = [
        "1. Ensure your vacuum is connected to the same network as Home Assistant",
        "2. Check that the vacuum's IP address is correctly configured",
        "3. Verify the vacuum is powered on and not in sleep mode",
        "4. Try restarting both the vacuum and Home Assistant",
    ]

    series_specific = {
        "C": [
            "5. C Series models may need manual IP configuration",
            "6. Check if your router supports 2.4GHz WiFi (required for C Series)",
        ],
        "G": [
            "5. G Series models support both 2.4GHz and 5GHz WiFi",
            "6. Try using the Eufy app to verify connectivity first",
        ],
        "L": [
            "5. L Series models require strong WiFi signal for mapping features",
            "6. Ensure the vacuum has completed initial mapping if using room cleaning",
        ],
        "X": [
            "5. X Series models may need firmware updates for full compatibility",
            "6. Check if self-emptying station is properly connected (if applicable)",
        ],
    }

    all_steps = common_steps + series_specific.get(series, [])

    return {
        "model_code": model_code,
        "series": series,
        "troubleshooting_steps": all_steps,
        "documentation_url": "https://github.com/damacus/robovac#debugging",
    }
