"""eufy Clean L60 Hybrid SES (T2278)"""
from homeassistant.components.vacuum import (VacuumEntityFeature, VacuumActivity)
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2278(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )
    robovac_features = (
        RoboVacEntityFeature.CLEANING_TIME
        | RoboVacEntityFeature.CLEANING_AREA
        | RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.AUTO_RETURN
        | RoboVacEntityFeature.ROOM
        | RoboVacEntityFeature.ZONE
        | RoboVacEntityFeature.BOOST_IQ
        | RoboVacEntityFeature.MAP
    )
    commands = {
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                "standby": "AA==",
                "pause": "AggN",
                "stop": "AggG",
                "return": "AggG",
                "auto": "BBoCCAE=",
                "nosweep": "AggO",
                "AA==": "standby",
                "AggN": "pause",
                "AggG": "stop",
                "BBoCCAE=": "auto",
                "AggO": "nosweep"
            },
        },
        RobovacCommand.START_PAUSE: {  # via mode command
            "code": 152,
            "values": {
                "pause": "AggN",
            },
        },
        RobovacCommand.RETURN_HOME: {  # via mode command
            "code": 152,
            "values": {
                "return": "AggG",
            },
        },
        RobovacCommand.STATUS: {  # works
            "code": 153,
            "values": {
                "AA==": "Standby",
                "AggB": "Paused",
                "AhAB": "Sleeping",
                "BBADGgA=": "Charging",
                "BBAHQgA=": "Heading Home",
                "BgoAEAUyAA==": "Cleaning",
                "BgoAEAVSAA==": "Positioning",
                "BhADGgIIAQ==": "Completed",
                "CAoAEAUyAggB": "Paused",
                "CAoCCAEQBTIA": "Room Cleaning",
                "CAoCCAEQBVIA": "Room Positioning",
                "CAoCCAIQBTIA": "Zone Cleaning",
                "CAoCCAIQBVIA": "Zone Positioning",
                "CgoCCAEQBTICCAE=": "Room Paused",
                "CgoCCAIQBTICCAE=": "Zone Paused",
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

        RobovacCommand.LOCATE: {
            "code": 160,
            "values": {
                "locate": "true",
            }
        },
        RobovacCommand.BATTERY: {
            "code": 163,
        },
    }

    activity_mapping = {
        "Cleaning": VacuumActivity.CLEANING,
        "Charging": VacuumActivity.DOCKED,
        "Completed": VacuumActivity.DOCKED,
        "Heading Home": VacuumActivity.RETURNING,
        "Paused": VacuumActivity.PAUSED,
        "Positioning": VacuumActivity.CLEANING,
        "Room Cleaning": VacuumActivity.CLEANING,
        "Room Paused": VacuumActivity.PAUSED,
        "Room Positioning": VacuumActivity.CLEANING,
        "Sleeping": VacuumActivity.IDLE,
        "Standby": VacuumActivity.IDLE,
        "Zone Cleaning": VacuumActivity.CLEANING,
        "Zone Paused": VacuumActivity.PAUSED,
        "Zone Positioning": VacuumActivity.CLEANING,
    }
