"""RoboVac L60 (T2267)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2267(RobovacModelDetails):
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
        RobovacCommand.MODE: {
            "code": 152,
            "values": ["AggN", "AA==", "AggG", "BBoCCAE=", "AggO"],
        },
        RobovacCommand.STATUS: {
            "code": 153,
            "values": [
                "BgoAEAUyAA===",
                "BgoAEAVSAA===",
                "CAoAEAUyAggB",
                "CAoCCAEQBTIA",
                "CAoCCAEQBVIA",
                "CgoCCAEQBTICCAE=",
                "CAoCCAIQBTIA",
                "CAoCCAIQBVIA",
                "CgoCCAIQBTICCAE=",
                "BAoAEAY=",
                "BBAHQgA=",
                "BBADGgA=",
                "BhADGgIIAQ==",
                "AA==",
                "AhAB",
            ],
        },
        RobovacCommand.DIRECTION: {
            "code": 155,
            "values": ["Brake", "Forward", "Back", "Left", "Right"],
        },
        RobovacCommand.START_PAUSE: 156,
        RobovacCommand.DO_NOT_DISTURB: 157,
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": ["Quiet", "Standard", "Turbo", "Max"],
        },
        RobovacCommand.BOOST_IQ: 159,
        RobovacCommand.LOCATE: 160,
        RobovacCommand.BATTERY: 163,
        RobovacCommand.CONSUMABLES: 168,
        RobovacCommand.RETURN_HOME: 173,
        RobovacCommand.ERROR: 177
    }
