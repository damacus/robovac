"""Tests for RoboVacEntity.async_update error handling paths."""

import pytest
from unittest.mock import patch, AsyncMock

from custom_components.robovac.vacuum import RoboVacEntity, UPDATE_RETRIES
from custom_components.robovac.tuyalocalapi import TuyaException


@pytest.mark.asyncio
async def test_async_update_skips_unsupported_model(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test async_update returns early when model is unsupported."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity._attr_error_code = "UNSUPPORTED_MODEL"

        await entity.async_update()

        mock_robovac.async_get.assert_not_called()


@pytest.mark.asyncio
async def test_async_update_sets_error_when_no_ip(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test async_update sets IP_ADDRESS error when ip_address is empty."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity._attr_ip_address = ""

        await entity.async_update()

        assert entity._attr_error_code == "IP_ADDRESS"
        mock_robovac.async_get.assert_not_called()


@pytest.mark.asyncio
async def test_async_update_sets_error_when_vacuum_not_initialized(
    mock_robovac, mock_vacuum_data,
) -> None:
    """Test async_update sets INITIALIZATION_FAILED when vacuum is None."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

    entity.vacuum = None
    entity._attr_error_code = None

    await entity.async_update()

    assert entity._attr_error_code == "INITIALIZATION_FAILED"


@pytest.mark.asyncio
async def test_async_update_increments_failure_count_on_tuya_exception(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test async_update increments update_failures on TuyaException."""
    mock_robovac.async_get = AsyncMock(side_effect=TuyaException("connection lost"))

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        assert entity.update_failures == 0

        await entity.async_update()

        assert entity.update_failures == 1
        assert entity._attr_error_code != "CONNECTION_FAILED"


@pytest.mark.asyncio
async def test_async_update_sets_connection_failed_after_max_retries(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test async_update sets CONNECTION_FAILED after UPDATE_RETRIES failures."""
    mock_robovac.async_get = AsyncMock(side_effect=TuyaException("connection lost"))

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        for _ in range(UPDATE_RETRIES):
            await entity.async_update()

        assert entity.update_failures == UPDATE_RETRIES
        assert entity._attr_error_code == "CONNECTION_FAILED"


@pytest.mark.asyncio
async def test_async_update_resets_failure_count_on_success(
    mock_robovac, mock_vacuum_data
) -> None:
    """Test async_update resets update_failures to 0 on successful update."""
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        entity.update_failures = 2

        await entity.async_update()

        assert entity.update_failures == 0
