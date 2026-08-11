"""RoboVac G20 Hybrid (T2258)."""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2258(RobovacModelDetails):
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
        | RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.AUTO_RETURN
        | RoboVacEntityFeature.CONSUMABLES
    )
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 2,
            "values": {"start": True, "pause": False},
        },
        RobovacCommand.MODE: {
            "code": 5,
            "values": {
                "auto": "Auto",
                "spot": "Spot",
            },
        },
        # DPS 15 is not a usable status register on this model: it reports
        # "Running" while cleaning, paused, stopped and docked alike, so the
        # entity never leaves CLEANING. DPS 2 is the datapoint that tracks
        # whether the vacuum is actually active.
        #
        # The values map is required rather than cosmetic. DPS 2 is a boolean,
        # and a raw False is indistinguishable from "no status" to the
        # `state == 0` check in RoboVacEntity.activity, which then falls back to
        # the cleaning mode. Decoding to a string avoids that.
        RobovacCommand.STATUS: {
            "code": 2,
            "values": {"True": "cleaning", "False": "docked"},
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
                "boost_iq": "Boost_IQ",
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
