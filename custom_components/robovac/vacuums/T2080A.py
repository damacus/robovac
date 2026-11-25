"""RoboVac S1 Pro (T2080A)."""

from homeassistant.components.vacuum import VacuumEntityFeature

from .base import RobovacCommand, RobovacModelDetails
from .T2080 import T2080


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
            # DPS 6 contains elapsed cleaning minutes on this S1 Pro.
            # DPS 153 carries the actual encoded work status.
            **T2080.commands[RobovacCommand.STATUS],
            "values": {
                **T2080.commands[RobovacCommand.STATUS]["values"],
                # Observed with an EB14 alert. Expose generic error activity;
                # the error number itself is not decoded from this payload.
                "EgoAEAIaAggBMgIIAToECAEQAQ==": "Error",
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
    activity_mapping = dict(T2080.activity_mapping)
