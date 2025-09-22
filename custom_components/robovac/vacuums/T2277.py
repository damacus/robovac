"""eufy Clean L60 SES (T2277)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2277(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.CLEAN_SPOT
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
        RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.BOOST_IQ
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
                "auto": "BgoAEAUyAA===",
                "positioning": "BgoAEAVSAA===",
                "Paused": "CAoAEAUyAggB",  # capitalized in vacuum.py
                "room": "CAoCCAEQBTIA",
                "room_positioning": "CAoCCAEQBVIA",
                "room_pause": "CgoCCAEQBTICCAE=",
                "spot": "CAoCCAIQBTIA",
                "spot_positioning": "CAoCCAIQBVIA",
                "spot_pause": "CgoCCAIQBTICCAE=",
                "start_manual": "BAoAEAY=",
                "going_to_charge": "BBAHQgA=",
                "Charging": "BBADGgA=",  # capitalized in vacuum.py
                "completed": "BhADGgIIAQ==",
                "Standby": "AA==",  # capitalized in vacuum.py
                "Sleeping": "AhAB",  # capitalized in vacuum.py
                "BgoAEAUyAA===": "auto",
                "BgoAEAUyAA==": "auto",
                "BgoAEAVSAA===": "positioning",
                "CAoAEAUyAggB": "Paused",  # capitalized in vacuum.py
                "CAoCCAEQBTIA": "room",
                "CAoCCAEQBVIA": "room_positioning",
                "CgoCCAEQBTICCAE=": "room_pause",
                "CAoCCAIQBTIA": "spot",
                "CAoCCAIQBVIA": "spot_positioning",
                "CgoCCAIQBTICCAE=": "spot_pause",
                "BAoAEAY=": "start_manual",
                "BBAHQgA=": "going_to_charge",
                "BBADGgA=": "Charging",  # capitalized in vacuum.py
                "BhADGgIIAQ==": "completed",
                "AA==": "Standby",  # capitalized in vacuum.py
                "AhAB": "Sleeping",  # capitalized in vacuum.py
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
        # RobovacCommand.ERROR: {  # doesnt work, includes encrypted last error timestamp
        #    "code": 177,
        #    "values":
        #    {
        #        "DAiI6suO9dXszgFSAA==": "no_error",
        #        "FAjwudWorOPszgEaAqURUgQSAqUR": "Sidebrush stuck",
        #        "FAj+nMu7zuPszgEaAtg2UgQSAtg2": "Robot stuck",
        #        "DAjtzbfps+XszgFSAA==": "no_error",
        #        "DAiom9rd6eTszgFSAA==": "no_error",
        #        "DAia8JTV5OPszgFSAA==": "no_error",
        #        "DAj489bWsePszgFSAA==": "no_error",
        #        "ByIDCgEAUgA=": "no_error",
        #    }
        # },
    }
