"""Zero-dependency protobuf decoder for Eufy RoboVac T2277 DPS messages.

Wire format:
  Each DPS value is a base64 string. When decoded:
  - Byte 0: length prefix (stripped)
  - Bytes 1+: standard protobuf binary encoding

Protobuf binary format:
  - Each field: tag-byte(s) + value
  - Tag = (field_number << 3) | wire_type
    - wire_type 0: varint
    - wire_type 1: 64-bit (8 bytes)
    - wire_type 2: length-delimited (varint length + bytes)
    - wire_type 5: 32-bit (4 bytes)
  - Varint: little-endian base-128 (MSB=1 → more bytes)
  - Repeated fields: multiple field_number occurrences → list
"""

import base64
from typing import Any


# T2277 error/warning code mapping
T2277_ERROR_CODES = {
    # Mobility
    2101: "Front bumper stuck",
    2102: "Left wheel stuck",
    2103: "Right wheel stuck",
    2104: "Both wheels stuck",
    2105: "Wheel suspended",
    2106: "Wheel module error",
    # Brushes
    2201: "Main brush stuck",
    2202: "Main brush tangled",
    2211: "Side brush stuck",
    2212: "Side brush tangled",
    2213: "Side brush stuck",
    2214: "Main brush stuck",
    # Dust system
    2301: "Filter blocked",
    2302: "Dust box full",
    2303: "Dust box missing",
    2304: "Dust collector blocked",
    # Sensors
    2401: "Laser sensor stuck",
    2402: "Laser sensor blocked",
    2403: "Wall sensor error",
    2404: "Laser cover stuck",
    2405: "Path tracking sensor dirty",
    2406: "Ultrasonic sensor error",
    # Physical state
    2501: "Robot tilted",
    2502: "Cliff detected",
    2503: "Magnetic boundary detected",
    2504: "Restricted area detected",
    # Power
    2601: "Battery low",
    2602: "Battery error",
    2603: "Charging error",
    2604: "Charging abnormal",
    2605: "Return to charge failed",
    # Navigation / task
    7000: "Robot trapped",
    7001: "Return to dock failed",
    7002: "Inaccessible areas not cleaned",
    7003: "Navigation error",
    7004: "Relocalization failed",
    7005: "Map error",
    # System
    8101: "LIDAR error",
    8102: "Camera error",
    8103: "System error",
}


def _parse_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Parse a varint at position pos. Return (value, new_pos)."""
    value = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        value |= (byte & 0x7F) << shift
        pos += 1
        if (byte & 0x80) == 0:
            break
        shift += 7
    return value, pos


def _parse_proto(data: bytes) -> dict[int, Any]:
    """Parse protobuf binary data. Return dict of field_num -> value/bytes/list."""
    fields: dict[int, Any] = {}
    pos = 0

    while pos < len(data):
        # Parse tag
        tag, pos = _parse_varint(data, pos)
        field_num = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 0:  # varint
            value, pos = _parse_varint(data, pos)
            if field_num in fields:
                # Repeated field → convert to list or append
                if not isinstance(fields[field_num], list):
                    fields[field_num] = [fields[field_num]]
                fields[field_num].append(value)
            else:
                fields[field_num] = value

        elif wire_type == 2:  # length-delimited
            length, pos = _parse_varint(data, pos)
            value = data[pos : pos + length]
            pos += length
            fields[field_num] = value

        elif wire_type == 1:  # 64-bit
            pos += 8

        elif wire_type == 5:  # 32-bit
            pos += 4

    return fields


def _strip_length_prefix(raw_b64: str) -> bytes:
    """Decode base64 and strip the length prefix byte."""
    return base64.b64decode(raw_b64)[1:]


def decode_mode_ctrl(raw_b64: str) -> str:
    """Decode DPS 152 (ModeCtrlRequest) to a mode string."""
    METHOD_NAMES = {
        0: "auto",
        6: "stop",
        12: "standby",
        13: "pause",
        14: "nosweep",
    }

    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    # Extract fields
    method = fields.get(1)
    param = fields.get(3)

    # Logic: if method is 0 or absent but param (field_3) is present → auto
    if (method is None or method == 0) and param is not None:
        return "auto"

    # If both absent → standby
    if method is None and param is None:
        return "standby"

    # Otherwise use method
    if method is not None:
        return METHOD_NAMES.get(method, f"method_{method}")

    return "standby"


def decode_work_status(raw_b64: str) -> str:
    """Decode DPS 153 (WorkStatus) to a status string."""
    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    # Extract main fields
    mode_bytes = fields.get(1)
    state = fields.get(2)
    charging_bytes = fields.get(3)
    cleaning_bytes = fields.get(6)
    gohome_bytes = fields.get(8)
    relocating_bytes = fields.get(10)
    breakpoint_bytes = fields.get(11)

    # Parse sub-messages
    mode_fields = _parse_proto(mode_bytes) if mode_bytes else {}
    charging_fields = _parse_proto(charging_bytes) if charging_bytes else {}
    cleaning_fields = _parse_proto(cleaning_bytes) if cleaning_bytes else {}
    gohome_fields = _parse_proto(gohome_bytes) if gohome_bytes else {}
    relocating_fields = _parse_proto(relocating_bytes) if relocating_bytes else {}
    breakpoint_fields = _parse_proto(breakpoint_bytes) if breakpoint_bytes else {}

    mode = mode_fields.get(1, 0)
    charging_state = charging_fields.get(1)
    cleaning_run_state = cleaning_fields.get(1)
    cleaning_mode = cleaning_fields.get(2)
    gohome_run_state = gohome_fields.get(1)

    # State-based routing
    if state == 0:  # STANDBY
        return "Standby"

    if state == 1:  # SLEEP
        return "Sleeping"

    if state == 2:  # FAULT
        return "error"

    if state == 3:  # CHARGING
        if charging_state == 1:  # DONE
            return "completed"
        if breakpoint_fields:  # mid-clean charge
            return "recharging"
        return "Charging"

    if state == 4:  # FAST_MAPPING
        return "fast_mapping"

    if state == 5:  # CLEANING
        if relocating_fields:  # positioning
            if mode == 0:  # AUTO
                return "positioning"
            if mode == 1:  # SELECT_ROOM
                return "room_positioning"
            if mode == 2:  # SELECT_ZONE
                return "spot_positioning"
            return "positioning"

        if cleaning_run_state == 1:  # PAUSED
            if mode == 0:  # AUTO
                return "Paused"
            if mode == 1:  # SELECT_ROOM
                return "room_pause"
            if mode == 2:  # SELECT_ZONE
                return "spot_pause"
            return "Paused"

        # Active cleaning
        if mode == 0:  # AUTO
            return "auto"
        if mode == 1:  # SELECT_ROOM
            return "room"
        if mode == 2:  # SELECT_ZONE
            return "spot"
        if mode == 3:  # SPOT
            return "spot"
        return "auto"

    if state == 6:  # REMOTE_CTRL
        return "start_manual"

    if state == 7:  # GO_HOME
        if breakpoint_fields:  # mid-clean, will resume
            return "going_to_recharge"
        return "going_to_charge"

    if state == 8:  # CRUISING
        return "cruising"

    return f"state_{state}"


def decode_error_code(raw_b64: str) -> str:
    """Decode DPS 177 (ErrorCode) to a comma-separated error string."""
    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    codes_set: set[int] = set()

    # Collect from field_3 (repeated warn)
    if 3 in fields:
        warn_field = fields[3]
        if isinstance(warn_field, list):
            codes_set.update(warn_field)
        else:
            codes_set.add(warn_field)

    # Collect from field_10 (new_code message)
    new_code_bytes = fields.get(10)
    if new_code_bytes:
        new_code_fields = _parse_proto(new_code_bytes)

        # field_1: repeated error
        if 1 in new_code_fields:
            error_field = new_code_fields[1]
            if isinstance(error_field, list):
                codes_set.update(error_field)
            else:
                codes_set.add(error_field)

        # field_2: repeated warn
        if 2 in new_code_fields:
            warn_field = new_code_fields[2]
            if isinstance(warn_field, list):
                codes_set.update(warn_field)
            else:
                codes_set.add(warn_field)

    if not codes_set:
        return "no_error"

    # Sort and map
    sorted_codes = sorted(codes_set)
    mapped = [T2277_ERROR_CODES.get(code, f"error_{code}") for code in sorted_codes]
    return ", ".join(mapped)
