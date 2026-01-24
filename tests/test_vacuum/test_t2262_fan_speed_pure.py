"""Test T2262 Pure fan speed mapping.

This test verifies the fix for GitHub issue #300:
The T2262 (Eufy X8) device uses "Quiet" internally for what Eufy markets as "Pure" mode.
"""
from unittest.mock import patch

import pytest
from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_t2262_robovac() -> RoboVac:
    """Create a mock T2262 RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2262",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_local_key",
        )
        return robovac


class TestT2262PureFanSpeed:
    """Test that T2262 Pure fan speed sends correct value to device."""

    def test_pure_fan_speed_sends_quiet_to_device(self, mock_t2262_robovac: RoboVac) -> None:
        """Verify that 'pure' fan speed sends 'Quiet' to the device.

        The device internally uses 'Quiet' for what Eufy markets as 'Pure' mode.
        When user selects "Pure" in Home Assistant, the normalized value "pure"
        should be translated to "Quiet" before sending to the device.
        """
        result = mock_t2262_robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "pure")
        assert result == "Quiet", (
            f"Expected 'Quiet' to be sent to device for 'pure' fan speed, "
            f"but got '{result}'"
        )

    def test_fan_speed_list_shows_pure_for_ui(self, mock_t2262_robovac: RoboVac) -> None:
        """Verify that the fan speed list shows 'Pure' (not 'Quiet') to users.

        The UI should display user-friendly names, so "Pure" should appear
        in the fan speed list even though "Quiet" is sent to the device.
        """
        fan_speeds = mock_t2262_robovac.getFanSpeeds()
        assert "Pure" in fan_speeds, (
            f"Expected 'Pure' in fan speed list for UI display, "
            f"got {fan_speeds}"
        )

    def test_other_fan_speeds_unchanged(self, mock_t2262_robovac: RoboVac) -> None:
        """Verify that other fan speeds still work correctly."""
        assert mock_t2262_robovac.getRoboVacCommandValue(
            RobovacCommand.FAN_SPEED, "standard"
        ) == "Standard"
        assert mock_t2262_robovac.getRoboVacCommandValue(
            RobovacCommand.FAN_SPEED, "turbo"
        ) == "Turbo"
        assert mock_t2262_robovac.getRoboVacCommandValue(
            RobovacCommand.FAN_SPEED, "max"
        ) == "Max"
