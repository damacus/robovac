"""eufy Clean L60 Hybrid SES (T2278)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2278(RobovacModelDetails):
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
            "values": {
                "small_room": "AA==",
                "pause": "AggN",
                "edge": "AggG",
                "auto": "BBoCCAE=",
                "nosweep": "AggO",
            },
        },
        RobovacCommand.STATUS: {
            "code": 173,
        },
        RobovacCommand.RETURN_HOME: {
            "code": 153,
            "values": {
                "return_home": "AggB",
            }
        },
        RobovacCommand.FAN_SPEED: {
            "code": 154,
            "values": {
                "fan_speed": "AgkBCgIKAQoDCgEKBAoB",
            }
        },
        RobovacCommand.LOCATE: {
            "code": 153,
            "values": {
                "locate": "AggC",
            }
        },
        RobovacCommand.BATTERY: {
            "code": 172,
        },
        RobovacCommand.ERROR: {
            "code": 169,
        },
    }
