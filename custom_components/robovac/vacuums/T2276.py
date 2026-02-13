"""eufy Clean X8 Pro SES (T2276)

Protocol 3.5 device using standard Tuya DPS codes (same structure as T2128).
Previously misconfigured with protobuf-encoded DPS 152-173 which caused
"Incomplete read" errors (Issue #42). The actual device responds on protocol
3.5 with human-readable DPS values on codes 1-135.
"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2276(RobovacModelDetails):
    protocol_version = 3.5
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
        | RoboVacEntityFeature.ROOM
    )
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 2,
            "values": {"start": True, "pause": False},
        },
        RobovacCommand.MODE: {
            "code": 5,
            "values": {
                # T2276 uses lowercase "auto" (unlike T2128's "Auto"),
                # confirmed via local Tuya protocol 3.5 packet capture.
                "auto": "auto",
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
                "pure": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "boost": "Boost",
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
        RobovacCommand.DO_NOT_DISTURB: {
            "code": 107,
        },
        RobovacCommand.CLEANING_TIME: {
            "code": 109,
        },
        RobovacCommand.CLEANING_AREA: {
            "code": 110,
        },
        RobovacCommand.BOOST_IQ: {
            "code": 118,
        },
    }
