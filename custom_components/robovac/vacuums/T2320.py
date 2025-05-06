from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand


class T2320:
    homeassistant_features = (
        VacuumEntityFeature.BATTERY
        # | VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
        # | VacuumEntityFeature.MAP
    )
    robovac_features = (
        # RoboVacEntityFeature.CLEANING_TIME
        # RoboVacEntityFeature.CLEANING_AREA
        RoboVacEntityFeature.DO_NOT_DISTURB
        # RoboVacEntityFeature.AUTO_RETURN
        # RoboVacEntityFeature.ROOM
        # RoboVacEntityFeature.ZONE
        | RoboVacEntityFeature.BOOST_IQ
        # RoboVacEntityFeature.MAP
        # RoboVacEntityFeature.CONSUMABLES
    )
    commands = {
        RobovacCommand.MODE: {  # works   (Start Auto and Return dock commands tested)
            "code": 152,
            "values": ["AggN", "AA==", "AggG", "BBoCCAE=", "AggO"],
        },
        RobovacCommand.STATUS: 173,  # works
        RobovacCommand.RETURN_HOME: {  # works
            "code": 153,
            "values": ["AggB"]
        },
        RobovacCommand.FAN_SPEED: {  # Works
            "code": 154,
            "values": ["AgkBCgIKAQoDCgEKBAoB"]
        },
        RobovacCommand.LOCATE: {  # Works
            "code": 153,
            "values": ["AggC"]
        },
        RobovacCommand.BATTERY: 172,  # Works
        RobovacCommand.ERROR: 169,  # works
        # These command may have been added to the base.py if not they need codes adding
        # RoboVacEntityFeature.CLEANING_TIME: 0,
        # RoboVacEntityFeature.CLEANING_AREA: 0,
        RoboVacEntityFeature.DO_NOT_DISTURB: {  # Works
            "code": 163,
            "values": ["AQ==", "AA=="],
        },
        # RoboVacEntityFeature.AUTO_RETURN: 0,
        # RoboVacEntityFeature.ROOM: 0,
        # RoboVacEntityFeature.ZONE: 0,
        RoboVacEntityFeature.BOOST_IQ: {  # Works
            "code": 161,
            "values": ["AQ==", "AA=="],
        },
        # RoboVacEntityFeature.MAP: 0,
        # RoboVacEntityFeature.CONSUMABLES: 0,
    }
