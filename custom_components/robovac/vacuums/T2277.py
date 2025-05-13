"""eufy Clean L60 SES (T2277)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2277(RobovacModelDetails):
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
    robovac_features = (
        RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.BOOST_IQ
    )
    commands = {
        RobovacCommand.MODE: {
            "code": 152,
            "values": ["AggN", "AA==", "AggG", "BBoCCAE=", "AggO"],
        },
        RobovacCommand.STATUS: 173,
        RobovacCommand.RETURN_HOME: {
            "code": 153,
            "values": ["AggB"]
        },
        RobovacCommand.FAN_SPEED: {
            "code": 154,
            "values": ["AgkBCgIKAQoDCgEKBAoB"]
        },
        RobovacCommand.LOCATE: {
            "code": 153,
            "values": ["AggC"]
        },
        RobovacCommand.BATTERY: 172,
        RobovacCommand.ERROR: 169,
        # RoboVacEntityFeature.DO_NOT_DISTURB: {
        #     "code": 163,
        #     "values": ["AQ==", "AA=="],
        # },
        # RoboVacEntityFeature.BOOST_IQ: {
        #     "code": 161,
        #     "values": ["AQ==", "AA=="],
        # },
    }
