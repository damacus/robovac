"""RoboVac 30C (T2118)"""

from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2118(RobovacModelDetails):

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
    robovac_features = RoboVacEntityFeature.EDGE | RoboVacEntityFeature.SMALL_ROOM
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 2,
            "values": {"start": True, "pause": False},
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
            "values": {
                "Charging": "Charging",
                "completed": "Completed",
                "Running": "Running",
                "standby": "Standby",
                "Sleeping": "Sleeping",
                "recharge_needed": "Recharge needed",
            },
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
            "values": {
                "0": "No error",
            },
        },
    }
