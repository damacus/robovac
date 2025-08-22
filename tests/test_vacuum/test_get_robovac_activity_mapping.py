"""Tests for the getRoboVacActivityMapping method."""

import pytest
from unittest.mock import patch

from homeassistant.components.vacuum import VacuumActivity
from custom_components.robovac.robovac import RoboVac


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

        # Mock the T2080 activity mapping
        robovac.model_details.activity_mapping = {
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
        return robovac


@pytest.fixture
def mock_robovac_no_activity_mapping():
    """Create a mock RoboVac instance without activity mapping."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2118",  # Model without activity mapping
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )

        # No activity mapping for this model
        robovac.model_details.activity_mapping = None
        return robovac


def test_get_activity_mapping_success(mock_t2080_robovac):
    """Test getRoboVacActivityMapping returns correct activity mapping."""
    activity_mapping = mock_t2080_robovac.getRoboVacActivityMapping()

    assert activity_mapping is not None
    assert isinstance(activity_mapping, dict)

    # Test specific mappings
    assert activity_mapping["Paused"] == VacuumActivity.PAUSED
    assert activity_mapping["Auto Cleaning"] == VacuumActivity.CLEANING
    assert activity_mapping["Room Cleaning"] == VacuumActivity.CLEANING
    assert activity_mapping["Standby"] == VacuumActivity.IDLE
    assert activity_mapping["Heading Home"] == VacuumActivity.RETURNING
    assert activity_mapping["Charging"] == VacuumActivity.DOCKED
    assert activity_mapping["Completed"] == VacuumActivity.DOCKED


def test_get_activity_mapping_none(mock_robovac_no_activity_mapping):
    """Test getRoboVacActivityMapping returns None when no mapping exists."""
    activity_mapping = mock_robovac_no_activity_mapping.getRoboVacActivityMapping()

    assert activity_mapping is None


def test_activity_mapping_completeness(mock_t2080_robovac):
    """Test that activity mapping covers all expected T2080 states."""
    activity_mapping = mock_t2080_robovac.getRoboVacActivityMapping()

    # Expected states from T2080.py
    expected_states = [
        "Paused",
        "Auto Cleaning",
        "Room Cleaning",
        "Room Positioning",
        "Room Paused",
        "Standby",
        "Heading Home",
        "Charging",
        "Completed",
        "Sleeping",
        "Drying Mop",
        "Washing Mop",
        "Removing Dirty Water",
        "Emptying Dust",
        "Manual Control",
    ]

    for state in expected_states:
        assert state in activity_mapping, f"Missing activity mapping for state: {state}"
        assert isinstance(
            activity_mapping[state], VacuumActivity), f"Invalid activity type for state: {state}"


def test_activity_mapping_values_are_valid(mock_t2080_robovac):
    """Test that all activity mapping values are valid VacuumActivity enums."""
    activity_mapping = mock_t2080_robovac.getRoboVacActivityMapping()

    valid_activities = set(VacuumActivity)

    for state, activity in activity_mapping.items():
        assert activity in valid_activities, f"Invalid VacuumActivity for state {state}: {activity}"
