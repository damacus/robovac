"""Tests for base-station maintenance activity mapping."""

import pytest
from homeassistant.components.vacuum import VacuumActivity

from custom_components.robovac.vacuum import _activity_from_station_maintenance


@pytest.mark.parametrize(
    "status",
    [
        "RollAutoCleaning",
        "DustCollecting",
        "SelfCleaning",
        "MopWashing",
        "Drying",
    ],
)
def test_station_maintenance_reports_docked(status: str) -> None:
    """The robot sits in the dock while the station cleans itself."""
    assert _activity_from_station_maintenance(status) == VacuumActivity.DOCKED


def test_station_maintenance_is_case_insensitive() -> None:
    """Device responses are matched case-insensitively across the integration."""
    assert (
        _activity_from_station_maintenance("rollautocleaning")
        == VacuumActivity.DOCKED
    )
    assert (
        _activity_from_station_maintenance("ROLLAUTOCLEANING")
        == VacuumActivity.DOCKED
    )


@pytest.mark.parametrize("status", ["Running", "Charging", "Paused", "", None, 0])
def test_non_station_statuses_are_not_claimed(status: object) -> None:
    """Anything else falls through to the existing chain untouched."""
    assert _activity_from_station_maintenance(status) is None  # type: ignore[arg-type]
