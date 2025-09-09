"""Eufy Robot Vacuum and Mop X9 Pro with Auto-Clean Station (T2320)"""
from homeassistant.components.vacuum import VacuumEntityFeature, VacuumActivity
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
    # Align DP codes/values with field logs (similar to T2267/L60 layout)
    commands = {
        # Pause is applied via MODE DP (152) on this model
        RobovacCommand.START_PAUSE: {
            "code": 152,
            "values": {
                "pause": "AggN",
            },
        },
        # Mode selection is DP 152 using Tuya base64 tokens
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                # Bidirectional mapping: human -> token and token -> human
                # human -> token (for sending commands)
                "auto": "BBoCCAE=",
                "pause": "AggN",
                "spot": "AA==",
                "return": "AggG",
                "nosweep": "AggO",
                # token -> human (for decoding DPS -> readable mode)
                "BBoCCAE=": "auto",
                "AggN": "pause",
                "AA==": "spot",
                "AggG": "return",
                "AggO": "nosweep",
            },
        },
        # Status reports via DP 153 (base64-encoded status payloads)
        RobovacCommand.STATUS: {
            "code": 153,
            "values": {
                # Observed when the vacuum is idle at the dock. Without this
                # mapping Home Assistant would treat the state as cleaning.
                # Mapping it to "standby" ensures the entity reports an idle
                # activity instead.
                "EhAFGgIIAToCEAJyBhoCCAEiAA==": "standby",
                # Observed when the vacuum is fully charged and docked
                "ChADGgIIAXICIgA=": "Fully Charged",
                # Observed when the vacuum automatically returns to the dock to charge
                "EAoAEAMaADICCAFaAHICIgA=": "Auto-return charging",
                # Observed when the mop is drying at the dock
                "EBAFGgA6AhACcgYaAggBIgA=": "Drying Mop",
                # Observed when the vacuum is auto-cleaning off the dock
                "CgoAEAUyAHICIgA=": "Auto Cleaning",
                "DgoAEAUaAggBMgByAiIA": "Auto Cleaning",
            },
        },
        # Return home is triggered via MODE DP (152) on this model
        RobovacCommand.RETURN_HOME: {
            "code": 152,
            "values": {
                "return": "AggG",
            },
        },
        # Fan speed is DP 158 with human-readable values
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        },
        # Locate/beep is DP 160
        RobovacCommand.LOCATE: {
            "code": 160,
        },
        # Battery level is DP 163
        RobovacCommand.BATTERY: {
            "code": 163,
        },
        # Bind a dummy error DP to satisfy plumbing and avoid
        # misclassifying informational payloads as errors.
        # When a reliable error DP is known for this model, update it.
        RobovacCommand.ERROR: {
            "code": 0,
        },
    }

    activity_mapping = {
        "Auto-return charging": VacuumActivity.DOCKED,
        "Drying Mop": VacuumActivity.DOCKED,
        "Fully Charged": VacuumActivity.DOCKED,
        "Auto Cleaning": VacuumActivity.CLEANING,
        "standby": VacuumActivity.IDLE,
    }
