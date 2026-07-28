"""Tests for T2266 command mappings and DPS codes.

The T2266 (eufy Clean X8 Pro) shares the same core hardware as the X8 Pro SES (T2276)
and uses protocol 3.5 with standard Tuya DPS codes (1-135).
"""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2266_robovac() -> RoboVac:
    """Create a mock T2266 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2266",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_t2266_protocol_version() -> None:
    """T2266 must speak protocol 3.5 (session-key negotiation / AES-GCM)."""
    from custom_components.robovac.vacuums.T2266 import T2266

    assert T2266.protocol_version == 3.5


def test_t2266_does_not_opt_into_protocol_35_network_behaviors() -> None:
    """T2266 must not enable the T2276's protocol 3.5 network opt-ins.

    protocol_35_empty_dps_query and protocol_35_map_data_keepalive change what
    the integration sends on the wire (empty-DPS status queries, SET_COMMAND_NEW
    writes to DPS 121 on ping). They were validated for the T2276 with packet
    captures; no equivalent T2266 capture exists, so they must stay off until
    one does.
    """
    from custom_components.robovac.vacuums.T2266 import T2266

    assert getattr(T2266, "protocol_35_empty_dps_query", False) is False
    assert getattr(T2266, "protocol_35_map_data_keepalive", False) is False


def test_t2266_dps_codes(mock_t2266_robovac) -> None:
    """Test that T2266 has the correct DPS codes (protocol 3.5, standard Tuya)."""
    dps_codes = mock_t2266_robovac.getDpsCodes()

    assert dps_codes["MODE"] == "5"
    assert dps_codes["STATUS"] == "15"
    assert dps_codes["RETURN_HOME"] == "101"
    assert dps_codes["FAN_SPEED"] == "102"
    assert dps_codes["LOCATE"] == "103"
    assert dps_codes["BATTERY_LEVEL"] == "104"
    assert dps_codes["ERROR_CODE"] == "106"
    assert dps_codes["DO_NOT_DISTURB"] == "107"
    assert dps_codes["CLEANING_TIME"] == "109"
    assert dps_codes["CLEANING_AREA"] == "110"
    assert dps_codes["BOOST_IQ"] == "118"


def test_t2266_mode_command_values(mock_t2266_robovac) -> None:
    """Test T2266 MODE command value mappings.

    Note: the X8 Pro series uses lowercase "auto" unlike T2128's "Auto",
    confirmed by T2276 packet capture and the T2266 cloud DPS snapshot.
    """
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "auto") == "auto"
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "small_room") == "SmallRoom"
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "spot") == "Spot"
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "edge") == "Edge"
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "nosweep") == "Nosweep"

    # Unknown returns as-is
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.MODE, "unknown") == "unknown"


def test_t2266_start_pause_command_values(mock_t2266_robovac) -> None:
    """Test T2266 START_PAUSE value mapping (boolean DPS 2)."""
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "start") is True
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.START_PAUSE, "pause") is False


def test_t2266_return_home_command_values(mock_t2266_robovac) -> None:
    """Test T2266 RETURN_HOME value mapping (boolean DPS 101)."""
    # DPS 101 is a boolean trigger — "return" maps to True
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.RETURN_HOME, "return") is True


def test_t2266_fan_speed_command_values(mock_t2266_robovac) -> None:
    """Test T2266 FAN_SPEED value mapping."""
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "pure") == "Quiet"
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "standard") == "Standard"
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "turbo") == "Turbo"
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "boost") == "Boost"

    # Unknown returns as-is
    assert mock_t2266_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "unknown") == "unknown"


def test_t2266_command_codes(mock_t2266_robovac) -> None:
    """Test that T2266 command codes are correctly defined on model."""
    commands = mock_t2266_robovac.model_details.commands

    assert commands[RobovacCommand.START_PAUSE]["code"] == 2
    assert commands[RobovacCommand.MODE]["code"] == 5
    assert commands[RobovacCommand.STATUS]["code"] == 15
    assert commands[RobovacCommand.RETURN_HOME]["code"] == 101
    assert commands[RobovacCommand.FAN_SPEED]["code"] == 102
    assert commands[RobovacCommand.LOCATE]["code"] == 103
    assert commands[RobovacCommand.BATTERY]["code"] == 104
    assert commands[RobovacCommand.ERROR]["code"] == 106
    assert commands[RobovacCommand.DO_NOT_DISTURB]["code"] == 107
    assert commands[RobovacCommand.CLEANING_TIME]["code"] == 109
    assert commands[RobovacCommand.CLEANING_AREA]["code"] == 110
    assert commands[RobovacCommand.BOOST_IQ]["code"] == 118
