"""Compatibility helpers for Home Assistant VacuumActivity enum.

This module attempts to import :class:`~homeassistant.components.vacuum.VacuumActivity`
from Home Assistant. If Home Assistant is not installed, or the installed version
doesn't expose ``VacuumActivity`` (older core releases), we fall back to a local
``StrEnum`` that mirrors the values Home Assistant uses.  This keeps developer
utilities like ``robovac_logger.py`` working when executed outside a Home
Assistant environment while still providing the real enum when available.
"""

from __future__ import annotations

from enum import StrEnum
from importlib import import_module
from importlib.util import find_spec

VacuumActivity: type[StrEnum]


def _create_fallback_enum() -> type[StrEnum]:
    """Return a minimal VacuumActivity enum compatible with Home Assistant."""

    class _FallbackVacuumActivity(StrEnum):
        CLEANING = "cleaning"
        DOCKED = "docked"
        ERROR = "error"
        IDLE = "idle"
        PAUSED = "paused"
        RETURNING = "returning"

    return _FallbackVacuumActivity


_vacuum_spec = find_spec("homeassistant.components.vacuum")
if _vacuum_spec is not None:
    _vacuum_module = import_module("homeassistant.components.vacuum")
    _activity = getattr(_vacuum_module, "VacuumActivity", None)
    if _activity is None:
        VacuumActivity = _create_fallback_enum()
    else:
        VacuumActivity = _activity
else:
    VacuumActivity = _create_fallback_enum()

__all__ = ["VacuumActivity"]

