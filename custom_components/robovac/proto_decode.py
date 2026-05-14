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


# T2277 error/warning codes (DPS 177 field_3 warn / field_10 new_code)
# Empirically observed on T2277 hardware; codes are in the 2100–8100 range.
T2277_ERROR_CODES = {
    # Mobility
    4111: "Front bumper stuck (left)",
    4112: "Front bumper stuck (right)",
    1013: "Left wheel stuck",
    1023: "Right wheel stuck",
    1033: "Both wheels stuck",
    # Brushes
    2112: "Main brush stuck",
    2213: "Side brush stuck",
    # Dust system
    2310: "Dust box missing",
    # Sensors
    4012: "Laser sensor stuck",
    4011: "Laser sensor blocked",
    4130: "Laser cover stuck",
    # Power
    5014: "Battery low",
    2602: "Battery error",
    2603: "Charging error",
    2604: "Charging abnormal",
    2605: "Return to charge failed",
    # Navigation / task
    7000: "Robot trapped",
    7001: "Robot partly suspended",
    7002: "Robot suspended",
    7010: "Robot entered no go zone",
    7031: "Return to dock failed",
    7050: "Inaccessible areas not cleaned",
}

# T2277 prompt/notification codes (DPS 178 field_2 packed uint32)
# Source: PromptCodeList enum in error_code_list_t2265.proto
# These are informational notifications, not hardware faults.
T2277_PROMPT_CODES = {
    31: "Positioning successful",
    40: "Task finished, returning to dock",
    76: "Cannot start task while at charging dock",
    78: "Low battery, please charge before cleaning",
    79: "Low battery, returning to dock",
    85: "Starting scheduled cleaning",
    87: "Map updating, please try again later",
    6300: "Cutting hair / debris",
    6301: "Low battery, cannot cut hair",
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
            raw_value: bytes = data[pos: pos + length]
            pos += length
            if field_num in fields:
                # Repeated length-delimited field → accumulate as list
                if not isinstance(fields[field_num], list):
                    fields[field_num] = [fields[field_num]]
                fields[field_num].append(raw_value)
            else:
                fields[field_num] = raw_value

        elif wire_type == 1:  # 64-bit
            pos += 8

        elif wire_type == 5:  # 32-bit
            pos += 4

    return fields


def _encode_varint(v: int) -> bytes:
    """Encode a non-negative integer as protobuf varint bytes."""
    if v < 0:
        raise ValueError("varint must be non-negative")
    buf = bytearray()
    while True:
        piece = v & 0x7F
        v >>= 7
        if v:
            buf.append(piece | 0x80)
        else:
            buf.append(piece)
            break
    return bytes(buf)


def _serialize_proto(fields: dict[int, Any]) -> bytes:
    """Serialize a protobuf message from field_num -> int | bytes | dict (nested submessage).

    Wire types: int → varint (type 0), bytes/dict → length-delimited (type 2).
    Dict values are serialized as nested sub-messages.
    """
    chunks: list[bytes] = []
    for field_num in sorted(fields.keys()):
        val = fields[field_num]
        tag = field_num << 3
        if isinstance(val, int):
            chunks.append(_encode_varint(tag))
            chunks.append(_encode_varint(val))
        elif isinstance(val, bytes):
            chunks.append(_encode_varint(tag | 2))
            chunks.append(_encode_varint(len(val)))
            chunks.append(val)
        elif isinstance(val, dict):
            nested = _serialize_proto(val)
            chunks.append(_encode_varint(tag | 2))
            chunks.append(_encode_varint(len(nested)))
            chunks.append(nested)
        else:
            raise TypeError(f"Unsupported protobuf field value type: {type(val)!r}")
    return b"".join(chunks)


def _clean_param_b64_with_length_prefix(proto_payload: bytes) -> str:
    """Wrap payload with single-byte length prefix and return base64 (DPS 154 on-wire)."""
    return base64.b64encode(bytes([len(proto_payload)]) + proto_payload).decode("ascii")


def patch_clean_param_dps154(
    raw_b64: str,
    *,
    clean_type: str | None = None,
    mop_level: str | None = None,
    edge_hugging_mopping: bool | None = None,
) -> str:
    """Patch decoded CleanParamResponse params and re-encode for DPS 154 SET.

    Preserves other outer fields and inner fields (carpet, extent, etc.) when possible.
    """
    body = base64.b64decode(raw_b64)
    if not body:
        raise ValueError("empty clean param base64")
    # Match decode_clean_param_response / _strip_length_prefix: byte 0 is length, protobuf starts at 1
    payload = body[1:] if len(body) > 1 else b""

    outer = _parse_proto(payload)

    clean_type_names = ["sweep_only", "mop_only", "sweep_and_mop", "sweep_then_mop"]
    mop_level_names = ["low", "middle", "high"]

    def _patch_layer(inner_raw: Any) -> bytes:
        if not isinstance(inner_raw, bytes):
            inner_raw = b""
        inner: dict[int, Any] = dict(_parse_proto(inner_raw))

        if clean_type_key is not None:
            inner[1] = _serialize_proto({1: clean_type_names.index(clean_type_key)})

        if mop_level is not None or edge_hugging_mopping is not None:
            prev_m = inner.get(4)
            midx: int | None = None
            edge = 0
            if isinstance(prev_m, bytes):
                mf = _parse_proto(prev_m)
                midx = _as_varint(mf.get(1))
                edge = int(mf.get(2) or 0)
            if mop_level_key is not None:
                midx = mop_level_names.index(mop_level_key)
            if midx is None:
                midx = 0
            if edge_hugging_mopping is not None:
                edge = 1 if edge_hugging_mopping else 0
            inner[4] = _serialize_proto({1: midx, 2: edge})

        return _serialize_proto(inner)

    clean_type_key = None
    if clean_type is not None:
        key = clean_type.lower().replace(" ", "_").replace("-", "_")
        if key not in clean_type_names:
            raise ValueError(f"Unknown clean_type {clean_type!r}")
        clean_type_key = key

    mop_level_key = None
    if mop_level is not None or edge_hugging_mopping is not None:
        if mop_level is not None:
            mk = mop_level.lower().replace(" ", "_")
            if mk not in mop_level_names:
                raise ValueError(f"Unknown mop_level {mop_level!r}")
            mop_level_key = mk

    new_outer = dict(outer)
    fields_to_patch = (
        (1, 4)
        if edge_hugging_mopping is not None and mop_level is None
        else (1, 3, 4)
    )
    for field in fields_to_patch:
        if field in outer or field == 1:
            new_outer[field] = _patch_layer(outer.get(field))
    new_payload = _serialize_proto(new_outer)
    return _clean_param_b64_with_length_prefix(new_payload)


def _strip_length_prefix(raw_b64: str) -> bytes:
    """Decode base64 and strip the length prefix byte."""
    return base64.b64decode(raw_b64)[1:]


def _as_varint(val: Any) -> int | None:
    """Return integer from either a plain int or a sub-message {field_1: value}.

    Some firmware versions wrap scalar enums in single-field messages instead
    of encoding them as plain varints (e.g. RunState {value=1} instead of 1).
    """
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, bytes):
        inner = _parse_proto(val)
        return inner.get(1)
    return None


def _decode_packed_varints(data: bytes) -> list[int]:
    """Decode a packed repeated varint field into a list of integers."""
    values: list[int] = []
    pos = 0
    while pos < len(data):
        value, pos = _parse_varint(data, pos)
        values.append(value)
    return values


def decode_mode_ctrl(raw_b64: str) -> str:
    """Decode DPS 152 (ModeCtrlRequest) to a mode string.

    ModeCtrlRequest schema (control.proto):
      field_1 [varint]  method — command type:
                          0=START_AUTO_CLEAN, 1=START_SELECT_ROOMS_CLEAN,
                          2=START_SELECT_ZONES_CLEAN, 3=START_SPOT_CLEAN,
                          5=START_RC_CLEAN, 6=START_GOHOME, 9=START_FAST_MAPPING,
                          12=STOP_TASK, 13=PAUSE_TASK, 14=RESUME_TASK
      field_2 [varint]  seq — request sequence number (ignored for state lookup)
      field_3 [message] param — oneof Param (e.g. AutoClean for START_AUTO_CLEAN)
    """
    METHOD_NAMES = {
        0: "auto",
        1: "room",
        2: "spot",
        3: "spot",
        5: "start_manual",
        6: "stop",
        9: "fast_mapping",
        12: "standby",
        13: "pause",
        14: "nosweep",
    }

    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    method = fields.get(1)
    seq = fields.get(2)
    param = fields.get(3)

    # method=0 or absent with param present → auto clean
    if (method is None or method == 0) and param is not None:
        return "auto"

    # seq-only (no method, no param) → active-session update, treat as auto
    if method is None and param is None:
        if seq is not None:
            return "auto"
        return "standby"

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
    # gohome_bytes = fields.get(8)
    relocating_bytes = fields.get(10)
    breakpoint_bytes = fields.get(11)

    # Parse sub-messages
    mode_fields = _parse_proto(mode_bytes) if mode_bytes else {}
    charging_fields = _parse_proto(charging_bytes) if charging_bytes else {}
    cleaning_fields = _parse_proto(cleaning_bytes) if cleaning_bytes else {}
    # gohome_fields = _parse_proto(gohome_bytes) if gohome_bytes else {}
    relocating_fields = _parse_proto(relocating_bytes) if relocating_bytes else {}
    breakpoint_fields = _parse_proto(breakpoint_bytes) if breakpoint_bytes else {}

    mode = mode_fields.get(1, 0)
    charging_state = charging_fields.get(1)
    cleaning_run_state = cleaning_fields.get(1)
    # cleaning_mode = cleaning_fields.get(2)
    # gohome_run_state = gohome_fields.get(1)

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
    """Decode DPS 177/178 (ErrorCode) to a comma-separated error string.

    ErrorCode schema (error_code.proto):
      field_1  [uint64]           last_time  — CLOCK_MONOTONIC ns uptime (ignored)
      field_2  [repeated uint32]  error      — active error codes (may be packed)
      field_3  [repeated uint32]  warn       — active warning codes
      field_10 [message]          new_code   — newly triggered codes:
        field_1 [repeated uint32]  error
        field_2 [repeated uint32]  warn
    """
    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    codes_set: set[int] = set()

    def _collect(field_val: Any) -> None:
        if field_val is None:
            return
        if isinstance(field_val, list):
            codes_set.update(field_val)
        elif isinstance(field_val, int):
            codes_set.add(field_val)
        elif isinstance(field_val, bytes):
            # packed repeated uint32
            codes_set.update(_decode_packed_varints(field_val))

    # field_2: repeated error
    _collect(fields.get(2))

    # field_3: repeated warn
    _collect(fields.get(3))

    # field_10: new_code message
    new_code_bytes = fields.get(10)
    if new_code_bytes:
        new_code_fields = _parse_proto(new_code_bytes)
        _collect(new_code_fields.get(1))  # error
        _collect(new_code_fields.get(2))  # warn

    codes_set.discard(0)  # 0 = P0000_NONE / E0000_NONE — not a real code
    if not codes_set:
        return "no_error"

    def _lookup(code: int) -> str:
        if code in T2277_ERROR_CODES:
            return T2277_ERROR_CODES[code]
        if code in T2277_PROMPT_CODES:
            return T2277_PROMPT_CODES[code]
        return f"error_{code}"

    sorted_codes = sorted(codes_set)
    return ", ".join(_lookup(c) for c in sorted_codes)


# ---------------------------------------------------------------------------
# New DPS decoders
# ---------------------------------------------------------------------------


def decode_work_status_v2(raw_b64: str) -> str:
    """Decode DPS 173 (wrapped WorkStatus) to a status string.

    DPS 173 outer message:
      field_1 [message] WorkStatus — embedded WorkStatus (may omit State/Mode fields)
      field_2 [message] extra      — additional data (e.g. station state), ignored

    The embedded WorkStatus may encode sub-state RunState/Mode values as
    single-field sub-messages {value=N} instead of plain varints, as seen in
    T2278/T2275 firmware.  _as_varint() handles both encodings transparently.

    State is inferred from which sub-state messages are present when the
    explicit State field (field_2 of WorkStatus) is absent.
    """
    data = _strip_length_prefix(raw_b64)
    outer = _parse_proto(data)

    ws_bytes = outer.get(1)
    if not isinstance(ws_bytes, bytes) or not ws_bytes:
        return "Standby"

    fields = _parse_proto(ws_bytes)

    # Mode (field 1 of WorkStatus) — may be bytes or absent
    mode_val = 0
    mode_raw = fields.get(1)
    if isinstance(mode_raw, bytes):
        mode_val = _parse_proto(mode_raw).get(1, 0)

    # State (field 2) — varint or sub-message; may be absent
    state = _as_varint(fields.get(2))

    def _sub(field_num: int) -> dict[int, Any]:
        b = fields.get(field_num)
        return _parse_proto(b) if isinstance(b, bytes) and b else {}

    charging_fields = _sub(3)
    cleaning_fields = _sub(6)
    gowash_fields = _sub(7)
    gohome_fields = _sub(8)
    relocating_fields = _sub(10)
    breakpoint_fields = _sub(11)

    cleaning_run_state = _as_varint(cleaning_fields.get(1))
    gowash_run_state = _as_varint(gowash_fields.get(1))
    charging_state = _as_varint(charging_fields.get(1))

    # Infer overall state from sub-state presence when explicit state absent
    if state is None:
        if cleaning_fields or gowash_fields:
            state = 5   # CLEANING
        elif gohome_fields:
            state = 7   # GO_HOME
        elif charging_fields:
            state = 3   # CHARGING
        else:
            state = 0   # STANDBY

    if state == 0:
        return "Standby"
    if state == 1:
        return "Sleeping"
    if state == 2:
        return "error"
    if state == 3:   # CHARGING
        if charging_state == 1:
            return "completed"
        if breakpoint_fields:
            return "recharging"
        return "Charging"
    if state == 4:
        return "fast_mapping"
    if state == 5:   # CLEANING
        if relocating_fields:
            if mode_val == 1:
                return "room_positioning"
            if mode_val == 2:
                return "spot_positioning"
            return "positioning"
        if cleaning_run_state == 1:   # PAUSED
            if mode_val == 1:
                return "room_pause"
            if mode_val == 2:
                return "spot_pause"
            return "Paused"
        if gowash_run_state == 1:     # GoWash PAUSED
            return "Paused"
        if gowash_fields:
            return "going_to_wash"
        if mode_val == 0:
            return "auto"
        if mode_val == 1:
            return "room"
        if mode_val == 2:
            return "spot"
        return "auto"
    if state == 6:
        return "start_manual"
    if state == 7:   # GO_HOME
        if breakpoint_fields:
            return "going_to_recharge"
        return "going_to_charge"
    if state == 8:
        return "cruising"

    return f"state_{state}"


def decode_clean_param_response(raw_b64: str) -> dict[str, Any]:
    """Decode DPS 154 (CleanParamResponse) to a dict of cleaning parameters.

    CleanParamResponse schema (clean_param.proto):
      field_1 CleanParam clean_param          — global params
      field_2 CleanTimes clean_times          — deprecated
      field_3 CleanParam area_clean_param     — area-specific params
      field_4 CleanParam running_clean_param  — currently active params

    CleanParam fields:
      field_1 CleanType   {value: SWEEP_ONLY=0, MOP_ONLY=1, SWEEP_AND_MOP=2, SWEEP_THEN_MOP=3}
      field_2 CleanCarpet {strategy: AUTO_RAISE=0, AVOID=1, IGNORE=2}
      field_3 CleanExtent {value: NORMAL=0, NARROW=1, QUICK=2}
      field_4 MopMode     {level: LOW=0, MIDDLE=1, HIGH=2}
      field_5 Switch      smart_mode_sw
      field_6 Fan         {suction: QUIET=0, STANDARD=1, TURBO=2, MAX=3, MAX_PLUS=4}
      field_7 uint32      clean_times
    """
    FAN_NAMES = ["quiet", "standard", "turbo", "max", "max_plus"]
    CLEAN_TYPE_NAMES = ["sweep_only", "mop_only", "sweep_and_mop", "sweep_then_mop"]
    CARPET_NAMES = ["auto_raise", "avoid", "ignore"]
    EXTENT_NAMES = ["normal", "narrow", "quick"]
    MOP_LEVEL_NAMES = ["low", "middle", "high"]

    def _enum_val(b: Any) -> int:
        """Extract enum value from sub-message {field_1: N} or plain int."""
        if isinstance(b, bytes):
            return int(_parse_proto(b).get(1, 0))
        if isinstance(b, int):
            return b
        return 0

    def _decode_param(param_bytes: bytes | None) -> dict[str, Any]:
        if not param_bytes:
            return {}
        f = _parse_proto(param_bytes)
        result: dict[str, Any] = {}
        if 1 in f:
            v = _enum_val(f[1])
            result["clean_type"] = CLEAN_TYPE_NAMES[v] if v < len(CLEAN_TYPE_NAMES) else f"clean_type_{v}"
        if 2 in f:
            v = _enum_val(f[2])
            result["clean_carpet"] = CARPET_NAMES[v] if v < len(CARPET_NAMES) else f"carpet_{v}"
        if 3 in f:
            v = _enum_val(f[3])
            result["clean_extent"] = EXTENT_NAMES[v] if v < len(EXTENT_NAMES) else f"extent_{v}"
        if 4 in f:
            mop_fields = _parse_proto(f[4]) if isinstance(f[4], bytes) else {}
            v = _enum_val(f[4])
            result["mop_level"] = MOP_LEVEL_NAMES[v] if v < len(MOP_LEVEL_NAMES) else f"mop_{v}"
            result["edge_hugging_mopping"] = mop_fields.get(2) == 1
        if 6 in f:
            v = _enum_val(f[6])
            result["fan"] = FAN_NAMES[v] if v < len(FAN_NAMES) else f"fan_{v}"
        if 7 in f:
            result["clean_times"] = f[7] if isinstance(f[7], int) else 0
        return result

    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    result: dict[str, Any] = {}
    cp = _decode_param(fields.get(1))
    if cp:
        result["clean_param"] = cp
    acp = _decode_param(fields.get(3))
    if acp:
        result["area_clean_param"] = acp
    rcp = _decode_param(fields.get(4))
    if rcp:
        result["running_clean_param"] = rcp
    return result


def merge_clean_param_layers(decoded: dict[str, Any]) -> dict[str, Any]:
    """Merge clean_param / area_clean_param / running_clean_param for display.

    During an active job, ``running_clean_param`` often includes fan and mop
    fields but omits ``clean_type``; that value still lives on the global
    ``clean_param``. Later layers override earlier ones for keys present in both.
    """
    merged: dict[str, Any] = {}
    for layer in (
        decoded.get("clean_param"),
        decoded.get("area_clean_param"),
        decoded.get("running_clean_param"),
    ):
        if isinstance(layer, dict):
            merged.update(layer)
    return merged


def decode_consumable_response(raw_b64: str) -> dict[str, int]:
    """Decode DPS 168 (ConsumableResponse) to a dict of {name: hours}.

    ConsumableResponse schema (consumable.proto):
      field_1 ConsumableRuntime runtime

    ConsumableRuntime:
      field_1  Duration side_brush
      field_2  Duration rolling_brush
      field_3  Duration filter_mesh
      field_4  Duration scrape
      field_5  Duration sensor
      field_6  Duration mop
      field_7  Duration dustbag
      field_10 Duration dirty_watertank
      field_11 Duration dirty_waterfilter
      field_20 uint64   last_time  (ignored)

    Duration = {field_1 uint32 duration}  — unit: hours
    """
    FIELD_NAMES = {
        1: "side_brush",
        2: "rolling_brush",
        3: "filter_mesh",
        4: "scrape",
        5: "sensor",
        6: "mop",
        7: "dustbag",
        10: "dirty_watertank",
        11: "dirty_waterfilter",
    }

    data = _strip_length_prefix(raw_b64)
    outer = _parse_proto(data)

    runtime_bytes = outer.get(1)
    if not isinstance(runtime_bytes, bytes):
        return {}

    runtime = _parse_proto(runtime_bytes)
    result: dict[str, int] = {}
    for field_num, name in FIELD_NAMES.items():
        duration_bytes = runtime.get(field_num)
        if isinstance(duration_bytes, bytes):
            inner = _parse_proto(duration_bytes)
            hours = inner.get(1)
            if isinstance(hours, int):
                result[name] = hours
    return result


def decode_device_info(raw_b64: str) -> dict[str, Any]:
    """Decode DPS 169 (DeviceInfo) to a dict of device properties.

    DeviceInfo schema (app_device_info.proto):
      field_1  string  product_name
      field_2  string  video_sn
      field_3  string  device_mac
      field_4  string  software       — firmware version
      field_5  uint32  hardware       — hardware revision
      field_6  string  wifi_name
      field_7  string  wifi_ip
      field_8  string  last_user_id
      field_11 Station station        — base station info (optional)
      field_12 ProtoInfo proto_info
    """
    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    def _str(b: Any) -> str | None:
        if isinstance(b, bytes):
            try:
                return b.decode("utf-8")
            except UnicodeDecodeError:
                return None
        return None

    result: dict[str, Any] = {}
    for field_num, key in [
        (1, "product_name"),
        (2, "video_sn"),
        (3, "device_mac"),
        (4, "software"),
        (6, "wifi_name"),
        (7, "wifi_ip"),
        (8, "last_user_id"),
    ]:
        v = _str(fields.get(field_num))
        if v is not None:
            result[key] = v

    hw = fields.get(5)
    if isinstance(hw, int):
        result["hardware"] = hw

    return result


def decode_unisetting_response(raw_b64: str) -> dict[str, Any]:
    """Decode DPS 176 (UnisettingResponse) to a dict of device settings.

    UnisettingResponse schema (unisetting.proto):
      field_1  Switch  children_lock
      field_3  Switch  multi_map_sw
      field_10 Unistate unistate
        field_3 Switch  custom_clean_mode
        field_4 Active  map_valid
      field_11 uint32  ap_signal_strength   — 0-100
      field_12 WifiData wifi_data
        field_1 repeated Ap ap
          field_1 string ssid
          field_2 Frequency frequency      — FREQ_2_4G=0, FREQ_5G=1

    Switch = {field_1 bool value}  Active = {field_1 bool active}
    """
    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    def _switch_on(b: Any) -> bool:
        if isinstance(b, bytes):
            return bool(_parse_proto(b).get(1, 0) == 1)
        return False

    result: dict[str, Any] = {}

    result["children_lock"] = _switch_on(fields.get(1))
    result["multi_map"] = _switch_on(fields.get(3))

    unistate_bytes = fields.get(10)
    if isinstance(unistate_bytes, bytes):
        us = _parse_proto(unistate_bytes)
        result["custom_clean_mode"] = _switch_on(us.get(3))
        map_valid_bytes = us.get(4)
        if isinstance(map_valid_bytes, bytes):
            result["map_valid"] = _parse_proto(map_valid_bytes).get(1, 0) == 1

    signal = fields.get(11)
    if isinstance(signal, int):
        result["wifi_signal_pct"] = signal

    wifi_bytes = fields.get(12)
    if isinstance(wifi_bytes, bytes):
        wifi_fields = _parse_proto(wifi_bytes)
        ap_bytes = wifi_fields.get(1)
        if isinstance(ap_bytes, bytes):
            ap_fields = _parse_proto(ap_bytes)
            ssid_raw = ap_fields.get(1)
            if isinstance(ssid_raw, bytes):
                try:
                    result["wifi_ssid"] = ssid_raw.decode("utf-8")
                except UnicodeDecodeError:
                    pass
            freq = ap_fields.get(2)
            if isinstance(freq, int):
                result["wifi_frequency"] = "5GHz" if freq == 1 else "2.4GHz"

    return result


def decode_analysis_response(raw_b64: str) -> dict[str, Any]:
    """Decode DPS 179 (AnalysisResponse) to a dict with clean-record stats.

    AnalysisResponse schema (analysis.proto):
      field_1 AnalysisInternalStatus internal_status
      field_2 AnalysisStatistics     statistics
        field_1 CleanRecord clean
          field_1  uint32  clean_id
          field_2  bool    result        — true = success
          field_3  enum    fail_code     — UNKNOW=0, ROBOT_FAULT=1, ROBOT_ALERT=2, MANUAL_BREAK=3
          field_4  enum    mode          — AUTO_CLEAN=0, SELECT_ROOMS_CLEAN=1,
                                           SELECT_ZONES_CLEAN=2, SPOT_CLEAN=3, FAST_MAPPING=4
          field_5  enum    type          — SWEEP_ONLY=0, MOP_ONLY=1, SWEEP_AND_MOP=2
          field_6  uint64  start_time    — Unix seconds
          field_7  uint64  end_time      — Unix seconds
          field_8  uint32  clean_time    — seconds (excludes pauses)
          field_9  uint32  clean_area    — m²
          field_10 uint32  slam_area     — m²
          field_11 uint32  map_id
          field_12 uint32  room_count
          field_13 RollBrush roll_brush
    """
    MODES = ["auto_clean", "select_rooms_clean", "select_zones_clean", "spot_clean", "fast_mapping"]
    TYPES = ["sweep_only", "mop_only", "sweep_and_mop"]
    FAIL_CODES = ["unknown", "robot_fault", "robot_alert", "manual_break"]

    data = _strip_length_prefix(raw_b64)
    outer = _parse_proto(data)

    stats_bytes = outer.get(2)
    if not isinstance(stats_bytes, bytes):
        return {}

    stats = _parse_proto(stats_bytes)
    clean_bytes = stats.get(1)
    if not isinstance(clean_bytes, bytes):
        return {}

    cr = _parse_proto(clean_bytes)
    result: dict[str, Any] = {}

    if 1 in cr:
        result["clean_id"] = cr[1]
    if 2 in cr:
        result["success"] = bool(cr[2])
    if 3 in cr:
        v = cr[3]
        result["fail_code"] = FAIL_CODES[v] if isinstance(v, int) and v < len(FAIL_CODES) else str(v)
    if 4 in cr:
        v = cr[4]
        result["mode"] = MODES[v] if isinstance(v, int) and v < len(MODES) else f"mode_{v}"
    if 5 in cr:
        v = cr[5]
        result["clean_type"] = TYPES[v] if isinstance(v, int) and v < len(TYPES) else f"type_{v}"
    if 6 in cr:
        result["start_time"] = cr[6]
    if 7 in cr:
        result["end_time"] = cr[7]
    if 8 in cr:
        result["clean_time_s"] = cr[8]
    if 9 in cr:
        result["clean_area_m2"] = cr[9]
    if 10 in cr:
        result["slam_area_m2"] = cr[10]
    if 11 in cr:
        result["map_id"] = cr[11]
    if 12 in cr:
        result["room_count"] = cr[12]

    # RollBrush stats (field 13)
    rb_bytes = cr.get(13)
    if isinstance(rb_bytes, bytes):
        rb = _parse_proto(rb_bytes)
        if 1 in rb:
            result["roll_brush_protect_count"] = rb[1]
        if 2 in rb:
            result["roll_brush_stalled_count"] = rb[2]

    return result


def decode_clean_record_list(raw_b64: str) -> list[dict[str, Any]]:
    """Decode DPS 164 (clean record list) — structural decode of repeated records.

    DPS 164 uses a custom list wrapper not directly mirroring a single proto
    message.  Outer field_4 carries repeated CleanRecord-like sub-messages,
    each with a wrapped timestamp (field_1 {value}), status (field_2 {1:N}),
    and detail sub-messages.
    """
    data = _strip_length_prefix(raw_b64)
    outer = _parse_proto(data)

    record_list = outer.get(4)
    if record_list is None:
        return []
    if isinstance(record_list, bytes):
        record_list = [record_list]
    if not isinstance(record_list, list):
        return []

    records: list[dict[str, Any]] = []
    for entry_bytes in record_list:
        if not isinstance(entry_bytes, bytes):
            continue
        entry = _parse_proto(entry_bytes)
        rec: dict[str, Any] = {}

        # field_1: wrapped timestamp {1: unix_seconds}
        ts_bytes = entry.get(1)
        if isinstance(ts_bytes, bytes):
            ts_inner = _parse_proto(ts_bytes)
            ts = ts_inner.get(1)
            if isinstance(ts, int):
                rec["timestamp"] = ts

        # field_2: status {1: N}
        st_bytes = entry.get(2)
        if isinstance(st_bytes, bytes):
            st_inner = _parse_proto(st_bytes)
            st = st_inner.get(1)
            if isinstance(st, int):
                rec["status"] = st

        if rec:
            records.append(rec)

    return records


def decode_analysis_stats(raw_b64: str) -> dict[str, Any]:
    """Decode DPS 167 (AnalysisStatistics sub-set) — structural decode.

    DPS 167 carries a subset of AnalysisStatistics (analysis.proto) with fields
    matching CleanRecord (field_1), GoHomeRecord (field_2), and RelocateRecord
    (field_3).  Values are extracted as raw integers for caller interpretation.
    """
    data = _strip_length_prefix(raw_b64)
    fields = _parse_proto(data)

    def _flat(b: Any) -> dict[int, int]:
        if not isinstance(b, bytes):
            return {}
        return {k: v for k, v in _parse_proto(b).items() if isinstance(v, int)}

    result: dict[str, Any] = {}
    clean_flat = _flat(fields.get(1))
    if clean_flat:
        result["clean"] = clean_flat
    gohome_flat = _flat(fields.get(2))
    if gohome_flat:
        result["gohome"] = gohome_flat
    relocate_flat = _flat(fields.get(3))
    if relocate_flat:
        result["relocate"] = relocate_flat
    return result
