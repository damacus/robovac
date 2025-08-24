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

    # DPS mapping corrected to match on-device telemetry
    commands = {
        # Cleaning mode blob seen on DPS 152 in logs (leave as-is for this model)
        RobovacCommand.MODE: {
            "code": 152,
            "values": ["AggN", "AA==", "AggG", "BBoCCAE=", "AggO"],
        },

        # High-level running/cleaning state bit is on DPS 156
        RobovacCommand.STATUS: {
            "code": 156,
        },

        # Start/Pause actions happen on DPS 153 on this model
        RobovacCommand.START_PAUSE: {
            "code": 153,
        },

        # Return-to-dock uses DPS 153 on this model
        RobovacCommand.RETURN_HOME: {
            "code": 153,
        },

        # Fan speed is DPS 158 and reports strings like "Quiet/Standard/Turbo/Max"
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": ["Quiet", "Standard", "Turbo", "Max"],
        },

        # Locate/beep also rides on DPS 153 for this model
        RobovacCommand.LOCATE: {
            "code": 153,
            "values": ["AggC"],
        },

        # Battery percentage comes from DPS 161
        RobovacCommand.BATTERY: {
            "code": 161,
        },

        # Error/info blob
        RobovacCommand.ERROR: {
            "code": 169,
        },
    }
