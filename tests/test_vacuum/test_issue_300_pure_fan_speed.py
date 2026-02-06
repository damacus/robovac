"""Test T2262 Pure fan speed mapping for Issue #300."""
import pytest
from unittest.mock import patch
from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


class TestIssue300PureFanSpeed:
    """Test that T2262 Pure fan speed sends correct value to device."""

    @pytest.fixture
    def robovac(self):
        """Create a T2262 RoboVac instance for testing."""
        with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
            return RoboVac(
                model_code="T2262",
                device_id="test_device",
                host="127.0.0.1",
                local_key="test_key",
            )

    def test_pure_fan_speed_sends_quiet_to_device(self, robovac):
        """Verify that 'pure' fan speed sends 'Quiet' to the device for T2262.

        The device internally uses 'Quiet' for what Eufy markets as 'Pure' mode.
        """
        result = robovac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "pure")
        assert result == "Quiet", (
            f"Expected 'Quiet' to be sent to device for 'pure' fan speed, "
            f"but got '{result}'"
        )

    def test_t2261_pure_fan_speed(self):
        """Verify T2261 Pure fan speed mapping."""
        with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
            vac = RoboVac(model_code="T2261", device_id="id", host="127.0.0.1", local_key="key")
            result = vac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "pure")
            # We expect this to fail currently (returns "Pure", should be "Quiet")
            assert result == "Quiet", f"T2261: Expected 'Quiet', got '{result}'"

    def test_t2268_pure_fan_speed(self):
        """Verify T2268 Pure fan speed mapping."""
        with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
            vac = RoboVac(model_code="T2268", device_id="id", host="127.0.0.1", local_key="key")
            result = vac.getRoboVacCommandValue(RobovacCommand.FAN_SPEED, "pure")
            # We expect this to fail currently (returns "Pure", should be "Quiet")
            assert result == "Quiet", f"T2268: Expected 'Quiet', got '{result}'"

    def test_fan_speed_list_shows_pure(self, robovac):
        """Verify that the fan speed list shows 'Pure' (not 'Quiet') to users."""
        fan_speeds = robovac.getFanSpeeds()
        # getFanSpeeds() returns the KEYS from the mapping dict (title-cased)
        # This ensures the UI displays "Pure" even if the value is "Quiet"
        assert "Pure" in fan_speeds, (
            f"Expected 'Pure' in fan speed list for UI display, "
            f"got {fan_speeds}"
        )
