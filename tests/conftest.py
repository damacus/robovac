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

from custom_components.robovac.robovac import RoboVacEntityFeature


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
