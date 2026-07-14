"""RoboVac S1 Pro (T2080A)."""

from homeassistant.components.vacuum import VacuumActivity, VacuumEntityFeature

from .base import RobovacCommand, RobovacModelDetails


class T2080A(RobovacModelDetails):
    """Model details for the alphanumeric T2080A S1 Pro."""

    homeassistant_features = (
        VacuumEntityFeature.STATE
        | VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.FAN_SPEED
    )
    robovac_features = 0
    protocol_version = (3, 3)
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 160,
            "values": {"start": True, "pause": False},
        },
        RobovacCommand.STATUS: {
            "code": 6,
            "values": {
                "0": "Standby",
                "1": "Cleaning",
                "2": "Paused",
                "5": "Returning",
                "34": "Docked",
            },
        },
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        },
        RobovacCommand.BATTERY: {"code": 8},
    }
    activity_mapping = {
        "Standby": VacuumActivity.IDLE,
        "Cleaning": VacuumActivity.CLEANING,
        "Paused": VacuumActivity.PAUSED,
        "Returning": VacuumActivity.RETURNING,
        "Docked": VacuumActivity.DOCKED,
    }
