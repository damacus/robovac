"""eufy Clean X8 Pro (T2266)

Same core hardware and protocol as the X8 Pro SES (T2276) — eufy's own user
guide covers both under "eufy Clean X8 Pro Series (For T2266 & T2276)", and the
eufy cloud reports this unit as "T2266 eufy Clean X8 Pro Hybrid". A live cloud
DPS snapshot confirmed the T2266 exposes the same standard Tuya datapoints as
the T2276 (DPS 5 lowercase "auto", 15 status, 101/103 boolean triggers, 102 fan
speed, 104 battery, 106 error, 109/110 clean time/area, 118 BoostIQ), so the
T2276 command map applies unchanged. Both report on protocol 3.5 with
human-readable DPS values.

Note: contrary to the initial assumption that the T2266 was a bare charging-base
model, the snapshot shows it does have a station with dust collection (DPS 126,
base64 JSON). Neither this config nor the T2276 config maps DPS 126, though —
station / dust-collect control is not exposed as a Home Assistant command.

Unlike the T2276, this config does not opt into the protocol 3.5 network
behaviors (protocol_35_empty_dps_query, protocol_35_map_data_keepalive). Those
were validated for the T2276 with local packet captures; a cloud DPS snapshot
cannot show whether the T2266 needs an empty-DPS status query or a DPS 121
map-data keepalive on ping. Enable them only with a T2266 packet capture
proving the behavior.
"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2266(RobovacModelDetails):
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
                # X8 Pro series uses lowercase "auto" (unlike T2128's "Auto"):
                # confirmed by T2276 packet capture and the T2266 cloud DPS
                # snapshot, which reports the same lowercase value.
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
            "values": {"return": True},
        },
        RobovacCommand.FAN_SPEED: {
            "code": 102,
            "values": {
                "pure": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "boost": "Boost",
            },
        },
        RobovacCommand.LOCATE: {
            "code": 103,
            "values": {"locate": True},
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
