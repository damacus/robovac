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
    _ERROR_CODES = {
        1: "Wheel stuck",
        2: "Brush stuck",
        3: "Side brush stuck",
        4: "Dust box missing",
        5: "Lidar cover blocked",
        6: "Stuck on obstacle",
        7: "Drop sensor dirty",
        8: "Mop pad stuck",
        9: "Waterbox missing",
        11: "Clean station error",
        12: "Clean station water shortage",
        13: "Clean station wastewater full",
        14: "Clean station wash tray",
        49: "No path available",
        50: "Map generation failed",
        51: "Cannot reach target",
        73: "Dirty water tank full",
        74: "Clean water tank empty",
        82: "Clean station wash tray",
        83: "Waste water tank full",
    }
    _PROMPT_CODES = {
        7: "Route unavailable, returning to dock",
        10: "Prompt 10",
        12: "Prompt 12",
        17: "Prompt 17",
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
