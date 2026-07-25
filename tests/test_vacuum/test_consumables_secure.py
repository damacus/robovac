import pytest
import base64
from unittest.mock import patch
from custom_components.robovac.vacuum import RoboVacEntity
from custom_components.robovac.vacuums.base import RoboVacEntityFeature


@pytest.mark.asyncio
async def test_consumables_parsing_json(mock_robovac, mock_vacuum_data):
    """Test that consumables data in JSON format is correctly parsed."""
    # Data in valid JSON format
    raw_data = '{"consumable": {"duration": 200}, "active": true}'
    encoded_data = base64.b64encode(raw_data.encode("ascii")).decode("ascii")

    mock_robovac._dps = {"142": encoded_data}
    mock_robovac.getRoboVacFeatures.return_value = RoboVacEntityFeature.CONSUMABLES
    mock_robovac.getDpsCodes.return_value = {"CONSUMABLES": ["142"]}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.update_entity_values()

        assert entity._attr_consumables == 200


@pytest.mark.asyncio
async def test_consumables_parsing_invalid(mock_robovac, mock_vacuum_data):
    """Test that invalid consumables data doesn't crash the integration."""
    # Invalid data
    raw_data = "not a dict"
    encoded_data = base64.b64encode(raw_data.encode("ascii")).decode("ascii")

    mock_robovac._dps = {"142": encoded_data}
    mock_robovac.getRoboVacFeatures.return_value = RoboVacEntityFeature.CONSUMABLES
    mock_robovac.getDpsCodes.return_value = {"CONSUMABLES": ["142"]}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        # This should not raise an exception
        entity.update_entity_values()

        assert entity._attr_consumables is None
