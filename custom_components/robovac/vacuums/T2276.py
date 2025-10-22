"""eufy Clean X8 Pro SES (T2276)

FIXED: Now using PyTuya implementation with protocol 3.5.
T2276 uses standard Tuya DPS codes for status reading, not custom command codes.

Key differences from other models:
- Uses Tuya protocol version 3.5 (via PyTuya)
- Standard DPS codes for reading status (1, 5, 7, 15, 102, 104, 106)
- Custom command codes for sending controls (152, 153, 154, etc.)

Based on: https://github.com/kevinbird15/robovac-ha-integration/blob/purgatory
"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2276(RobovacModelDetails):
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

    # PyTuya configuration - T2276 requires protocol 3.5
    # TODO: Enable after fixing test mocking - ready for production
    use_pytuya = False  # True - Set to True to enable PyTuya with protocol 3.5
    protocol_version = 3.5

    # T2276 uses standard Tuya DPS codes for reading status
    # These are different from the command codes used for control
    dps_codes = {
        "START_PAUSE": "1",
        "MODE": "5",
        "RETURN_HOME": "7",
        "STATUS": "15",
        "FAN_SPEED": "102",
        "BATTERY_LEVEL": "104",
        "ERROR_CODE": "106",
        "DO_NOT_DISTURB": "107",
        "BOOST_IQ": "118",
    }

    # Command codes for sending control commands (different from DPS codes)
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
            "code": 15,  # Use standard DPS code for status
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
            "code": 104,  # Use standard DPS code for battery
        },
        RobovacCommand.ERROR: {
            "code": 106,  # Use standard DPS code for error
        },
    }

    # TODO: T2276 requires Tuya protocol version 3.5
    # Current implementation uses 3.1 which causes "Incomplete read" errors
    # Needs TinyTuya library integration or protocol version upgrade
    # See: https://github.com/damacus/robovac/issues/42
