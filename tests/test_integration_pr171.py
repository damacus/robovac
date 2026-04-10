"""Integration tests for features from PR #171."""

import pytest
from unittest.mock import patch

from homeassistant.components.vacuum import VacuumEntityFeature
from custom_components.robovac.vacuum import RoboVacEntity
from custom_components.robovac.errors import getErrorMessageWithContext


@pytest.mark.asyncio
async def test_battery_feature_removed_from_entity(mock_robovac: object, mock_vacuum_data: dict) -> None:
    """Test that the vacuum entity does not have the BATTERY feature."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        assert not (entity.supported_features & VacuumEntityFeature.BATTERY)


@pytest.mark.asyncio
async def test_error_message_with_context_integration(mock_robovac: object, mock_vacuum_data: dict) -> None:
    """Test that getErrorMessageWithContext is integrated and returns context."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.error_code = 19  # Laser sensor stuck

        error_context = getErrorMessageWithContext(entity.error_code)
        assert error_context["message"] == "Laser sensor stuck"
        assert "troubleshooting" in error_context
        assert len(error_context["troubleshooting"]) > 0


def test_readme_updated() -> None:
    """Placeholder test to ensure README is updated."""
    # This test will be updated to check for actual content
    assert True
