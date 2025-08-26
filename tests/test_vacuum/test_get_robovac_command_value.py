"""Tests for the getRoboVacCommandValue method."""

import pytest
from unittest.mock import patch, MagicMock

from custom_components.robovac.robovac import RoboVac, RobovacCommand


@pytest.fixture
def mock_robovac():
    """Create a mock RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2250",  # G30
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        # Mock the model commands for testing
        robovac.model_details.commands = {
            RobovacCommand.MODE: {
                "code": 5,
                "values": {
                    "auto": "auto",
                    "small_room": "SmallRoom",
                    "edge": "Edge",
                    "spot": "Spot"
                },
            },
            RobovacCommand.DIRECTION: {
                "code": 3,
                "values": ["forward", "back", "left", "right"],
            },
            RobovacCommand.FAN_SPEED: {
                "code": 102,
            },
        }
        return robovac


def test_get_robovac_command_value_with_dict(mock_robovac):
    """Test getRoboVacCommandValue returns correct values when using dict format."""
    # Test normal case - key exists
    assert mock_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "auto"
    assert (
        mock_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room")
        == "SmallRoom"
    )

    # Test case where key doesn't exist in the dict - should return the original value
    assert (
        mock_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown_mode")
        == "unknown_mode"
    )


def test_get_robovac_command_value_no_values(mock_robovac):
    """Test getRoboVacCommandValue when command has no values field."""
    # Test when command exists but has no values defined
    value = mock_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard")
    assert value == "standard"


def test_get_robovac_command_value_invalid_command(mock_robovac):
    """Test getRoboVacCommandValue with invalid command."""
    # Test with invalid command name (not in the commands dict)
    assert mock_robovac.getRoboVacCommandValue("INVALID_COMMAND", "some_value") == "some_value"

    # Test with None value
    assert mock_robovac.getRoboVacCommandValue(RobovacCommand.MODE, None) is None


def test_get_robovac_command_value_error_handling(mock_robovac):
    """Test getRoboVacCommandValue error handling."""
    # Mock the _get_command_values to raise an exception
    mock_robovac._get_command_values = MagicMock(side_effect=KeyError("Test exception"))

    # Should return the original value when an exception occurs
    assert mock_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "auto"
