"""Tests for the map camera's route polling."""

import asyncio
from unittest.mock import MagicMock

import pytest

# Home Assistant's camera platform needs turbojpeg, which a bare dev env lacks.
pytest.importorskip("turbojpeg")

from custom_components.robovac.camera import RoboVacMapCoordinator  # noqa: E402


def _coordinator() -> RoboVacMapCoordinator:
    """Build a coordinator without Home Assistant's coordinator machinery."""
    coordinator = object.__new__(RoboVacMapCoordinator)
    coordinator._session = MagicMock()
    coordinator._layout = MagicMock()
    coordinator._poll_lock = asyncio.Lock()
    calls: list[int] = []
    release = asyncio.Event()

    async def _slow_poll() -> None:
        calls.append(1)
        await release.wait()

    coordinator._async_poll_route_locked = _slow_poll  # type: ignore[method-assign]
    coordinator.calls = calls  # type: ignore[attr-defined]
    coordinator.release = release  # type: ignore[attr-defined]
    return coordinator


def test_overlapping_route_polls_are_skipped() -> None:
    """A poll that arrives while another is pending does not run."""
    async def scenario() -> list[int]:
        coordinator = _coordinator()
        first = asyncio.create_task(coordinator.async_poll_route())
        await asyncio.sleep(0)
        await coordinator.async_poll_route()  # arrives while the first is pending
        coordinator.release.set()  # type: ignore[attr-defined]
        await first
        await coordinator.async_poll_route()  # lock is free again
        return coordinator.calls  # type: ignore[attr-defined]

    assert len(asyncio.run(scenario())) == 2
