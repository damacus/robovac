"""Eufy Robot Vacuum and Mop X9 Pro with Auto-Clean Station (T2320).

Model-specific DPS codes, activity mapping for station states, and decode_dps
for base64/protobuf payloads on this hardware variant.
"""
import base64
from typing import Any

from homeassistant.components.vacuum import VacuumActivity, VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2320(RobovacModelDetails):
    # X9 Pro firmware maps unsupported "sweep_then_mop" to "sweep_and_mop"; expose only real modes.
    expose_config_entities = True
    clean_type_select_keys = ("sweep_only", "mop_only", "sweep_and_mop")
    default_clean_param_dps154 = "JgoOCgIIAhIAGgAiAggCKgASABoAIhAKAggCGgAiAggCKgAyAggB"
    warning_dps_code = 177
    expose_room_select = True
    consumable_sensor_keys = (
        "side_brush",
        "rolling_brush",
        "filter_mesh",
        "scrape",
        "sensor",
        "mop",
    )

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

    # ── Activity mapping for HA vacuum state ──────────────────────────
    activity_mapping = {
        "standby": VacuumActivity.IDLE,
        "idle": VacuumActivity.IDLE,
        "auto": VacuumActivity.CLEANING,
        "cleaning": VacuumActivity.CLEANING,
        "pause": VacuumActivity.PAUSED,
        "paused": VacuumActivity.PAUSED,
        "return": VacuumActivity.RETURNING,
        "returning": VacuumActivity.RETURNING,
        "docking": VacuumActivity.RETURNING,
        "charging": VacuumActivity.DOCKED,
        "docked": VacuumActivity.DOCKED,
        "washing": VacuumActivity.DOCKED,
        "drying": VacuumActivity.DOCKED,
        "removing scale": VacuumActivity.DOCKED,
        "error": VacuumActivity.ERROR,
    }

    # ── Command definitions ───────────────────────────────────────────
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 2,
            "values": {
                "start": True,
                "pause": False,
            },
        },
        RobovacCommand.MODE: {
            "code": 152,
            "values": {
                "auto": "BBoCCAE=",
                "return": "AggG",
                "pause": "AggN",
                "standby": "AA==",
                "stop": "AggM",
                "resume": "AggO",
                "small_room": "small_room",
                "single_room": "single_room",
            },
        },
        RobovacCommand.STATUS: {
            "code": 173,
        },
        RobovacCommand.RETURN_HOME: {
            "code": 153,
            "values": {
                "return_home": True,
                "return": True,
            },
        },
        # DPS 154 — CleanParamResponse (sweep/mop type, mop level, etc.). Separate from
        # FAN_SPEED on 158; enables RobovacCleanTypeSensor on the sensor platform.
        RobovacCommand.CLEAN_PARAM: {
            "code": 154,
        },
        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": {
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "quiet": "Quiet",
            },
        },
        RobovacCommand.LOCATE: {
            "code": 160,
            "values": {
                "locate": True,
            },
        },
        RobovacCommand.BATTERY: {
            "code": 163,
        },
        RobovacCommand.CONSUMABLES: {
            "code": 168,
        },
        RobovacCommand.ERROR: {
            "code": 177,
        },
        RobovacCommand.ACTIVE_ERRORS: {
            "code": 178,
        },
    }
    dps_codes = {
        "ROOM_META": "165",
    }

    # ── DPS 152 base64 mode detection ─────────────────────────────────
    _MODE_BASE64 = {
        "AA==": "standby",
        "AggN": "pause",
        "AggM": "stop",
        "AggG": "return",
        "BBoCCAE=": "auto",
        "AggO": "auto",  # resume
    }

    # ── DPS 173 station status detection ──────────────────────────────
    _STATION_KEYWORDS = {
        "WASHING": "washing",
        "DRYING": "drying",
        "REMOVING_SCALE": "removing scale",
    }
    _STATION_CODES = {
        45: "washing",
        76: "drying",
    }

    # ── DPS 177 error/warning codes ───────────────────────────────────
    # T2320 ErrorCodeList/PromptCodeList labels adapted from
    # `error_code_list_t2320.proto` in martijnpoppen/eufy-clean,
    # copyright (c) Martijn Poppen:
    # https://github.com/martijnpoppen/eufy-clean
    #
    # The same file was reviewed through the jeppesens/eufy-clean fork
    # history and the GijsKruize/eufy-clean renamed path:
    # custom_components/robovac_mqtt/proto/cloud/error_code_list_t2320.proto
    #
    # Eufy-Clean License, Version 1.0 - 2024-09-01, permits use, copy,
    # modification, merge, publication, distribution, sublicensing, and sale
    # with attribution. These enum names/comments were translated into
    # robovac's human-readable message style.
    _ERROR_CODES = {
        1: "Crash buffer stuck",
        2: "Wheel stuck",
        3: "Side brush stuck",
        4: "Rolling brush stuck",
        5: "Robot trapped, clear surrounding obstacles",
        6: "Robot trapped, move it near the starting point",
        7: "Wheel overhanging",
        8: "Power too low, shutting down",
        13: "Robot tilted",
        14: "Dust box or filter missing",
        17: "Forbidden area detected",
        18: "Laser cover stuck",
        19: "Laser sensor stuck or tangled",
        20: "Laser sensor may be blocked",
        21: "Docking failed",
        26: "Low battery, scheduled cleaning failed",
        31: "Foreign object stuck in suction port",
        32: "Mop holder rotation motor stuck",
        33: "Mop holder lift motor stuck",
        39: "Positioning failed, ending cleaning",
        40: "Mop cloth dislodged",
        41: "Air-drying heater abnormal",
        50: "Robot mistakenly on carpet",
        51: "Camera blocked",
        52: "Unable to leave station",
        55: "Base station exploration failed",
        70: "Clean dust box and filter",
        71: "Wall sensor abnormal",
        72: "Robot water tank low",
        73: "Dirty water tank full",
        74: "Clean water tank low",
        75: "Water tank missing",
        76: "Camera abnormal",
        77: "3D ToF sensor abnormal",
        78: "Ultrasonic sensor abnormal",
        79: "Clean tray not installed",
        80: "Robot and station communication abnormal",
        81: "Sewage tank air leak",
        82: "Clean tray needs cleaning",
        83: "Poor charging contact",
        101: "Battery abnormal",
        102: "Wheel module abnormal",
        103: "Side brush module abnormal",
        104: "Fan abnormal",
        105: "Rolling brush motor abnormal",
        106: "Robot water pump abnormal",
        107: "Laser sensor abnormal",
        111: "Rotation motor abnormal",
        112: "Lift motor abnormal",
        113: "Water spraying device abnormal",
        114: "Water pumping device abnormal",
        117: "Ultrasonic sensor abnormal",
        119: "Wi-Fi or Bluetooth abnormal",
    }
    _PROMPT_CODES = {
        1: "Start scheduled cleaning",
        3: "Low battery, returning to base station immediately",
        4: "Positioning failed, rebuilding map and starting new cleaning",
        5: "Positioning failed, mission ended, returning to base station",
        6: "Some areas were not cleaned because they are unreachable",
        7: "Path planning failed, cannot reach the designated area",
        9: "Base station exploration failed, robot returned to starting point",
        10: "Positioning successful",
        11: "Task finished, returning to base station",
        12: "Cannot start task while on station",
        13: "Scheduled cleaning failed because robot is working",
        14: "Map data updating, try again later",
        15: "Finished washing mop, resuming task",
        16: "Low battery, charge and try again",
        17: "Mop cleaning completed",
    }

    @classmethod
    def decode_warning_dps(cls, raw_value: str) -> list[dict[str, int | str]]:
        """Decode DPS 177 warning fields into warning code/message pairs."""
        if not raw_value:
            return []
        try:
            from custom_components.robovac.proto_decode import (
                _decode_packed_varints,
                _parse_proto,
                _strip_length_prefix,
            )

            fields = _parse_proto(_strip_length_prefix(raw_value))
            codes: set[int] = set()

            def collect(field_value: Any) -> None:
                if field_value is None:
                    return
                if isinstance(field_value, list):
                    for item in field_value:
                        collect(item)
                elif isinstance(field_value, int):
                    codes.add(field_value)
                elif isinstance(field_value, bytes):
                    codes.update(_decode_packed_varints(field_value))

            collect(fields.get(3))

            new_code = fields.get(10)
            if isinstance(new_code, bytes):
                new_code_fields = _parse_proto(new_code)
                collect(new_code_fields.get(2))

            codes.discard(0)
            return [
                {
                    "code": warning_code,
                    "message": cls._ERROR_CODES.get(
                        warning_code, f"warning_{warning_code}"
                    ),
                }
                for warning_code in sorted(codes)
            ]
        except Exception:
            return []

    # ── Custom DPS decoder ────────────────────────────────────────────
    @classmethod
    def decode_dps(cls, dps_code: str, raw_value: str) -> str | None:
        """Decode base64/protobuf DPS payloads into human-readable strings."""
        if not raw_value:
            return None

        code = str(dps_code)

        # DPS 152 — mode/activity (base64 encoded)
        if code == "152":
            decoded = cls._MODE_BASE64.get(raw_value)
            if decoded:
                return decoded
            try:
                base64.b64decode(raw_value, validate=True)
                return f"mode:{raw_value}"
            except Exception:
                return raw_value

        # DPS 153 — return/dock progress. X9 leaves DPS 152 as "return" after it
        # reaches the dock, so this payload is needed to distinguish returning
        # from already docked.
        if code == "153":
            try:
                from custom_components.robovac.proto_decode import (
                    _as_varint,
                    _parse_proto,
                    _strip_length_prefix,
                )

                fields = _parse_proto(_strip_length_prefix(raw_value))
                dock_state = fields.get(7)
                if isinstance(dock_state, bytes):
                    dock_fields = _parse_proto(dock_state)
                    progress = _as_varint(dock_fields.get(2))
                    if progress == 1:
                        if isinstance(fields.get(6), bytes) or isinstance(
                            fields.get(14), bytes
                        ):
                            return "docked"
                        return "returning"
                    if progress == 2:
                        return "docked"
                state = _as_varint(fields.get(2))
                if state == 7:
                    return "returning"
                if state == 3:
                    return "docked"
                if state == 5:
                    return "cleaning"
                active_state = fields.get(6)
                if isinstance(active_state, bytes) and not active_state:
                    return "cleaning"
            except Exception:
                pass
            return None

        # DPS 173 — station status
        if code == "173":
            raw_bytes = b""
            try:
                from custom_components.robovac.proto_decode import (
                    _parse_proto,
                    _strip_length_prefix,
                )

                raw_bytes = base64.b64decode(raw_value, validate=True)
                upper = raw_bytes.decode("utf-8", errors="ignore").upper()
                for keyword, label in cls._STATION_KEYWORDS.items():
                    if keyword in upper:
                        return label

                fields = _parse_proto(_strip_length_prefix(raw_value))
                station_bytes = fields.get(5)
                if isinstance(station_bytes, bytes):
                    station_fields = _parse_proto(station_bytes)
                    station_code = station_fields.get(1)
                    station_label = (
                        cls._STATION_CODES.get(station_code)
                        if isinstance(station_code, int)
                        else None
                    )
                    if station_label:
                        return station_label
            except Exception:
                upper = raw_bytes.decode("utf-8", errors="ignore").upper()
                for keyword, label in cls._STATION_KEYWORDS.items():
                    if keyword in upper:
                        return label
            return "idle"

        # DPS 177 — error/warning protobuf
        if code == "177":
            try:
                from custom_components.robovac.proto_decode import (
                    _decode_packed_varints,
                    _parse_proto,
                    _strip_length_prefix,
                )

                fields = _parse_proto(_strip_length_prefix(raw_value))
                codes: set[int] = set()

                def collect(field_value: Any) -> None:
                    if field_value is None:
                        return
                    if isinstance(field_value, list):
                        for item in field_value:
                            collect(item)
                    elif isinstance(field_value, int):
                        codes.add(field_value)
                    elif isinstance(field_value, bytes):
                        codes.update(_decode_packed_varints(field_value))

                # Only field 2 is an active error list. Field 3 carries warnings,
                # and on the X9 mop-wash station notifications are warning-only.
                collect(fields.get(2))

                new_code = fields.get(10)
                if isinstance(new_code, bytes):
                    new_code_fields = _parse_proto(new_code)
                    collect(new_code_fields.get(1))

                codes.discard(0)
                if not codes:
                    return "no_error"

                return "; ".join(
                    cls._ERROR_CODES.get(error_code, f"error_{error_code}")
                    for error_code in sorted(codes)
                )
            except Exception:
                pass
            return raw_value

        # DPS 178 — prompt/notification protobuf
        if code == "178":
            try:
                from custom_components.robovac.proto_decode import (
                    _decode_packed_varints as _decode_prompt_packed_varints,
                    _parse_proto,
                    _strip_length_prefix,
                )

                fields = _parse_proto(_strip_length_prefix(raw_value))
                prompt_codes: set[int] = set()

                def collect_prompt(field_value: Any) -> None:
                    if field_value is None:
                        return
                    if isinstance(field_value, list):
                        for item in field_value:
                            collect_prompt(item)
                    elif isinstance(field_value, int):
                        prompt_codes.add(field_value)
                    elif isinstance(field_value, bytes):
                        prompt_codes.update(_decode_prompt_packed_varints(field_value))

                collect_prompt(fields.get(2))

                prompt_codes.discard(0)
                if not prompt_codes:
                    return "no_error"

                return "; ".join(
                    cls._PROMPT_CODES.get(prompt_code, f"prompt_{prompt_code}")
                    for prompt_code in sorted(prompt_codes)
                )
            except Exception:
                pass
            return raw_value

        return None
