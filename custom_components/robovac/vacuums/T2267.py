"""RoboVac L60 (T2267)"""
from homeassistant.components.vacuum import (VacuumEntityFeature, VacuumActivity)
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2267(RobovacModelDetails):
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
        RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.BOOST_IQ
    )
    commands = {
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                "auto": "BBoCCAE=",
                "pause": "AggN",
                "spot": "AggD",
                "return": "AggG",
                "nosweep": "AggO",
            },
        },
        RobovacCommand.STATUS: {
            "code": 153,
            "values": {
                # Cleaning states
                "BgoAEAUyAA==": "Cleaning",
                "BgoAEAVSAA==": "Positioning",
                # Paused states
                "CAoAEAUyAggB": "Paused",
                "AggB": "Paused",
                # Room cleaning states
                "CAoCCAEQBTIA": "Room Cleaning",
                "CAoCCAEQBVIA": "Room Positioning",
                "CgoCCAEQBTICCAE=": "Room Paused",
                # Zone cleaning states
                "CAoCCAIQBTIA": "Zone Cleaning",
                "CAoCCAIQBVIA": "Zone Positioning",
                "CgoCCAIQBTICCAE=": "Zone Paused",
                # Navigation states
                "BAoAEAY=": "Remote Control",
                "BBAHQgA=": "Heading Home",
                # Charging/docked states
                "BBADGgA=": "Charging",
                "BhADGgIIAQ==": "Completed",
                # Idle states
                "AA==": "Standby",
                "AhAB": "Sleeping",
                # Error states
                "BQgNEIsB": "Off Ground",
            },
        },
        RobovacCommand.DIRECTION: {
            "code": 155,
            "values": {
                "brake": "brake",
                "forward": "forward",
                "back": "back",
                "left": "left",
                "right": "right",
            },
        },
        RobovacCommand.START_PAUSE: {
            # Pause is sent via MODE command (code 152) with protobuf-encoded value
            # "AggN" encodes ModeCtrlRequest.Method.PAUSE_TASK (13)
            # "AggO" encodes ModeCtrlRequest.Method.RESUME_TASK (14)
            "code": 152,
            "values": {
                "pause": "AggN",
                "resume": "AggO",
            },
        },
        RobovacCommand.STOP: {
            # Stop is sent via MODE command (code 152) with protobuf-encoded value
            # "AggM" encodes ModeCtrlRequest.Method.STOP_TASK (12)
            "code": 152,
            "values": {
                "stop": "AggM",
            },
        },
        RobovacCommand.DO_NOT_DISTURB: {
            "code": 157,
        },
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "boost_iq": "Boost_IQ",
            },
        },
        RobovacCommand.BOOST_IQ: {
            "code": 159,
        },
        RobovacCommand.LOCATE: {
            "code": 160,
        },
        RobovacCommand.BATTERY: {
            "code": 163,
        },
        RobovacCommand.CONSUMABLES: {
            "code": 168,
        },
        RobovacCommand.RETURN_HOME: {
            # Return home is sent via MODE command (code 152) with protobuf-encoded value
            # "AggG" encodes ModeCtrlRequest.Method.START_GOHOME (6)
            "code": 152,
            "values": {
                "return": "AggG",
            },
        },
        RobovacCommand.ERROR: {
            "code": 177,
        }
    }

    activity_mapping = {
        # Cleaning states
        "Cleaning": VacuumActivity.CLEANING,
        "Positioning": VacuumActivity.CLEANING,
        "Room Cleaning": VacuumActivity.CLEANING,
        "Room Positioning": VacuumActivity.CLEANING,
        "Zone Cleaning": VacuumActivity.CLEANING,
        "Zone Positioning": VacuumActivity.CLEANING,
        "Remote Control": VacuumActivity.CLEANING,
        # Paused states
        "Paused": VacuumActivity.PAUSED,
        "Room Paused": VacuumActivity.PAUSED,
        "Zone Paused": VacuumActivity.PAUSED,
        # Returning states
        "Heading Home": VacuumActivity.RETURNING,
        # Docked states
        "Charging": VacuumActivity.DOCKED,
        "Completed": VacuumActivity.DOCKED,
        # Idle states
        "Standby": VacuumActivity.IDLE,
        "Sleeping": VacuumActivity.IDLE,
        # Error states
        "Off Ground": VacuumActivity.ERROR,
    }

    # Patterns for STATUS codes with dynamic content (prefix, suffix, status_name)
    # These match base64-encoded protobuf messages with embedded timestamps
    status_patterns = [
        # Positioning codes: start with "DA" (0c08), end with "FSAA==" (5200)
        # The middle bytes contain a timestamp that changes with each update
        ("DA", "FSAA==", "Positioning"),
    ]

    # Patterns for ERROR codes - some devices send status messages on the ERROR DPS
    # These patterns map such messages to "no_error" to prevent false error states
    error_patterns = [
        # Positioning/relocating status sent on ERROR DPS - not an actual error
        ("DA", "FSAA==", "no_error"),
    ]
