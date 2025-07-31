"""RoboVac LR30 Hybrid (T2193)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2193(RobovacModelDetails):
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
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
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
