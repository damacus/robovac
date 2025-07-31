"""RoboVac 35C (T2117)"""

from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2117(RobovacModelDetails):

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
    robovac_features = RoboVacEntityFeature.EDGE | RoboVacEntityFeature.SMALL_ROOM
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 2,
        },
        RobovacCommand.DIRECTION: {
            "code": 3,
            "values": {
                "forward": "Forward",
                "back": "Back",
                "left": "Left",
                "right": "Right",
            },
        },
        RobovacCommand.MODE: {
            "code": 5,
            "values": {
                "auto": "Auto",
                "small_room": "SmallRoom",
                "spot": "Spot",
                "edge": "Edge",
                "nosweep": "Nosweep",
            },
        },
        RobovacCommand.STATUS: {
            "code": 15,
        },
        RobovacCommand.RETURN_HOME: {
            "code": 101,
        },
        RobovacCommand.FAN_SPEED: {
            "code": 102,
            "values": {
                "no_suction": "No_suction",
                "standard": "Standard",
                "boost_iq": "Boost_IQ",
                "max": "Max",
            },
        },
        RobovacCommand.LOCATE: {
            "code": 103,
        },
        RobovacCommand.BATTERY: {
            "code": 104,
        },
        RobovacCommand.ERROR: {
            "code": 106,
        },
    }
