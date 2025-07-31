"""RoboVac S1 Pro (T2080A)"""
from homeassistant.components.vacuum import (VacuumEntityFeature, VacuumActivity)
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2080(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE  # Not yet confirmed working
        | VacuumEntityFeature.RETURN_HOME  # Not yet confirmed working
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START  # Verified
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP  # Not yet confirmed working
        | VacuumEntityFeature.MAP
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
        | RoboVacEntityFeature.CONSUMABLES
    )
    commands = {
        # Received updated state bf7ef4e5de08b0b99an7pf (192.168.1.105:6668):
        # {'2': False, '5': 'smart', '6': 0, '7': 0, '8': 100, '9': 'normal', '10': 'low', '40': 'installed', '156': True, '158': 'Standard', '159': True, '161': 24, '163': 100}

        RobovacCommand.START_PAUSE: {
            "code": 2,
            # I've seen `'2': False` when ending a session (maybe when paused??)
            # I've also seen `'2': False` when actively vacuuming..
        },
        RobovacCommand.DIRECTION: {
            # Not working
            "code": 176,  # try 157 next??
            "values": ["forward", "back", "left", "right"],
        },
        # The below is copied from T2267.py - need to test.
        RobovacCommand.MODE: {
            # Not sure this is accurate
            "code": 152,
            "values": {
                "BBoCCAE=": "auto",
                "AggN": "pause",
                "AA==": "Spot",
                "AggG": "return",
                "AggO": "Nosweep",
                # "AggB": "AggB", # I keep seeing this value.. not really sure what it means! Room clean, maybe??
                # "BAgNGAE=": "BAgNGAE=",
            },
        },
        # The below is copied from vacuum.py, here: https://github.com/CodeFoodPixels/robovac/compare/main...maximoei:robovac:L60-support
        # Needs some verification as to how it mixes with this repo.
        RobovacCommand.STATUS: {
            "code": 153,
            "values": {
                "CAoAEAUyAggB": "Paused",
                "CAoCCAEQBTIA": "Room Cleaning",
                "CAoCCAEQBVIA": "Room Positioning",
                "DAoCCAEQBTICEAFSAA==": "Room Positioning",
                "CgoCCAEQBTICCAE=": "Room Paused",
                "BhAHQgBSAA==": "Standby",
                "BgoAEAUyAA==": "Standby",
                "BBAHQgA=": "Heading Home",
                "BBADGgA=": "Charging",
                "BhADGgIIAQ==": "Completed",
                "AA==": "Standby",
                "AgoA": "Heading Home",
                "AhAB": "Sleeping",
                "DAoCCAEQCRoCCAEyAA==": "Adding Water",
                "BhAJOgIQAg==": "Drying Mop",
                "CBAJGgA6AhAC": "Drying Mop",
                "ChAJGgIIAToCEAI=": "Drying Mop",
                "EAoCCAEQCRoCCAEyADoCEAE=": "Washing Mop",
                "BhAJOgIQAQ==": "Washing Mop",
                "AhAJ": "Removing Dirty Water",
                "BhAGGgIIAQ==": "Manual Control",  # Double check this
                # One of these next two (maybe both?) is "Emptying Dust", but I'm not sure which
                # "BxAJGgD6AQA=": "Emptying Dust",
                # "BRAJ+gEA": "Emptying Dust",
                "CgoAEAkaAggBMgA=": "Auto Cleaning",
            }
        },
        RobovacCommand.RETURN_HOME: {
            # Pretty sure this is correct, but untested
            "code": 152,
            "values": ["AggB"]
        },
        RobovacCommand.LOCATE: {
            "code": 103,
        },
        RobovacCommand.ERROR: {
            "code": 106,
        },
        RobovacCommand.FAN_SPEED: {
            # Verified
            "code": 158,
            "values": {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max"
            },
        },
        RobovacCommand.BATTERY: {
            # Verified
            # Seems that '8' is a duplicate of '163'
            "code": 163,
        },
        RobovacCommand.BOOST_IQ: {
            # Verified
            "code": 159,
        },
        RobovacCommand.CLEANING_TIME: {
            # Verified
            "code": 6,
        },
        RobovacCommand.CLEANING_AREA: {
            # Verified
            "code": 7,
        }
    }
    activity_mapping = {
        "AUTO": VacuumActivity.CLEANING,
        "POSITION": VacuumActivity.CLEANING,
        "Paused": VacuumActivity.PAUSED,
        "Auto Cleaning": VacuumActivity.CLEANING,
        "Room Cleaning": VacuumActivity.CLEANING,  # I've seen this when doing a room clean - navigating to the room and while cleaning it. Maybe 153 is mode, not status???
        "Room Positioning": VacuumActivity.CLEANING,
        "Room Paused": VacuumActivity.PAUSED,  # I've seen this when doing a room clean and hitting pause
        "SPOT": VacuumActivity.CLEANING,
        "SPOT_POSITION": VacuumActivity.CLEANING,
        "SPOT_PAUSE": VacuumActivity.PAUSED,
        "START_MANUAL": VacuumActivity.CLEANING,
        "Standby": VacuumActivity.IDLE,
        "Heading Home": VacuumActivity.RETURNING,  # I've seen this when heading home
        "Charging": VacuumActivity.DOCKED,
        "Completed": VacuumActivity.DOCKED,
        "Sleeping": VacuumActivity.IDLE,
        "Drying Mop": VacuumActivity.DOCKED,
        "Washing Mop": VacuumActivity.DOCKED,
        "Removing Dirty Water": VacuumActivity.DOCKED,
        "Emptying Dust": VacuumActivity.DOCKED,
        "Manual Control": VacuumActivity.CLEANING,
    }
