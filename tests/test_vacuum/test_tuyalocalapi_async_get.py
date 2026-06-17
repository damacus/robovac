"""Tests for local Tuya status refresh behavior."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from custom_components.robovac.tuyalocalapi import (
    ConnectionTimeoutException,
    Message,
    TuyaDevice,
)
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.mark.asyncio
async def test_legacy_async_get_connects_before_waiting_for_response() -> None:
    """Test legacy GET status refresh waits only after connection is established."""
    device = TuyaDevice.__new__(TuyaDevice)
    device.version = (3, 3)
    device.gateway_id = "test-device"
    device.device_id = "test-device"
    device._queue = []
    device._listeners = {}
    device._connected = False
    device._backoff = False

    async def connect() -> None:
        device._connected = True

    async def receive(message: Message) -> None:
        assert device._connected is True
        assert device._queue == [message]

    device.async_connect = AsyncMock(side_effect=connect)
    device.async_receive = AsyncMock(side_effect=receive)

    await device.async_get()

    device.async_connect.assert_awaited_once()
    device.async_receive.assert_awaited_once()
    assert device._queue[0].command == Message.GET_COMMAND


@pytest.mark.asyncio
async def test_legacy_async_get_skips_status_request_during_backoff() -> None:
    """Test legacy GET status refresh does not wait while queue is backing off."""
    device = TuyaDevice.__new__(TuyaDevice)
    device.version = (3, 3)
    device._queue = []
    device._listeners = {}
    device._backoff = True

    device.async_connect = AsyncMock()
    device.async_receive = AsyncMock()

    await device.async_get()

    device.async_connect.assert_not_awaited()
    device.async_receive.assert_not_awaited()
    assert device._queue == []
    assert device._listeners == {}


@pytest.mark.asyncio
async def test_async_connect_records_connection_failure_on_error_dps_code() -> None:
    """Test connection timeouts update the error DPS without using dict keys."""
    device = TuyaDevice.__new__(TuyaDevice)
    device.model_details = SimpleNamespace(
        commands={RobovacCommand.ERROR: {"code": 177}}
    )
    device.device_id = "test-device"
    device.host = "192.0.2.10"
    device.port = 6668
    device.timeout = 0.1
    device.version = (3, 5)
    device._connected = False
    device._enabled = True
    device._last_connect_attempt = 0.0
    device._dps = {}
    device._LOGGER = MagicMock()

    with patch(
        "custom_components.robovac.tuyalocalapi.asyncio.open_connection",
        new=AsyncMock(side_effect=asyncio.TimeoutError),
    ):
        with pytest.raises(ConnectionTimeoutException):
            await device.async_connect()

    assert device._dps["177"] == "CONNECTION_FAILED"
