"""Test fixtures for RoboVac integration tests."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import from pytest_homeassistant_custom_component instead of directly from homeassistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.components.vacuum import VacuumEntityFeature
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_MODEL,
    CONF_NAME,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_DESCRIPTION,
    CONF_MAC,
)

from custom_components.robovac.vacuums.base import RoboVacEntityFeature


# This fixture is required for testing custom components
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for testing."""
    yield


@pytest.fixture
def mock_robovac():
    """Create a mock RoboVac device."""
    mock = MagicMock()
    # Set up common return values
    mock.getHomeAssistantFeatures.return_value = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )

    # Set up getRoboVacCommandValue to simulate T2268 model lookup behavior
    def command_value_side_effect(command_name, value):
        # Simulate T2268 model command value mappings
        if command_name.name == "MODE":
            mode_mappings = {
                "auto": "Auto",
                "small_room": "SmallRoom",
                "spot": "Spot",
                "edge": "Edge",
                "nosweep": "Nosweep",
            }
            return mode_mappings.get(value, value)
        elif command_name.name == "FAN_SPEED":
            fan_speed_mappings = {
                "no_suction": "No Suction",
                "standard": "Standard",
                "boost_iq": "Boost IQ",
                "max": "Max",
                "turbo": "Turbo",
                "pure": "Pure",
            }
            return fan_speed_mappings.get(value, value)
        elif command_name.name == "START_PAUSE":
            start_pause_mappings = {
                "pause": "pause",
                "start": "start",
            }
            return start_pause_mappings.get(value, value)
        elif command_name.name == "RETURN_HOME":
            return_home_mappings = {
                "return": "return",
            }
            return return_home_mappings.get(value, value)
        # For other commands, return the value as-is
        return value

    mock.getRoboVacCommandValue.side_effect = command_value_side_effect
    mock.getRoboVacFeatures.return_value = (
        RoboVacEntityFeature.EDGE | RoboVacEntityFeature.SMALL_ROOM
    )
    mock.getFanSpeeds.return_value = ["No Suction", "Standard", "Boost IQ", "Max"]
    mock._dps = {}

    # Mock the new methods added in PR #161
    # For models without activity mapping, return None
    mock.getRoboVacActivityMapping.return_value = None

    # For human readable values, return the original value (no conversion)
    mock.getRoboVacHumanReadableValue.side_effect = lambda command, value: value

    # Set up async methods with AsyncMock
    mock.async_get = AsyncMock(return_value=mock._dps)
    mock.async_set = AsyncMock(return_value=True)
    mock.async_disable = AsyncMock(return_value=True)

    return mock


@pytest.fixture
def mock_g30():
    """Create a mock G30 RoboVac device."""
    mock = MagicMock()
    # Set up common return values
    mock.getHomeAssistantFeatures.return_value = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )
    mock.getRoboVacFeatures.return_value = (
        RoboVacEntityFeature.EDGE | RoboVacEntityFeature.SMALL_ROOM
    )
    mock.getFanSpeeds.return_value = ["No Suction", "Standard", "Boost IQ", "Max"]
    mock._dps = {}

    # Set up async methods with AsyncMock
    mock.async_get = AsyncMock(return_value=mock._dps)
    mock.async_set = AsyncMock(return_value=True)
    mock.async_disable = AsyncMock(return_value=True)

    return mock


@pytest.fixture
def mock_vacuum_data():
    """Create mock vacuum configuration data."""
    return {
        CONF_NAME: "Test RoboVac",
        CONF_ID: "test_robovac_id",
        CONF_MODEL: "T2118",  # 15C model
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_access_token",
        CONF_DESCRIPTION: "RoboVac 15C",
        CONF_MAC: "aa:bb:cc:dd:ee:ff",
    }


@pytest.fixture
def mock_g30_data():
    """Create mock G30 vacuum configuration data."""
    return {
        CONF_NAME: "Test G30",
        CONF_ID: "test_g30_id",
        CONF_MODEL: "T2250",  # G30 model
        CONF_IP_ADDRESS: "192.168.1.101",
        CONF_ACCESS_TOKEN: "test_access_token_g30",
        CONF_DESCRIPTION: "RoboVac G30",
        CONF_MAC: "aa:bb:cc:dd:ee:00",
    }


@pytest.fixture
def mock_l60():
    """Create a mock L60 RoboVac device."""
    mock = MagicMock()
    # Set up common return values
    mock.getHomeAssistantFeatures.return_value = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )
    mock.getRoboVacFeatures.return_value = (
        RoboVacEntityFeature.DO_NOT_DISTURB | RoboVacEntityFeature.BOOST_IQ
    )
    mock.getFanSpeeds.return_value = ["No Suction", "Standard", "Boost IQ", "Max"]
    mock._dps = {}

    # Set up model-specific DPS codes for L60 (T2278)
    mock.getDpsCodes.return_value = {
        "MODE": "152",
        "STATUS": "173",
        "RETURN_HOME": "153",
        "FAN_SPEED": "154",
        "LOCATE": "153",
        "BATTERY_LEVEL": "172",
        "ERROR_CODE": "169"
    }

    # Set up L60-specific command value mapping
    def l60_command_value_side_effect(command_name, value):
        from custom_components.robovac.robovac import RobovacCommand
        if (command_name == RobovacCommand.MODE or command_name == "MODE") and value == "auto":
            return "BBoCCAE="
        return value

    mock.getRoboVacCommandValue.side_effect = l60_command_value_side_effect

    # Set up async methods with AsyncMock
    mock.async_get = AsyncMock(return_value=mock._dps)
    mock.async_set = AsyncMock(return_value=True)
    mock.async_disable = AsyncMock(return_value=True)

    return mock


@pytest.fixture
def mock_l60_data():
    """Create mock L60 vacuum configuration data."""
    return {
        CONF_NAME: "Test L60",
        CONF_ID: "test_l60_id",
        CONF_MODEL: "T2278",  # L60 model
        CONF_IP_ADDRESS: "192.168.1.102",
        CONF_ACCESS_TOKEN: "test_access_token_l60",
        CONF_DESCRIPTION: "eufy Clean L60 Hybrid SES",
        CONF_MAC: "aa:bb:cc:dd:ee:11",
    }


@pytest.fixture
def mock_t2080():
    """Create a mock T2080 RoboVac device."""
    mock = MagicMock()
    # Set up T2080-specific return values
    mock.getHomeAssistantFeatures.return_value = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.MAP
    )
    mock.getRoboVacFeatures.return_value = (
        RoboVacEntityFeature.CLEANING_TIME
        | RoboVacEntityFeature.CLEANING_AREA
        | RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.AUTO_RETURN
        | RoboVacEntityFeature.ROOM
        | RoboVacEntityFeature.ZONE
        | RoboVacEntityFeature.BOOST_IQ
        | RoboVacEntityFeature.MAP
        | RoboVacEntityFeature.CONSUMABLES
    )
    mock.getFanSpeeds.return_value = ["quiet", "standard", "turbo", "max"]
    mock.model_code = "T2080"
    mock._dps = {
        "2": False,
        "153": "BhAHQgBSAA==",  # Standby status
        "158": "standard",
        "163": 85,
        "159": True,
        "6": 0,
        "7": 0,
    }

    # Mock activity mapping for T2080
    from homeassistant.components.vacuum import VacuumActivity
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
        from custom_components.robovac.vacuums.base import RobovacCommand
        status_mapping = {
            "CAoAEAUyAggB": "Paused",
            "CAoCCAEQBTIA": "Room Cleaning",
            "BhAHQgBSAA==": "Standby",
            "BBADGgA=": "Charging",
            "BhADGgIIAQ==": "Completed",
            "CgoAEAkaAggBMgA=": "Auto Cleaning",
        }

        if command == RobovacCommand.STATUS:
            return status_mapping.get(value, value)
        return value

    mock.getRoboVacHumanReadableValue.side_effect = mock_get_human_readable_value

    return mock


@pytest.fixture
def mock_t2080_data():
    """Create mock T2080 vacuum configuration data."""
    return {
        CONF_ID: "test_t2080_id",
        CONF_NAME: "Test T2080 Vacuum",
        CONF_MODEL: "T2080",
        CONF_IP_ADDRESS: "192.168.1.103",
        CONF_ACCESS_TOKEN: "test_access_token_t2080",
        CONF_DESCRIPTION: "RoboVac S1 Pro",
        CONF_MAC: "aa:bb:cc:dd:ee:22",
    }
