from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2276(RobovacModelDetails):
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
    commands = {
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                "SmallRoom": "AggN",  # Small room mode
                "Spot": "AA==",     # Spot clean mode
                "Edge": "AggG",     # Edge clean mode
                "auto": "BBoCCAE=",  # Auto clean mode
                "Nosweep": "AggO",  # No sweep mode
            },
        },
        RobovacCommand.STATUS: {
            "code": 173,
        },
        RobovacCommand.RETURN_HOME: {
            "code": 153,
            "values": {
                "return_home": "AggB",  # Return home command
            }
        },
        RobovacCommand.FAN_SPEED: {
            "code": 154,
            "values": {
                "fan_speed": "AgkBCgIKAQoDCgEKBAoB",  # Fan speed values
            }
        },
        RobovacCommand.LOCATE: {
            "code": 153,
            "values": {
                "locate": "AggC",  # Locate command
            }
        },
        RobovacCommand.BATTERY: {
            "code": 172,
        },
        RobovacCommand.ERROR: {
            "code": 169,
        },
    }
