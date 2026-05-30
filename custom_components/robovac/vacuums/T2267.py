"""RoboVac L60 (T2267)"""
import base64
from homeassistant.components.vacuum import VacuumActivity, VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2267(RobovacModelDetails):
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
    )
    activity_mapping = {
        "BgoAEAUyAA==":     VacuumActivity.CLEANING,
        "BgoAEAVSAA==":     VacuumActivity.CLEANING,
        "CAoAEAUyAggB":     VacuumActivity.CLEANING,
        "CAoCCAEQBTIA":     VacuumActivity.CLEANING,
        "CAoCCAEQBVIA":     VacuumActivity.CLEANING,
        "CgoCCAEQBTICCAE=": VacuumActivity.CLEANING,
        "CAoCCAIQBTIA":     VacuumActivity.CLEANING,
        "CAoCCAIQBVIA":     VacuumActivity.CLEANING,
        "CgoCCAIQBTICCAE=": VacuumActivity.CLEANING,
        "BAoAEAY=":         VacuumActivity.RETURNING,
        "BBAHQgA=":         VacuumActivity.RETURNING,
        "BBADGgA=":         VacuumActivity.DOCKED,
        "BhADGgIIAQ==":     VacuumActivity.DOCKED,
        "AA==":             VacuumActivity.IDLE,
        "AhAB":             VacuumActivity.IDLE,
    }


    @staticmethod
    def decode_dps(dps_code: int, value: str) -> str | None:
        """Decode binary protobuf DPS values for the L60 (T2267).
        DPS 177 (error): last byte is the error code. 0x00 = no error.
        All other DPS codes fall through to standard handling.
        """
        if dps_code == 177:
            try:
                data = base64.b64decode(value)
                if len(data) > 0 and data[-1] == 0:
                    return "no_error"
                return str(data[-1]) if len(data) > 0 else "no_error"
            except Exception:
                return "no_error"
        return None

    commands = {
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                "auto": "BBoCCAE=",
                "pause": "AggN",
                "Spot": "AA==",
                "return": "AggG",
                "Nosweep": "AggO",
            },
        },
        RobovacCommand.STATUS: {
            "code": 153,
            "values": [
                "BgoAEAUyAA==",
                "BgoAEAVSAA==",
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
            "values": {
                "brake": "brake",
                "forward": "forward",
                "back": "back",
                "left": "left",
                "right": "right",
            },
        },
        RobovacCommand.START_PAUSE: {
            "code": 156,
        },
        RobovacCommand.DO_NOT_DISTURB: {
            "code": 157,
        },
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "boost_iq": "Boost_IQ",
            },
        },
        RobovacCommand.BOOST_IQ: {
            "code": 159,
        },
        RobovacCommand.LOCATE: {
            "code": 160,
        },
        RobovacCommand.BATTERY: {
            "code": 163,
        },
        RobovacCommand.CONSUMABLES: {
            "code": 168,
        },
        RobovacCommand.RETURN_HOME: {
            "code": 173,
        },
        RobovacCommand.ERROR: {
            "code": 177,
        },
    }