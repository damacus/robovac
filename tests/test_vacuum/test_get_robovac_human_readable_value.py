"""Tests for the getRoboVacHumanReadableValue method."""

import pytest
from unittest.mock import patch, MagicMock

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2080_robovac():
    """Create a mock T2080 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2080",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        # Mock the T2080 model commands for testing
        robovac.model_details.commands = {
            RobovacCommand.STATUS: {
                "code": 153,
                "values": {
                    "CAoAEAUyAggB": "Paused",
                    "CAoCCAEQBTIA": "Room Cleaning",
                    "BhAHQgBSAA==": "Standby",
                    "BBADGgA=": "Charging",
                    "BhADGgIIAQ==": "Completed",
                    "CgoAEAkaAggBMgA=": "Auto Cleaning",
                },
            },
            RobovacCommand.MODE: {
                "code": 152,
                "values": {
                    "BBoCCAE=": "auto",
                    "AggN": "pause",
                    "AA==": "Spot",
                    "AggG": "return",
                },
            },
            RobovacCommand.ERROR: {
                "code": 106,
                "values": {
                    "E001": "Wheel stuck",
                    "E002": "Side brush stuck",
                    "E003": "Suction fan stuck",
                },
            },
            RobovacCommand.FAN_SPEED: {
                "code": 158,
                "values": {
                    "quiet": "Quiet",
                    "standard": "Standard",
                    "turbo": "Turbo",
                    "max": "Max"
                },
            },
        }
        return robovac


def test_get_human_readable_value_status_success(mock_t2080_robovac):
    """Test getRoboVacHumanReadableValue returns correct human-readable status values."""
    # Test various status codes
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "CAoAEAUyAggB"
    ) == "Paused"

    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "CAoCCAEQBTIA"
    ) == "Room Cleaning"

    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "BhAHQgBSAA=="
    ) == "Standby"

    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.STATUS, "BBADGgA="
    ) == "Charging"


def test_get_human_readable_value_mode_success(mock_t2080_robovac):
    """Test getRoboVacHumanReadableValue returns correct human-readable mode values."""
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.MODE, "BBoCCAE="
    ) == "auto"

    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.MODE, "AggN"
    ) == "pause"

    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.MODE, "AA=="
    ) == "Spot"


def test_get_human_readable_value_error_success(mock_t2080_robovac):
    """Test getRoboVacHumanReadableValue returns correct human-readable error values."""
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.ERROR, "E001"
    ) == "Wheel stuck"

    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.ERROR, "E002"
    ) == "Side brush stuck"


def test_get_human_readable_value_fan_speed_success(mock_t2080_robovac):
    """Test getRoboVacHumanReadableValue returns correct human-readable fan speed values."""
    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.FAN_SPEED, "quiet"
    ) == "Quiet"

    assert mock_t2080_robovac.getRoboVacHumanReadableValue(
        RobovacCommand.FAN_SPEED, "standard"
    ) == "Standard"


def test_get_human_readable_value_unknown_value(mock_t2080_robovac):
    """Test getRoboVacHumanReadableValue returns original value for unknown values."""
    with patch("custom_components.robovac.robovac._LOGGER") as mock_logger:
        result = mock_t2080_robovac.getRoboVacHumanReadableValue(
            RobovacCommand.STATUS, "UNKNOWN_CODE"
        )

        # Should return the original value
        assert result == "UNKNOWN_CODE"

        # Should log a warning
        mock_logger.warning.assert_called_once()
        # Check that the warning was called with the expected parameters
        call_args = mock_logger.warning.call_args
        assert "Command %s with value %s not found for model %s" in call_args[0][0]
        assert call_args[0][1] == "status"
        assert call_args[0][2] == "UNKNOWN_CODE"
        assert call_args[0][3] == "T2080"


def test_get_human_readable_value_invalid_command(mock_t2080_robovac):
    """Test getRoboVacHumanReadableValue handles invalid commands gracefully."""
    with patch("custom_components.robovac.robovac._LOGGER") as mock_logger:
        result = mock_t2080_robovac.getRoboVacHumanReadableValue(
            "INVALID_COMMAND", "some_value"
        )

        # Should return the original value
        assert result == "some_value"

        # Should log a warning
        mock_logger.warning.assert_called_once()


def test_get_human_readable_value_command_no_values(mock_t2080_robovac):
    """Test getRoboVacHumanReadableValue handles commands with no values field."""
    # Add a command with no values field
    mock_t2080_robovac.model_details.commands[RobovacCommand.BATTERY] = {
        "code": 163,
    }

    with patch("custom_components.robovac.robovac._LOGGER") as mock_logger:
        result = mock_t2080_robovac.getRoboVacHumanReadableValue(
            RobovacCommand.BATTERY, "85"
        )

        # Should return the original value
        assert result == "85"

        # Should log a warning
        mock_logger.warning.assert_called_once()
