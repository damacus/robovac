"""RoboVac G20 (T2257).
Added 2026-09-10: the plain (non-Hybrid) G20 (Tuya model code T2257) was missing
from damacus/robovac — only the G20 Hybrid (T2258) was supported, so the device
reported "model is not supported". Command codes confirmed live against a T2257
("Dobby") via a direct Tuya status query (tinytuya): start/pause 2, direction 3,
mode 5, status 15, fan 102, locate 103, battery 104, error 106, cleaning area 109,
cleaning time 110. Observed payload while docked/idle:
{'2': False, '3': 'forward', '5': 'Nosweep', '15': 'completed', '102': 'Max',
'103': False, '104': 100, '106': 0, '109': 2395, '110': 32}
Fan speed and mode value sets follow the wider G-series convention (see T2256/
T2258) but have only been confirmed for 'Max' and 'Nosweep' respectively; other
values are unverified and should be tested against the live device before relying
on them.
"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2257(RobovacModelDetails):
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
    robovac_features = (
        RoboVacEntityFeature.CLEANING_TIME
        | RoboVacEntityFeature.CLEANING_AREA
        | RoboVacEntityFeature.AUTO_RETURN
    )
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 2,
            "values": {"start": True, "pause": False},
        },
        RobovacCommand.DIRECTION: {
            "code": 3,
            "values": {
                "forward": "forward",
                "back": "back",
                "left": "left",
                "right": "right",
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
        RobovacCommand.CLEANING_AREA: {
            "code": 109,
        },
        RobovacCommand.CLEANING_TIME: {
            "code": 110,
        },
    }
