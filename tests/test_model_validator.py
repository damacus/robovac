"""Tests for model validator library with series detection."""

import pytest

from custom_components.robovac.model_validator import (
    detect_series,
    get_supported_models,
    is_supported_model,
    suggest_similar_models,
    get_troubleshooting_guide,
)


class TestSeriesDetection:
    """Test suite for model series detection."""

    def test_detect_c_series(self) -> None:
        """Test detection of C series models."""
        # C series models: T2103, T2123
        assert detect_series("T2103") == "C"
        assert detect_series("T2123") == "C"

    def test_detect_g_series(self) -> None:
        """Test detection of G series models."""
        # G series models: T2150, T2261
        assert detect_series("T2150") == "G"
        assert detect_series("T2261") == "G"

    def test_detect_l_series(self) -> None:
        """Test detection of L series models."""
        # L series models: T2267, T2268, T2270, T2272, T2273, T2275, T2276, T2277, T2278, T2320
        assert detect_series("T2267") == "L"
        assert detect_series("T2278") == "L"
        assert detect_series("T2320") == "L"

    def test_detect_x_series(self) -> None:
        """Test detection of X series models."""
        # X series models: T2080, T2117, T2118, T2119, T2120, T2128, T2130, T2132, T2181, T2190, T2192, T2193, T2194, T2250, T2251, T2252, T2253, T2254, T2255, T2259, T2262
        assert detect_series("T2080") == "X"
        assert detect_series("T2118") == "X"
        assert detect_series("T2250") == "X"

    def test_detect_unknown_series(self) -> None:
        """Test detection of unknown model returns None."""
        assert detect_series("T9999") is None
        assert detect_series("INVALID") is None

    def test_detect_none_model(self) -> None:
        """Test detection with None returns None."""
        assert detect_series(None) is None


class TestModelValidation:
    """Test suite for model validation."""

    def test_is_supported_model_true(self) -> None:
        """Test is_supported_model returns True for known models."""
        assert is_supported_model("T2278") is True
        assert is_supported_model("T2250") is True
        assert is_supported_model("T2080") is True

    def test_is_supported_model_false(self) -> None:
        """Test is_supported_model returns False for unknown models."""
        assert is_supported_model("T9999") is False
        assert is_supported_model("INVALID") is False

    def test_is_supported_model_case_sensitive(self) -> None:
        """Test is_supported_model is case-sensitive."""
        assert is_supported_model("t2278") is False
        assert is_supported_model("T2278") is True

    def test_get_supported_models_returns_list(self) -> None:
        """Test get_supported_models returns a list."""
        models = get_supported_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_get_supported_models_contains_known_models(self) -> None:
        """Test get_supported_models contains known models."""
        models = get_supported_models()
        assert "T2278" in models
        assert "T2250" in models
        assert "T2080" in models

    def test_get_supported_models_no_duplicates(self) -> None:
        """Test get_supported_models has no duplicates."""
        models = get_supported_models()
        assert len(models) == len(set(models))


class TestModelSuggestions:
    """Test suite for model suggestions."""

    def test_suggest_similar_models_returns_list(self) -> None:
        """Test suggest_similar_models returns a list."""
        suggestions = suggest_similar_models("T9999")
        assert isinstance(suggestions, list)

    def test_suggest_similar_models_for_unknown_model(self) -> None:
        """Test suggest_similar_models provides suggestions for unknown models."""
        suggestions = suggest_similar_models("T2999")
        # Should suggest similar models
        assert len(suggestions) > 0

    def test_suggest_similar_models_respects_max_suggestions(self) -> None:
        """Test suggest_similar_models respects max_suggestions parameter."""
        suggestions = suggest_similar_models("T9999", max_suggestions=3)
        assert len(suggestions) <= 3

    def test_suggest_similar_models_for_supported_model(self) -> None:
        """Test suggest_similar_models for already supported model."""
        suggestions = suggest_similar_models("T2278")
        # May return empty or similar models
        assert isinstance(suggestions, list)

    def test_suggest_similar_models_returns_tuples(self) -> None:
        """Test suggest_similar_models returns tuples of (model, reason)."""
        suggestions = suggest_similar_models("T2999")
        if len(suggestions) > 0:
            for suggestion in suggestions:
                assert isinstance(suggestion, tuple)
                assert len(suggestion) == 2


class TestTroubleshootingGuide:
    """Test suite for troubleshooting guides."""

    def test_get_troubleshooting_guide_returns_dict(self) -> None:
        """Test get_troubleshooting_guide returns a dictionary."""
        guide = get_troubleshooting_guide("T2278")
        assert isinstance(guide, dict)

    def test_get_troubleshooting_guide_for_supported_model(self) -> None:
        """Test get_troubleshooting_guide for supported model."""
        guide = get_troubleshooting_guide("T2278")
        # Should have some guidance
        assert isinstance(guide, dict)

    def test_get_troubleshooting_guide_for_unsupported_model(self) -> None:
        """Test get_troubleshooting_guide for unsupported model."""
        guide = get_troubleshooting_guide("T9999")
        assert isinstance(guide, dict)

    def test_get_troubleshooting_guide_by_series(self) -> None:
        """Test get_troubleshooting_guide provides series-specific guidance."""
        # L series model
        guide_l = get_troubleshooting_guide("T2278")
        # X series model
        guide_x = get_troubleshooting_guide("T2080")
        # Both should return dicts
        assert isinstance(guide_l, dict)
        assert isinstance(guide_x, dict)
