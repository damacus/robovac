"""Tests for rate-limited logging in RoboVac vacuum entity."""

import time
from unittest.mock import MagicMock, patch

import pytest
from typing import Any

from custom_components.robovac.vacuum import RoboVacEntity


@pytest.mark.asyncio
async def test_no_data_warning_logged_once(mock_robovac, mock_vacuum_data: Any, caplog) -> None:
    """Test that no data warning is logged only once initially."""
    # Arrange
    mock_robovac._dps = None

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act - call update_entity_values multiple times
        entity.update_entity_values()
        entity.update_entity_values()
        entity.update_entity_values()

        # Assert - warning should appear only once
        warning_count = sum(
            1 for record in caplog.records
            if record.levelname == "WARNING"
            and "no data points available" in record.message
        )
        assert warning_count == 1


@pytest.mark.asyncio
async def test_no_data_warning_logged_after_threshold(mock_robovac, mock_vacuum_data: Any, caplog) -> None:
    """Test that no data warning is logged again after 5 minute threshold."""
    # Arrange
    mock_robovac._dps = None

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act - first call logs warning
        entity.update_entity_values()
        initial_warning_count = sum(
            1 for record in caplog.records
            if record.levelname == "WARNING"
            and "no data points available" in record.message
        )

        # Simulate time passing (5 minutes + 1 second)
        entity._last_no_data_warning_time = time.time() - 301

        # Call again after threshold
        entity.update_entity_values()

        # Assert - warning should appear twice
        final_warning_count = sum(
            1 for record in caplog.records
            if record.levelname == "WARNING"
            and "no data points available" in record.message
        )
        assert initial_warning_count == 1
        assert final_warning_count == 2


@pytest.mark.asyncio
async def test_no_data_warning_not_logged_before_threshold(mock_robovac, mock_vacuum_data: Any, caplog) -> None:
    """Test that no data warning is not logged again before 5 minute threshold."""
    # Arrange
    mock_robovac._dps = None

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act - first call logs warning
        entity.update_entity_values()
        initial_warning_count = sum(
            1 for record in caplog.records
            if record.levelname == "WARNING"
            and "no data points available" in record.message
        )

        # Simulate time passing (less than 5 minutes)
        entity._last_no_data_warning_time = time.time() - 60

        # Call again before threshold
        entity.update_entity_values()

        # Assert - warning should still appear only once
        final_warning_count = sum(
            1 for record in caplog.records
            if record.levelname == "WARNING"
            and "no data points available" in record.message
        )
        assert initial_warning_count == 1
        assert final_warning_count == 1


@pytest.mark.asyncio
async def test_data_recovery_info_logged(mock_robovac, mock_vacuum_data: Any, caplog) -> None:
    """Test that info message is logged when data becomes available after warning."""
    # Arrange
    mock_robovac._dps = None

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act - first call with no data logs warning
        entity.update_entity_values()

        # Now provide data
        mock_robovac._dps = {"103": 100, "15": "Charging", "106": 0}
        entity.update_entity_values()

        # Assert - info message should be logged
        info_messages = [
            record for record in caplog.records
            if record.levelname == "INFO"
            and "Data points now available" in record.message
        ]
        assert len(info_messages) == 1


@pytest.mark.asyncio
async def test_no_info_logged_when_data_always_available(mock_robovac, mock_vacuum_data: Any, caplog) -> None:
    """Test that no info message is logged when data is always available."""
    # Arrange
    mock_robovac._dps = {"103": 100, "15": "Charging", "106": 0}

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act - call multiple times with data always available
        entity.update_entity_values()
        entity.update_entity_values()
        entity.update_entity_values()

        # Assert - no info message should be logged
        info_messages = [
            record for record in caplog.records
            if record.levelname == "INFO"
            and "Data points now available" in record.message
        ]
        assert len(info_messages) == 0


@pytest.mark.asyncio
async def test_warning_state_resets_after_data_recovery(mock_robovac, mock_vacuum_data: Any, caplog) -> None:
    """Test that warning state resets after data recovery and can be logged again."""
    # Arrange
    mock_robovac._dps = None

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act - first no data period
        entity.update_entity_values()
        first_warning_count = sum(
            1 for record in caplog.records
            if record.levelname == "WARNING"
            and "no data points available" in record.message
        )

        # Data becomes available
        mock_robovac._dps = {"103": 100, "15": "Charging", "106": 0}
        entity.update_entity_values()

        # Data becomes unavailable again
        mock_robovac._dps = None
        entity.update_entity_values()

        # Assert - warning should be logged twice (once for each no-data period)
        final_warning_count = sum(
            1 for record in caplog.records
            if record.levelname == "WARNING"
            and "no data points available" in record.message
        )
        assert first_warning_count == 1
        assert final_warning_count == 2
