"""Eufy Robot Vacuum and Mop X9 Pro with Auto-Clean Station (T2320)"""

from homeassistant.components.vacuum import VacuumActivity, VacuumEntityFeature

from .base import RobovacCommand, RoboVacEntityFeature, RobovacModelDetails


class T2320(RobovacModelDetails):
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
        | RoboVacEntityFeature.CLEANING_TIME
        | RoboVacEntityFeature.CLEANING_AREA
        | RoboVacEntityFeature.MAP
    )
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 152,  # Same as MODE, uses protobuf-encoded values like T2267
            "values": {
                "pause": "AggN",  # Protobuf: ModeCtrlRequest.Method.PAUSE_TASK
                "resume": "AggO",  # Protobuf: ModeCtrlRequest.Method.RESUME_TASK
            },
        },
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                "auto": "BBoCCAE=",  # Protobuf: ModeCtrlRequest.Method.START_AUTO_CLEAN
                "pause": "AggN",  # Protobuf: ModeCtrlRequest.Method.PAUSE_TASK
                "return": "AggG",  # Protobuf: ModeCtrlRequest.Method.START_GOHOME
                "small_room": "small_room",
                "single_room": "single_room",
            },
        },
        RobovacCommand.STATUS: {
            "code": 177,
            "values": {
                # Protobuf-encoded status values (similar to T2080/T2267)
                # Cleaning states
                "BgoAEAUyAA==": "Auto Cleaning",
                "BgoAEAVSAA==": "Positioning",
                "CgoAEAUyAhABUgA=": "Auto Cleaning",
                "CgoAEAkaAggBMgA=": "Auto Cleaning",
                # Room cleaning states
                "CAoCCAEQBTIA": "Room Cleaning",
                "CAoCCAEQBVIA": "Room Positioning",
                "CgoCCAEQBTICCAE=": "Room Paused",
                "DAoCCAEQBTICEAFSAA==": "Room Positioning",
                # Zone cleaning states
                "CAoCCAIQBTIA": "Zone Cleaning",
                "CAoCCAIQBVIA": "Zone Positioning",
                "CgoCCAIQBTICCAE=": "Zone Paused",
                # Paused states
                "CAoAEAUyAggB": "Paused",
                "AggB": "Paused",
                # Navigation states
                "BBAHQgA=": "Heading Home",
                "AgoA": "Heading Home",
                "CgoAEAcyAggBQgA=": "Temporary Return",
                "DAoCCAEQBzICCAFCAA==": "Temporary Return",
                # Charging/docked states
                "BBADGgA=": "Charging",
                "BhADGgIIAQ==": "Completed",
                "DAoCCAEQAxoAMgIIAQ==": "Charge Mid-Clean",
                # Idle states
                "AA==": "Standby",
                "BhAHQgBSAA==": "Standby",
                "AhAB": "Sleeping",
                # Station states (X9 Pro has auto-clean station)
                "DAoAEAUaADICEAFSAA==": "Adding Water",
                "DAoCCAEQCRoCCAEyAA==": "Adding Water",
                "DgoAEAkaAggBMgA6AhAB": "Adding Water",
                "BhAJOgIQAg==": "Drying Mop",
                "CBAJGgA6AhAC": "Drying Mop",
                "ChAJGgIIAToCEAI=": "Drying Mop",
                "DgoAEAUaAggBMgIQAVIA": "Washing Mop",
                "EAoCCAEQCRoCCAEyADoCEAE=": "Washing Mop",
                "BhAJOgIQAQ==": "Washing Mop",
                "AhAJ": "Removing Dirty Water",
                "BRAJ+gEA": "Emptying Dust",
                "DQoCCAEQCTICCAH6AQA=": "Remove Dust Mid-Clean",
                # Manual control
                "BhAGGgIIAQ==": "Manual Control",
                "BAoAEAY=": "Remote Control",
                # Error state
                "CAoAEAIyAggB": "Error",
            },
        },
        RobovacCommand.RETURN_HOME: {
            # Return home is sent via MODE command (code 152) with protobuf-encoded value
            # "AggG" encodes ModeCtrlRequest.Method.START_GOHOME (6)
            "code": 152,
            "values": {
                "return": "AggG",
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
        RobovacCommand.FAN_SPEED: {
            "code": 154,
            "values": {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "boost_iq": "Boost_IQ",
            },
        },
        RobovacCommand.LOCATE: {
            "code": 160,
        },
        RobovacCommand.BATTERY: {
            "code": 172,
        },
        RobovacCommand.ERROR: {
            "code": 169,
        },
        RobovacCommand.BOOST_IQ: {
            "code": 159,
        },
        RobovacCommand.CLEANING_TIME: {
            "code": 6,
        },
        RobovacCommand.CLEANING_AREA: {
            "code": 7,
        },
        RobovacCommand.ERROR: {
            "code": 177,
        },
    }

    activity_mapping = {
        # Cleaning states
        "Auto Cleaning": VacuumActivity.CLEANING,
        "Positioning": VacuumActivity.CLEANING,
        "Room Cleaning": VacuumActivity.CLEANING,
        "Room Positioning": VacuumActivity.CLEANING,
        "Zone Cleaning": VacuumActivity.CLEANING,
        "Zone Positioning": VacuumActivity.CLEANING,
        "Manual Control": VacuumActivity.CLEANING,
        "Remote Control": VacuumActivity.CLEANING,
        # Paused states
        "Paused": VacuumActivity.PAUSED,
        "Room Paused": VacuumActivity.PAUSED,
        "Zone Paused": VacuumActivity.PAUSED,
        # Returning states
        "Heading Home": VacuumActivity.RETURNING,
        "Temporary Return": VacuumActivity.RETURNING,
        # Docked states
        "Charging": VacuumActivity.DOCKED,
        "Completed": VacuumActivity.DOCKED,
        "Charge Mid-Clean": VacuumActivity.DOCKED,
        "Adding Water": VacuumActivity.DOCKED,
        "Drying Mop": VacuumActivity.DOCKED,
        "Washing Mop": VacuumActivity.DOCKED,
        "Removing Dirty Water": VacuumActivity.DOCKED,
        "Emptying Dust": VacuumActivity.DOCKED,
        "Remove Dust Mid-Clean": VacuumActivity.DOCKED,
        # Idle states
        "Standby": VacuumActivity.IDLE,
        "Sleeping": VacuumActivity.IDLE,
        # Error state
        "Error": VacuumActivity.ERROR,
    }

    # Patterns for STATUS codes with dynamic content (prefix, suffix, status_name)
    # These match base64-encoded protobuf messages with embedded timestamps
    status_patterns = [
        # Positioning codes: start with "DA" (0c08), end with "FSAA==" (5200)
        # The middle bytes contain a timestamp that changes with each update
        ("DA", "FSAA==", "Positioning"),
        ("Dw", "BSAA==", "Washing Mop"),
    ]

    # Patterns for ERROR codes - some devices send status messages on the ERROR DPS
    # These patterns map such messages to "no_error" to prevent false error states
    error_patterns = [
        # Positioning/relocating status sent on ERROR DPS - not an actual error
        ("DA", "FSAA==", "no_error"),
        ("Dw", "BSAA==", "no_error"),
    ]
