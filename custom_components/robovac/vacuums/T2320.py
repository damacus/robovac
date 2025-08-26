"""Eufy Robot Vacuum and Mop X9 Pro with Auto-Clean Station (T2320)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2320(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.BATTERY
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
        RobovacCommand.START_PAUSE: {
            "code": 2,
            "values": {
                "start": True,
                "pause": False
            },
        },
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                "auto": "auto",
                "return": "return",
                "pause": "pause",
                "small_room": "small_room",
                "single_room": "single_room"
            },
        },
        RobovacCommand.STATUS: {
            "code": 173,
        },
        RobovacCommand.RETURN_HOME: {
            "code": 153,
            "values": {
                "return_home": True
            }
        },
        RobovacCommand.FAN_SPEED: {
            "code": 154,
            "values": {
                "Standard": "standard",
                "Boost IQ": "boost_iq",
                "Max": "max",
                "Quiet": "Quiet",
            },
        },
        RobovacCommand.LOCATE: {
            "code": 153,
            "values": {
                "locate": True
            }
        },
        RobovacCommand.BATTERY: {
            "code": 172,
        },
        RobovacCommand.ERROR: {
            "code": 169,
        },
    }
