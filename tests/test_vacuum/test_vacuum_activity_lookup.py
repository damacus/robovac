"""Tests for vacuum activity mapping helpers."""

from homeassistant.components.vacuum import VacuumActivity

from custom_components.robovac.vacuum import _lookup_activity


def test_lookup_activity_case_insensitive() -> None:
    mapping = {"Paused": VacuumActivity.PAUSED, "auto": VacuumActivity.CLEANING}
    assert _lookup_activity(mapping, "paused") == VacuumActivity.PAUSED
    assert _lookup_activity(mapping, "AUTO") == VacuumActivity.CLEANING
    assert _lookup_activity(mapping, "unknown") is None
