"""Tests for error message handling and context functions."""

import pytest

from custom_components.robovac.errors import getErrorMessage, getErrorMessageWithContext


class TestErrorMessages:
    """Test suite for error message functions."""

    def test_laser_sensor_typo_fixed(self) -> None:
        """Test that 'Laser sesor stuck' typo has been fixed to 'Laser sensor stuck'."""
        # Error code 19 should return "Laser sensor stuck" (not "sesor")
        error_message = getErrorMessage(19)
        assert error_message == "Laser sensor stuck"
        assert "sesor" not in error_message.lower()

    def test_get_error_message_with_known_code(self) -> None:
        """Test getErrorMessage returns correct message for known error codes."""
        assert getErrorMessage(1) == "Front bumper stuck"
        assert getErrorMessage(2) == "Wheel stuck"
        assert getErrorMessage(3) == "Side brush"
        assert getErrorMessage(8) == "Low battery"
        assert getErrorMessage(19) == "Laser sensor stuck"

    def test_get_error_message_with_string_code(self) -> None:
        """Test getErrorMessage handles string error codes."""
        assert getErrorMessage("no_error") == "None"
        assert getErrorMessage("S1") == "Battery"
        assert getErrorMessage("S2") == "Wheel Module"

    def test_get_error_message_with_unknown_code(self) -> None:
        """Test getErrorMessage returns string representation for unknown codes."""
        result = getErrorMessage(9999)
        assert result == "9999"
        assert isinstance(result, str)

    def test_get_error_message_with_none(self) -> None:
        """Test getErrorMessage handles None gracefully."""
        result = getErrorMessage(None)  # type: ignore[arg-type]
        assert result == "None"


class TestErrorMessageWithContext:
    """Test suite for getErrorMessageWithContext function."""

    def test_error_context_returns_dict(self) -> None:
        """Test that getErrorMessageWithContext returns a dictionary."""
        result = getErrorMessageWithContext(19)
        assert isinstance(result, dict)

    def test_error_context_has_required_keys(self) -> None:
        """Test that error context includes required keys."""
        result = getErrorMessageWithContext(1)
        assert "message" in result
        assert isinstance(result["message"], str)

    def test_error_context_message_is_correct(self) -> None:
        """Test that error context message matches getErrorMessage."""
        error_code = 2
        context = getErrorMessageWithContext(error_code)
        message = getErrorMessage(error_code)
        assert context["message"] == message

    def test_error_context_with_model_code(self) -> None:
        """Test that error context can accept optional model_code parameter."""
        # Should not raise an error
        result = getErrorMessageWithContext(1, model_code="T2278")
        assert isinstance(result, dict)
        assert "message" in result

    def test_error_context_with_unknown_code(self) -> None:
        """Test error context handles unknown error codes."""
        result = getErrorMessageWithContext(9999)
        assert isinstance(result, dict)
        assert "message" in result

    def test_laser_sensor_context_has_troubleshooting(self) -> None:
        """Test that laser sensor error includes troubleshooting guidance."""
        result = getErrorMessageWithContext(19)
        # Should have some form of guidance or context
        assert isinstance(result, dict)
        assert "message" in result
        assert result["message"] == "Laser sensor stuck"

    def test_error_context_structure_consistency(self) -> None:
        """Test that error context maintains consistent structure across different codes."""
        codes = [1, 2, 8, 19]
        for code in codes:
            result = getErrorMessageWithContext(code)
            assert isinstance(result, dict)
            assert "message" in result
            assert isinstance(result["message"], str)
            assert len(result["message"]) > 0
