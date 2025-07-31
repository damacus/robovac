"""Tests for T2080 vacuum entity integration with activity mapping."""

import pytest
from unittest.mock import patch, MagicMock

from homeassistant.components.vacuum import VacuumActivity
from custom_components.robovac.vacuum import RoboVacEntity
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2080_robovac():
    """Create a mock T2080 RoboVac instance."""
    mock = MagicMock()

    # Mock the T2080 activity mapping
    mock.getRoboVacActivityMapping.return_value = {
        "Paused": VacuumActivity.PAUSED,
        "Auto Cleaning": VacuumActivity.CLEANING,
        "Room Cleaning": VacuumActivity.CLEANING,
        "Room Positioning": VacuumActivity.CLEANING,
        "Room Paused": VacuumActivity.PAUSED,
        "Standby": VacuumActivity.IDLE,
        "Heading Home": VacuumActivity.RETURNING,
        "Charging": VacuumActivity.DOCKED,
        "Completed": VacuumActivity.DOCKED,
        "Sleeping": VacuumActivity.IDLE,
        "Drying Mop": VacuumActivity.DOCKED,
        "Washing Mop": VacuumActivity.DOCKED,
        "Removing Dirty Water": VacuumActivity.DOCKED,
        "Emptying Dust": VacuumActivity.DOCKED,
        "Manual Control": VacuumActivity.CLEANING,
    }

    # Mock human readable value conversion
    def mock_get_human_readable_value(command, value):
        status_mapping = {
            "CAoAEAUyAggB": "Paused",
            "CAoCCAEQBTIA": "Room Cleaning",
            "BhAHQgBSAA==": "Standby",
            "BBADGgA=": "Charging",
            "BhADGgIIAQ==": "Completed",
            "CgoAEAkaAggBMgA=": "Auto Cleaning",
            "AhAB": "Sleeping",
            "BBAHQgA=": "Heading Home",
        }

        if command == RobovacCommand.STATUS:
            return status_mapping.get(value, value)
        return value

    mock.getRoboVacHumanReadableValue.side_effect = mock_get_human_readable_value

    # Mock other required methods
    mock.getHomeAssistantFeatures.return_value = 255
    mock.getRoboVacFeatures.return_value = 511
    mock.getFanSpeeds.return_value = ["quiet", "standard", "turbo", "max"]
    mock._get_dps_code.return_value = "153"  # STATUS code for T2080

    return mock


@pytest.fixture
def mock_t2080_vacuum_data():
    """Create mock T2080 vacuum configuration data."""
    from homeassistant.const import (
        CONF_ACCESS_TOKEN,
        CONF_MODEL,
        CONF_NAME,
        CONF_ID,
        CONF_IP_ADDRESS,
        CONF_DESCRIPTION,
        CONF_MAC,
    )

    return {
        CONF_ID: "test_t2080_id",
        CONF_NAME: "Test T2080 Vacuum",
        CONF_MODEL: "T2080",
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_key",
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
        CONF_DESCRIPTION: "RoboVac S1 Pro",
    }


@pytest.mark.asyncio
async def test_t2080_activity_with_activity_mapping(mock_t2080_robovac, mock_t2080_vacuum_data):
    """Test T2080 activity property uses activity mapping when available."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_t2080_robovac):
        entity = RoboVacEntity(mock_t2080_vacuum_data)

        # Test various T2080 states using activity mapping
        test_cases = [
            ("Paused", VacuumActivity.PAUSED),
            ("Auto Cleaning", VacuumActivity.CLEANING),
            ("Room Cleaning", VacuumActivity.CLEANING),
            ("Room Positioning", VacuumActivity.CLEANING),
            ("Room Paused", VacuumActivity.PAUSED),
            ("Standby", VacuumActivity.IDLE),
            ("Heading Home", VacuumActivity.RETURNING),
            ("Charging", VacuumActivity.DOCKED),
            ("Completed", VacuumActivity.DOCKED),
            ("Sleeping", VacuumActivity.IDLE),
            ("Drying Mop", VacuumActivity.DOCKED),
            ("Manual Control", VacuumActivity.CLEANING),
        ]

        for state, expected_activity in test_cases:
            entity._attr_tuya_state = state
            entity._attr_error_code = 0  # No error

            result = entity.activity
            assert result == expected_activity, f"Expected {expected_activity} for state '{state}', got {result}"


@pytest.mark.asyncio
async def test_t2080_activity_with_error_overrides_mapping(mock_t2080_robovac, mock_t2080_vacuum_data):
    """Test that error state overrides activity mapping."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_t2080_robovac):
        entity = RoboVacEntity(mock_t2080_vacuum_data)

        # Set a cleaning state but with an error
        entity._attr_tuya_state = "Auto Cleaning"
        entity._attr_error_code = "E001"  # Some error

        result = entity.activity
        assert result == VacuumActivity.ERROR


@pytest.mark.asyncio
async def test_t2080_activity_with_none_state(mock_t2080_robovac, mock_t2080_vacuum_data):
    """Test T2080 activity property returns None for None/0 state."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_t2080_robovac):
        entity = RoboVacEntity(mock_t2080_vacuum_data)

        # Test None state
        entity._attr_tuya_state = None
        result = entity.activity
        assert result is None

        # Test 0 state (default when no state)
        entity._attr_tuya_state = 0
        result = entity.activity
        assert result is None


@pytest.mark.asyncio
async def test_t2080_activity_unknown_state_not_in_mapping(mock_t2080_robovac, mock_t2080_vacuum_data):
    """Test T2080 activity property returns None for unknown states when activity mapping exists."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_t2080_robovac):
        entity = RoboVacEntity(mock_t2080_vacuum_data)

        # Set an unknown state not in activity mapping
        entity._attr_tuya_state = "Unknown State"
        entity._attr_error_code = 0  # No error

        result = entity.activity
        # When activity mapping exists but state is not found, returns None
        assert result is None


@pytest.mark.asyncio
async def test_t2080_update_state_uses_human_readable_values(mock_t2080_robovac, mock_t2080_vacuum_data):
    """Test that T2080 state updates use human-readable values."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_t2080_robovac):
        entity = RoboVacEntity(mock_t2080_vacuum_data)

        # Mock tuyastatus with encoded values
        entity.tuyastatus = {
            "153": "CAoAEAUyAggB",  # Encoded "Paused" status
            "106": "E001",  # Error code
            "152": "BBoCCAE=",  # Encoded "auto" mode
        }

        # Mock _get_dps_code to return the right codes
        def mock_get_dps_code(command_name):
            if command_name == "STATUS":
                return "153"
            elif command_name == "ERROR_CODE":
                return "106"
            elif command_name == "MODE":
                return "152"
            return None

        entity._get_dps_code = mock_get_dps_code

        # Call the private methods that update state
        entity._update_state_and_error()
        entity._update_mode_and_fan_speed()

        # Verify human-readable values are used
        assert entity._attr_tuya_state == "Paused"
        assert entity._attr_error_code == "E001"  # Error codes might not be converted yet

        # Verify the activity mapping is used - ERROR takes precedence over PAUSED
        # when error_code exists
        assert entity.activity == VacuumActivity.ERROR


@pytest.mark.asyncio
async def test_t2080_initialization_sets_activity_mapping(mock_t2080_robovac, mock_t2080_vacuum_data):
    """Test that T2080 entity initialization sets activity mapping attribute."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_t2080_robovac):
        entity = RoboVacEntity(mock_t2080_vacuum_data)

        # Verify activity mapping is set during initialization
        assert entity._attr_activity_mapping is not None
        assert isinstance(entity._attr_activity_mapping, dict)
        assert "Paused" in entity._attr_activity_mapping
        assert entity._attr_activity_mapping["Paused"] == VacuumActivity.PAUSED
