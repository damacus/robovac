"""Tests for local Tuya status refresh behavior."""

from unittest.mock import AsyncMock

import pytest

from custom_components.robovac.tuyalocalapi import Message, TuyaDevice


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
