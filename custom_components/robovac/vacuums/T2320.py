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

    # DPS mapping aligned with on-device telemetry
    commands = {
        # Cleaning mode / command blob on DPS 152 (leave list as-is for this model)
        RobovacCommand.MODE: {
            "code": 152,
            "values": ["AggN", "AA==", "AggG", "BBoCCAE=", "AggO"],
        },

        # High-level running/cleaning state bit on DPS 156
        RobovacCommand.STATUS: {"code": 156},

        # Start/Pause and Return-to-dock happen via DPS 153 on this model
        RobovacCommand.START_PAUSE: {"code": 153},
        RobovacCommand.RETURN_HOME: {"code": 153},

        # Fan speed is DPS 158 with string values
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": ["Quiet", "Standard", "Turbo", "Max"],
        },

        # Locate/beep via DPS 153 (payload provided by base command table)
        RobovacCommand.LOCATE: {"code": 153},

        # Battery percentage on DPS 161
        RobovacCommand.BATTERY: {"code": 161},

        # NOTE: We intentionally do NOT map RobovacCommand.ERROR for T2320.
        # DPS 169 is a device-info blob, not an error; mapping it to ERROR caused false "error" states.
        # If a real error DP is identified later for this model, add it here.
    }
