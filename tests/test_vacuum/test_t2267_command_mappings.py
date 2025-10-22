"""Tests for T2267 command mappings and DPS codes."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2267_robovac() -> RoboVac:
    """Create a mock T2267 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2267",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2267_dps_codes(mock_t2267_robovac: RoboVac) -> None:
    """Test that T2267 has the correct DPS codes."""
    dps_codes = mock_t2267_robovac.getDpsCodes()

    assert dps_codes["MODE"] == "152"
    assert dps_codes["STATUS"] == "153"
    assert dps_codes["DIRECTION"] == "155"
    assert dps_codes["START_PAUSE"] == "156"
    assert dps_codes["DO_NOT_DISTURB"] == "157"
    assert dps_codes["FAN_SPEED"] == "158"
    assert dps_codes["BOOST_IQ"] == "159"
    assert dps_codes["LOCATE"] == "160"
    assert dps_codes["BATTERY_LEVEL"] == "163"
    assert dps_codes["CONSUMABLES"] == "168"
    assert dps_codes["RETURN_HOME"] == "173"
    assert dps_codes["ERROR_CODE"] == "177"


def test_t2267_mode_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 MODE command value mappings."""
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "BBoCCAE="
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "pause") == "AggN"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "Spot") == "AA=="
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "return") == "AggG"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "Nosweep") == "AggO"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2267_fan_speed_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 FAN_SPEED command value mappings."""
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "quiet") == "Quiet"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "max") == "Max"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost_iq") == "Boost_IQ"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2267_direction_command_values(mock_t2267_robovac: RoboVac) -> None:
    """Test T2267 DIRECTION command value mappings."""
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "brake") == "brake"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "forward") == "forward"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "back") == "back"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "left") == "left"
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "right") == "right"

    # Unknown returns as-is
    assert mock_t2267_robovac.getRoboVacCommandValue(RobovacCommand.DIRECTION, "unknown") == "unknown"


def test_t2267_command_codes(mock_t2267_robovac: RoboVac) -> None:
    """Test that T2267 command codes are correctly defined on model."""
    commands = mock_t2267_robovac.model_details.commands

    assert commands[RobovacCommand.MODE]["code"] == 152
    assert commands[RobovacCommand.STATUS]["code"] == 153
    assert commands[RobovacCommand.DIRECTION]["code"] == 155
    assert commands[RobovacCommand.START_PAUSE]["code"] == 156
    assert commands[RobovacCommand.DO_NOT_DISTURB]["code"] == 157
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 158
    assert commands[RobovacCommand.BOOST_IQ]["code"] == 159
    assert commands[RobovacCommand.LOCATE]["code"] == 160
    assert commands[RobovacCommand.BATTERY]["code"] == 163
    assert commands[RobovacCommand.CONSUMABLES]["code"] == 168
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 173
    assert commands[RobovacCommand.ERROR]["code"] == 177
