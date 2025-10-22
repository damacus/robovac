"""eufy Clean X8 Pro SES (T2276)

WARNING: This model has known communication issues.
Users report "Incomplete read" errors and empty data points.
See docs/ISSUE_42_T2276_INVESTIGATION.md for details.

If you have this model, please help by providing device data via GitHub Issue #42.
"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2276(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )
    robovac_features = (
        RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.BOOST_IQ
    )
    commands = {
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                "small_room": "AA==",
                "pause": "AggN",
                "edge": "AggG",
                "auto": "BBoCCAE=",
                "nosweep": "AggO",
            },
        },
        RobovacCommand.STATUS: {
            "code": 173,
        },
        RobovacCommand.RETURN_HOME: {
            "code": 153,
            "values": {
                "return_home": "AggB",
            }
        },
        RobovacCommand.FAN_SPEED: {
            "code": 154,
            "values": {
                "fan_speed": "AgkBCgIKAQoDCgEKBAoB",
            }
        },
        RobovacCommand.LOCATE: {
            "code": 153,
            "values": {
                "locate": "AggC",
            }
        },
        RobovacCommand.BATTERY: {
            "code": 172,
        },
        RobovacCommand.ERROR: {
            "code": 169,
        },
    }
