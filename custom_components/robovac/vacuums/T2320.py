"""Eufy Robot Vacuum and Mop X9 Pro with Auto-Clean Station (T2320)"""

from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2320(RobovacModelDetails):
    # This model exposes the full set of basic controls: start, pause, return home, stop, locate,
    # fan speed and battery state.  In Home Assistant the "stop" (square) action is mapped to
    # return-to-base, the "pause" (two bars) action pauses cleaning in place, and the "play"
    # (triangle) action starts an auto clean.
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

    # Additional vacuum-specific features (Do Not Disturb, Boost IQ)
    robovac_features = (
        RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.BOOST_IQ
    )

    # DPS mapping aligned with the X9 Pro’s on-device protocol.
    # DP 152 carries a small binary token that tells the robot what to do:
    #   - "AggG": start auto clean (play/triangle)
    #   - "AA==": pause and stop in place (pause/two bars)
    #   - "AggN": return to dock (stop/square)
    #   - "AggO": perform a spot clean
    #   - other tokens ("AggB", "BBoCCAE=") are retained for completeness but unused here.
    commands = {
        RobovacCommand.MODE: {
            "code": 152,
            "values": [
                "AggG",      # auto clean
                "AA==",      # pause
                "AggN",      # return home
                "AggO",      # spot clean
                "AggB",      # reserved/unused
                "BBoCCAE=",  # reserved/unused
            ],
        },

        # High-level running/cleaning state bit (True/False) on DP 156.
        RobovacCommand.STATUS: {"code": 156},

        # Start/Pause and Return-to-dock both use DP 152 on this model.
        # We provide these mappings so that any fallback logic in the integration doesn’t
        # mistakenly try to use DP 153.
        RobovacCommand.START_PAUSE: {"code": 152},
        RobovacCommand.RETURN_HOME: {"code": 152},

        # Fan speed is DP 158 with string values.
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": ["Quiet", "Standard", "Turbo", "Max"],
        },

        # Locate/beep uses DP 153 with a base64 token.
        RobovacCommand.LOCATE: {"code": 153},

        # Battery percentage on DP 161.
        RobovacCommand.BATTERY: {"code": 161},

        # NOTE: We intentionally do NOT map RobovacCommand.ERROR for T2320.
        # DP 169 is a device-info blob, not an error; mapping it to ERROR caused false "error"
        # states.  If a real error DP is identified later for this model, add it here.
    }
