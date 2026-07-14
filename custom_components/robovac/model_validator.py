"""Model validation and series detection for RoboVac devices.

This module provides utilities for validating RoboVac model codes,
detecting model series (C, G, L, X), and providing troubleshooting
guidance for unsupported models.
"""

import re
from typing import Optional

from .vacuums import ROBOVAC_MODELS


# Series detection patterns
SERIES_PATTERNS = {
    "C": r"^T2(103|123)$",
    "G": r"^T2(150|210|212|261)$",
    "L": r"^T2(2[67][0-9]|278|320)$",
    "X": r"^T2(080|117|118|119|120|128|130|132|181|190|192|193|194|25[0-9]|262)$",
}

# Series-specific troubleshooting guides
SERIES_GUIDES: dict[str, dict[str, str | list[str]]] = {
    "C": {
        "description": "RoboVac C Series",
        "features": "Budget-friendly models with basic cleaning capabilities",
        "common_issues": [
            "Connectivity issues - ensure WiFi is stable",
            "Navigation problems - clear obstacles from cleaning area",
            "Battery issues - charge fully before first use",
        ],
    },
    "G": {
        "description": "RoboVac G Series",
        "features": "Mid-range models with improved navigation",
        "common_issues": [
            "Mapping issues - run mapping mode in clear space",
            "Connectivity - check WiFi signal strength",
            "Sensor calibration - clean all sensors regularly",
        ],
    },
    "L": {
        "description": "Clean L Series (Hybrid)",
        "features": "Premium models with hybrid mopping and advanced features",
        "common_issues": [
            "Water tank issues - ensure tank is properly installed",
            "Mopping problems - check water level and pad condition",
            "Advanced features - refer to manual for specific features",
        ],
    },
    "X": {
        "description": "RoboVac X Series",
        "features": "Premium models with advanced navigation and features",
        "common_issues": [
            "Advanced features - check manual for feature-specific issues",
            "Navigation - ensure LiDAR sensor is clean",
            "Connectivity - verify WiFi 2.4GHz is available",
        ],
    },
}


def detect_series(model_code: Optional[str]) -> Optional[str]:
    """Detect the series of a RoboVac model.

    Args:
        model_code: The model code to analyze (e.g., 'T2278').

    Returns:
        The series letter ('C', 'G', 'L', 'X') or None if unknown.
    """
    if model_code is None:
        return None

    for series, pattern in SERIES_PATTERNS.items():
        if re.match(pattern, model_code):
            return series

    return None


def is_supported_model(model_code: str) -> bool:
    """Check if a model code is supported.

    Args:
        model_code: The model code to check.

    Returns:
        True if the model is supported, False otherwise.
    """
    return model_code in ROBOVAC_MODELS


def get_supported_models() -> list[str]:
    """Get list of all supported model codes.

    Returns:
        List of supported model codes sorted alphabetically.
    """
    return sorted(list(ROBOVAC_MODELS.keys()))


def suggest_similar_models(
    model_code: str, max_suggestions: int = 5
) -> list[tuple[str, str]]:
    """Suggest similar supported models for an unsupported model.

    Uses series detection and string similarity to find alternatives.

    Args:
        model_code: The unsupported model code.
        max_suggestions: Maximum number of suggestions to return.

    Returns:
        List of tuples (model_code, reason) for suggested models.
    """
    suggestions: list[tuple[str, str]] = []

    def numeric_component(candidate: str) -> int | None:
        """Return a model's numeric component, allowing alphabetic suffixes."""
        match = re.fullmatch(r"[A-Za-z](\d+)[A-Za-z]*", candidate)
        return int(match.group(1)) if match else None

    detected_series = detect_series(model_code)
    supported = get_supported_models()
    model_num = numeric_component(model_code)
    if model_num is not None:
        numeric_supported = [
            (model, candidate_num)
            for model in supported
            if (candidate_num := numeric_component(model)) is not None
        ]
        similar = sorted(
            numeric_supported,
            key=lambda candidate: (
                abs(candidate[1] - model_num),
                candidate[1],
                candidate[0].casefold(),
            ),
        )
        for model, _candidate_num in similar[:max_suggestions]:
            if detected_series and detect_series(model) == detected_series:
                reason = f"Same series ({detected_series})"
            else:
                reason = "Similar model number"
            suggestions.append((model, reason))
    elif detected_series:
        series_models = [
            model for model in supported if detect_series(model) == detected_series
        ]
        suggestions.extend(
            (model, f"Same series ({detected_series})")
            for model in series_models[:max_suggestions]
        )

    return suggestions[:max_suggestions]


def get_troubleshooting_guide(model_code: str) -> dict[str, str | list[str] | bool]:
    """Get series-specific troubleshooting guide.

    Args:
        model_code: The model code to get guidance for.

    Returns:
        Dictionary with troubleshooting information.
    """
    guide: dict[str, str | list[str] | bool] = {}

    # Detect series
    series = detect_series(model_code)

    if series and series in SERIES_GUIDES:
        series_info = SERIES_GUIDES[series]
        guide["series"] = series
        guide["description"] = series_info["description"]
        guide["features"] = series_info["features"]
        guide["common_issues"] = series_info["common_issues"]
    else:
        # Generic guide for unknown models
        guide["series"] = "Unknown"
        guide["description"] = "Model series could not be determined"
        guide["features"] = "Please check the manual for specifications"
        guide["common_issues"] = [
            "Verify model code is correct",
            "Check official documentation",
            "Contact support if issues persist",
        ]

    # Add support status
    guide["supported"] = is_supported_model(model_code)

    if not is_supported_model(model_code):
        suggestions = suggest_similar_models(model_code, max_suggestions=3)
        if suggestions:
            guide["suggestions"] = [s[0] for s in suggestions]

    return guide
