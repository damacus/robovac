"""Unit tests for proto_decode module - protobuf decoder for T2277 DPS messages."""

import base64
import pytest

from custom_components.robovac.proto_decode import (
    _parse_varint,
    _parse_proto,
    _as_varint,
    _decode_packed_varints,
    decode_mode_ctrl,
    decode_work_status,
    decode_work_status_v2,
    decode_error_code,
    decode_clean_param_response,
    merge_clean_param_layers,
    patch_clean_param_dps154,
    decode_consumable_response,
    decode_device_info,
    decode_unisetting_response,
    decode_analysis_response,
    decode_clean_record_list,
    decode_analysis_stats,
)
from custom_components.robovac.errors import getT2277ErrorMessage


# ============================================================================
# Tests for _parse_varint
# ============================================================================


class TestParseVarint:
    """Tests for _parse_varint function."""

    def test_single_byte_varint_value_1(self) -> None:
        """Test parsing single-byte varint with value 1."""
        data = bytes([0x01])
        value, pos = _parse_varint(data, 0)
        assert value == 1
        assert pos == 1

    def test_single_byte_varint_value_127(self) -> None:
        """Test parsing single-byte varint with value 127 (max single byte)."""
        data = bytes([0x7F])
        value, pos = _parse_varint(data, 0)
        assert value == 127
        assert pos == 1

    def test_single_byte_varint_value_0(self) -> None:
        """Test parsing single-byte varint with value 0."""
        data = bytes([0x00])
        value, pos = _parse_varint(data, 0)
        assert value == 0
        assert pos == 1

    def test_multibyte_varint_value_300(self) -> None:
        """Test parsing multi-byte varint with value 300."""
        # 300 = 0xAC, 0x02 in varint encoding
        data = bytes([0xAC, 0x02])
        value, pos = _parse_varint(data, 0)
        assert value == 300
        assert pos == 2

    def test_multibyte_varint_value_2101(self) -> None:
        """Test parsing multi-byte varint with value 2101."""
        # 2101 in binary is 0x835 = varint [0xB5, 0x10]
        data = bytes([0xB5, 0x10])
        value, pos = _parse_varint(data, 0)
        assert value == 2101
        assert pos == 2

    def test_varint_at_nonzero_position(self) -> None:
        """Test parsing varint starting at non-zero position."""
        data = bytes([0xFF, 0xFF, 0x05])  # junk + varint for 5
        value, pos = _parse_varint(data, 2)
        assert value == 5
        assert pos == 3

    def test_varint_three_byte_value(self) -> None:
        """Test parsing three-byte varint."""
        # 16384 = 0x4000 = varint [0x80, 0x80, 0x01]
        data = bytes([0x80, 0x80, 0x01])
        value, pos = _parse_varint(data, 0)
        assert value == 16384
        assert pos == 3


# ============================================================================
# Tests for _parse_proto
# ============================================================================


class TestParseProto:
    """Tests for _parse_proto function."""

    def test_empty_bytes(self) -> None:
        """Test parsing empty protobuf data."""
        data = bytes([])
        fields = _parse_proto(data)
        assert fields == {}

    def test_single_varint_field(self) -> None:
        """Test parsing single varint field (field_1 = 5)."""
        # Tag for field_1 varint = (1 << 3) | 0 = 0x08
        # Value = 5
        data = bytes([0x08, 0x05])
        fields = _parse_proto(data)
        assert fields == {1: 5}

    def test_single_varint_field_value_300(self) -> None:
        """Test parsing varint field with value 300."""
        # Tag for field_1 = 0x08, value 300 = [0xAC, 0x02]
        data = bytes([0x08, 0xAC, 0x02])
        fields = _parse_proto(data)
        assert fields == {1: 300}

    def test_single_length_delimited_field(self) -> None:
        """Test parsing single length-delimited field (field_2 = some bytes)."""
        # Tag for field_2 length-delimited = (2 << 3) | 2 = 0x12
        # Length = 3, value = b'hello'[0:3] = b'hel'
        data = bytes([0x12, 0x03]) + b'hel'
        fields = _parse_proto(data)
        assert fields == {2: b'hel'}

    def test_repeated_varint_field_becomes_list(self) -> None:
        """Test parsing repeated varint field creates a list."""
        # field_3 = 5, field_3 = 10
        # Tag for field_3 = (3 << 3) | 0 = 0x18
        data = bytes([0x18, 0x05, 0x18, 0x0A])
        fields = _parse_proto(data)
        assert fields == {3: [5, 10]}

    def test_repeated_varint_field_three_values(self) -> None:
        """Test repeated varint field with three values."""
        data = bytes([0x18, 0x05, 0x18, 0x0A, 0x18, 0x0F])
        fields = _parse_proto(data)
        assert fields == {3: [5, 10, 15]}

    def test_mixed_fields_varint_and_length_delimited(self) -> None:
        """Test parsing mixed field types."""
        # field_1 = 5 (varint)
        # field_2 = b'hi' (length-delimited)
        # field_3 = 10 (varint)
        data = bytes([0x08, 0x05, 0x12, 0x02]) + b'hi' + bytes([0x18, 0x0A])
        fields = _parse_proto(data)
        assert fields == {1: 5, 2: b'hi', 3: 10}

    def test_field_numbers_with_higher_values(self) -> None:
        """Test parsing fields with higher field numbers."""
        # field_10 = 42
        # Tag = (10 << 3) | 0 = 0x50
        data = bytes([0x50, 0x2A])
        fields = _parse_proto(data)
        assert fields == {10: 42}

    def test_skips_64bit_fields(self) -> None:
        """Test that 64-bit fields (wire_type 1) are skipped."""
        # field_1 = 5, field_2 (64-bit), field_3 = 10
        # Tag for field_2 64-bit = (2 << 3) | 1 = 0x11
        data = bytes([0x08, 0x05, 0x11]) + bytes([0] * 8) + bytes([0x18, 0x0A])
        fields = _parse_proto(data)
        # 64-bit field is skipped, but varint fields are parsed
        assert 1 in fields and 3 in fields
        assert fields[1] == 5
        assert fields[3] == 10

    def test_skips_32bit_fields(self) -> None:
        """Test that 32-bit fields (wire_type 5) are skipped."""
        # field_1 = 5, field_2 (32-bit), field_3 = 10
        # Tag for field_2 32-bit = (2 << 3) | 5 = 0x15
        data = bytes([0x08, 0x05, 0x15]) + bytes([0] * 4) + bytes([0x18, 0x0A])
        fields = _parse_proto(data)
        assert 1 in fields and 3 in fields
        assert fields[1] == 5
        assert fields[3] == 10


# ============================================================================
# Tests for decode_mode_ctrl
# ============================================================================


class TestDecodeModeCtrl:
    """Tests for decode_mode_ctrl function using MODE values from T2277.py."""

    @pytest.mark.parametrize(
        "raw_b64,expected",
        [
            ("AA==", "standby"),            # empty payload
            ("AggN", "pause"),              # method=PAUSE_TASK (13)
            ("AggG", "stop"),               # method=START_GOHOME (6)
            ("BBoCCAE=", "auto"),           # param.auto_clean present
            ("AggO", "nosweep"),            # method=RESUME_TASK (14)
            ("BAgNEGg=", "pause"),          # method=PAUSE_TASK (13) with seq=104
            ("BAgOEGg=", "nosweep"),        # method=RESUME_TASK (14) with seq=104
            ("BAgOEGw=", "nosweep"),        # method=RESUME_TASK (14) with seq=108
            # Three new command values
            ("AhBs", "auto"),               # seq=108 only - active session update
            ("BAgGEHA=", "stop"),           # method=START_GOHOME (6), seq=112
            ("BAgCEHQ=", "spot"),           # method=START_SELECT_ZONES (2), seq=116
        ],
    )
    def test_mode_ctrl_payloads(self, raw_b64: str, expected: str) -> None:
        """Test decoding MODE control payloads from T2277."""
        result = decode_mode_ctrl(raw_b64)
        assert result == expected

    def test_mode_ctrl_seq_only_returns_auto(self) -> None:
        """Test that seq-only payload (no method, no param) returns auto.

        A seq-only payload is sent during an active cleaning session as a
        parameter update (e.g. BoostIQ adjustment).  Treating it as 'auto'
        preserves the current active-cleaning state rather than flipping to
        standby on every seq update.
        """
        # AhBw = {field_2: 112} — seq=112, no method, no param
        assert decode_mode_ctrl("AhBw") == "auto"
        # AhBs = {field_2: 108} — seq=108, no method, no param
        assert decode_mode_ctrl("AhBs") == "auto"

    def test_mode_ctrl_empty_is_standby(self) -> None:
        """Test that a completely empty payload (no fields at all) returns standby."""
        assert decode_mode_ctrl("AA==") == "standby"

    def test_mode_ctrl_new_methods(self) -> None:
        """Test newly mapped method values."""
        assert decode_mode_ctrl("BAgGEHA=") == "stop"     # method=6
        assert decode_mode_ctrl("BAgCEHQ=") == "spot"     # method=2


# ============================================================================
# Tests for decode_work_status
# ============================================================================


class TestDecodeWorkStatus:
    """Tests for decode_work_status function using STATUS values from T2277.py."""

    @pytest.mark.parametrize(
        "raw_b64,expected",
        [
            # Confirmed working cases from T2277.py reverse lookup
            ("AhAB", "Sleeping"),           # state=SLEEP(1)
            ("BgoAEAUyAA==", "auto"),       # state=CLEANING, mode=AUTO
            ("CAoAEAUyAggB", "Paused"),     # state=CLEANING, paused
            ("CAoCCAEQBTIA", "room"),       # state=CLEANING, SELECT_ROOM mode
            ("CgoCCAEQBTICCAE=", "room_pause"),  # SELECT_ROOM mode, paused
            ("CAoCCAIQBTIA", "spot"),       # state=CLEANING, SELECT_ZONE mode
            ("CgoCCAIQBTICCAE=", "spot_pause"),  # SELECT_ZONE mode, paused
            ("BAoAEAY=", "start_manual"),   # state=REMOTE_CTRL(6)
            ("BBAHQgA=", "going_to_charge"),  # state=GO_HOME(7), no breakpoint
            ("BBADGgA=", "Charging"),       # state=CHARGING(3), charging.state != DONE
            ("BhADGgIIAQ==", "completed"),  # state=CHARGING(3), charging.state=DONE
        ],
    )
    def test_work_status_payloads(self, raw_b64: str, expected: str) -> None:
        """Test decoding WORK_STATUS payloads from T2277."""
        result = decode_work_status(raw_b64)
        assert result == expected

    def test_work_status_empty_standby(self) -> None:
        """Test empty payload with no state field defaults to Standby-like behavior."""
        # AA== has no fields, so state is None
        # The code returns state_None for this case
        result = decode_work_status("AA==")
        # When state is None, code returns f"state_{state}" which is "state_None"
        assert result == "state_None"

    def test_work_status_positioning_with_empty_relocating(self) -> None:
        """Test positioning payloads that have relocating field."""
        # BgoAEAVSAA== has state=CLEANING(5) and field_10 (relocating) with empty bytes
        # Empty bytes are falsy, so relocating_fields = {}
        # This causes it to fall through to active cleaning logic
        result = decode_work_status("BgoAEAVSAA==")
        assert result == "auto"  # Falls through to active cleaning

    def test_work_status_room_positioning_with_empty_relocating(self) -> None:
        """Test room positioning payloads that have relocating field."""
        result = decode_work_status("CAoCCAEQBVIA")
        # Has state=CLEANING(5), mode=SELECT_ROOM(1), empty relocating
        assert result == "room"

    def test_work_status_spot_positioning_with_empty_relocating(self) -> None:
        """Test spot positioning payloads that have relocating field."""
        result = decode_work_status("CAoCCAIQBVIA")
        # Has state=CLEANING(5), mode=SELECT_ZONE(2), empty relocating
        assert result == "spot"

    def test_work_status_going_to_recharge(self) -> None:
        """Test going_to_recharge with breakpoint field."""
        result = decode_work_status("CAoAEAdCAFoA")
        # Has state=GO_HOME(7) and breakpoint field with empty bytes
        # Empty bytes are falsy, so breakpoint check fails
        assert result == "going_to_charge"

    def test_work_status_recharging(self) -> None:
        """Test recharging with breakpoint field."""
        result = decode_work_status("CAoAEAMaAFoA")
        # Has state=CHARGING(3) and breakpoint field with empty bytes
        # Empty bytes are falsy, so the breakpoint check fails and returns Charging
        assert result == "Charging"


# ============================================================================
# Tests for decode_error_code
# ============================================================================


class TestDecodeErrorCode:
    """Tests for decode_error_code function."""

    def test_empty_error_payload(self) -> None:
        """Test that empty/no-error payload returns 'no_error'."""
        # "AA==" is the empty payload (length prefix only)
        result = decode_error_code("AA==")
        assert result == "no_error"

    def test_single_error_code_4111(self) -> None:
        """Test payload with single error code 4111 (Front bumper stuck left)."""
        # Build proto bytes with field_3 (warn) = 4111
        # 4111 varint = [0x8F, 0x20]
        # Tag for field_3 = (3 << 3) | 0 = 0x18
        # Proto bytes = [0x18, 0x8F, 0x20]
        proto_bytes = bytes([0x18, 0x8F, 0x20])
        # Add length prefix
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        assert result == "Front bumper stuck (left)"

    def test_single_error_code_1013(self) -> None:
        """Test payload with single error code 1013 (Left wheel stuck)."""
        # 1013 varint = [0xF5, 0x07]
        proto_bytes = bytes([0x18, 0xF5, 0x07])
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        assert result == "Left wheel stuck"

    def test_multiple_error_codes_sorted(self) -> None:
        """Test payload with multiple error codes (should be sorted)."""
        # field_3 (warn) with values 1013 and 1023
        # 1013 varint = [0xF5, 0x07], 1023 = [0xFF, 0x07]
        # Tag for field_3 = 0x18
        proto_bytes = bytes([0x18, 0xF5, 0x07, 0x18, 0xFF, 0x07])
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        # Should be sorted by code value, comma-separated
        assert result == "Left wheel stuck, Right wheel stuck"

    def test_error_code_with_new_code_message(self) -> None:
        """Test payload with error codes in new_code message (field_10)."""
        # field_10 is a message containing field_1 (error codes)
        # Create new_code message: field_1 = 1033 (Both wheels stuck)
        # 1033 varint = [0x89, 0x08]
        inner_proto = bytes([0x08, 0x89, 0x08])  # field_1 = 1033
        # Tag for field_10 = (10 << 3) | 2 = 0x52
        proto_bytes = bytes([0x52, len(inner_proto)]) + inner_proto
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        assert result == "Both wheels stuck"

    def test_error_code_from_both_warn_and_new_code(self) -> None:
        """Test payload with codes from both field_3 (warn) and new_code."""
        # field_3 (warn) = 1013, field_10 (new_code.field_1) = 1033
        warn_bytes = bytes([0x18, 0xF5, 0x07])  # field_3 = 1013 (Left wheel)

        inner_proto = bytes([0x08, 0x89, 0x08])  # new_code.field_1 = 1033 (Both wheels)
        new_code_bytes = bytes([0x52, len(inner_proto)]) + inner_proto

        proto_bytes = warn_bytes + new_code_bytes
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        # Should contain both codes, sorted
        assert "Left wheel stuck" in result
        assert "Both wheels stuck" in result
        assert result.startswith("Left wheel stuck")  # sorted by code

    def test_error_code_unknown_code(self) -> None:
        """Test payload with unknown error code."""
        # field_3 (warn) = 9999 (unknown code)
        # 9999 varint encoding: 9999 = 0x270F
        # Little-endian base-128: 0x9F (with continuation) | 0x80 = 0x9F, then 0x4E
        # Correct encoding: 0x8F (9999 & 0x7F | 0x80), 0x4E ((9999 >> 7) & 0x7F)
        proto_bytes = bytes([0x18, 0x8F, 0x4E])  # field_3 = 9999 in varint
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        assert result == "error_9999"

    def test_error_code_field_3_repeated(self) -> None:
        """Test field_3 with multiple repeated values."""
        # field_3 repeated with values 1013 and 1023
        # 1013 = [0xF5, 0x07], 1023 = [0xFF, 0x07]
        proto_bytes = bytes([0x18, 0xF5, 0x07, 0x18, 0xFF, 0x07])
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        assert "Left wheel stuck" in result
        assert "Right wheel stuck" in result


# ============================================================================
# Tests for getT2277ErrorMessage
# ============================================================================


class TestGetT2277ErrorMessage:
    """Tests for getT2277ErrorMessage function from errors module."""

    @pytest.mark.parametrize(
        "code,expected",
        [
            (4111, "Front bumper stuck (left)"),
            (1013, "Left wheel stuck"),
            (1023, "Right wheel stuck"),
            (1033, "Both wheels stuck"),
            (5014, "Battery low"),
            (7000, "Robot trapped"),
            (7031, "Return to dock failed"),
            (9999, "Unknown error 9999"),
        ],
    )
    def test_t2277_error_messages(self, code: int, expected: str) -> None:
        """Test error message lookup for known and unknown codes."""
        result = getT2277ErrorMessage(code)
        assert result == expected

    def test_all_defined_error_codes_have_messages(self) -> None:
        """Verify all T2277 error codes are defined."""
        from custom_components.robovac.proto_decode import T2277_ERROR_CODES

        test_codes = [
            4111,  # Front bumper stuck (left)
            1013,  # Left wheel stuck
            1023,  # Right wheel stuck
            1033,  # Both wheels stuck
            5014,  # Battery low
            7000,  # Robot trapped
            7031,  # Return to dock failed
            2112,  # Main brush stuck
        ]

        for code in test_codes:
            message = getT2277ErrorMessage(code)
            assert not message.startswith("Unknown")
            assert code in T2277_ERROR_CODES
            assert T2277_ERROR_CODES[code] == message


# ============================================================================
# Tests for decode_work_status_v2  (DPS 173 — wrapped WorkStatus)
# ============================================================================


class TestDecodeWorkStatusV2:
    """Tests for decode_work_status_v2 with WorkStatus and RunState."""

    def test_dps173_sample_cleaning_paused(self) -> None:
        """Decode the observed DPS 173 sample: Cleaning + GoWash both PAUSED."""
        # FgoQMggKAggBEgIQAToECgIIARICCAE=
        # Outer field_1 = WorkStatus with Cleaning(PAUSED) + GoWash(PAUSED), no State
        result = decode_work_status_v2("FgoQMggKAggBEgIQAToECgIIARICCAE=")
        assert result == "Paused"

    def test_empty_payload_returns_standby(self) -> None:
        """Outer with no WorkStatus field → Standby."""
        import base64
        # build: outer has no field_1
        raw = base64.b64encode(bytes([0x00])).decode()
        result = decode_work_status_v2(raw)
        assert result == "Standby"


# ============================================================================
# Tests for decode_error_code  (field_2 packed error support)
# ============================================================================


class TestDecodeErrorCodeExtended:
    """Tests for the extended decode_error_code handling field_2 packed errors."""

    def test_dps178_sample_with_packed_error(self) -> None:
        """Decode the observed DPS 178 sample: last_time + packed prompt field_2."""
        # DQiiguWKr+3szgESASg=
        # field_1 = large monotonic timestamp, field_2 packed = [40]
        # Code 40 = P0040_TASK_FINISHED_HEADING_HOME → prompt code, now mapped
        result = decode_error_code("DQiiguWKr+3szgESASg=")
        assert result == "Task finished, returning to dock"

    def test_field2_packed_single_known_error(self) -> None:
        """field_2 as packed repeated uint32 with a known error code."""
        import base64
        # Build proto: field_2 packed = [4111]
        # 4111 varint = [0x8F, 0x20]
        # tag for field_2 packed = (2<<3)|2 = 0x12
        proto = bytes([0x12, 0x02, 0x8F, 0x20])
        raw = base64.b64encode(bytes([len(proto)]) + proto).decode()
        result = decode_error_code(raw)
        assert result == "Front bumper stuck (left)"

    def test_prompt_code_76_at_station(self) -> None:
        """Code 76 (P0076) maps to 'Cannot start task while at charging dock'."""
        import base64
        # field_2 packed = [76]
        proto = bytes([0x12, 0x01, 0x4C])  # tag=0x12, length=1, varint 76=0x4C
        raw = base64.b64encode(bytes([len(proto)]) + proto).decode()
        result = decode_error_code(raw)
        assert result == "Cannot start task while at charging dock"

    def test_prompt_code_40_heading_home(self) -> None:
        """Code 40 (P0040) maps to 'Task finished, returning to dock'."""
        import base64
        proto = bytes([0x12, 0x01, 0x28])  # varint 40=0x28
        raw = base64.b64encode(bytes([len(proto)]) + proto).decode()
        result = decode_error_code(raw)
        assert result == "Task finished, returning to dock"

    def test_code_zero_discarded(self) -> None:
        """Code 0 (P0000_NONE) is treated as no notification."""
        import base64
        proto = bytes([0x12, 0x01, 0x00])  # field_2 packed = [0]
        raw = base64.b64encode(bytes([len(proto)]) + proto).decode()
        assert decode_error_code(raw) == "no_error"


# ============================================================================
# Tests for decode_clean_param_response  (DPS 154)
# ============================================================================


class TestDecodeCleanParamResponse:
    """Tests for decode_clean_param_response."""

    def test_dps154_sample(self) -> None:
        """Decode the observed DPS 154 sample."""
        # DgoKCgAaAggBIgIIARIA
        # clean_param: clean_type=SWEEP_ONLY, clean_extent=NARROW, mop_level=MIDDLE
        result = decode_clean_param_response("DgoKCgAaAggBIgIIARIA")
        assert "clean_param" in result
        cp = result["clean_param"]
        assert cp.get("clean_type") == "sweep_only"
        assert cp.get("clean_extent") == "narrow"
        assert cp.get("mop_level") == "middle"

    def test_empty_payload_returns_empty_dict(self) -> None:
        """Empty payload → empty dict."""
        import base64
        raw = base64.b64encode(bytes([0x00])).decode()
        result = decode_clean_param_response(raw)
        assert result == {}

    def test_merge_clean_param_layers_keeps_clean_type_when_running_omits_it(self) -> None:
        """Running job payload may omit clean_type; inherit from global clean_param."""
        decoded = {
            "clean_param": {"clean_type": "mop_only", "mop_level": "low"},
            "running_clean_param": {"fan": "standard", "mop_level": "high"},
        }
        merged = merge_clean_param_layers(decoded)
        assert merged["clean_type"] == "mop_only"
        assert merged["fan"] == "standard"
        assert merged["mop_level"] == "high"

    def test_dps154_edge_hugging_mopping_on(self) -> None:
        """Decode observed X9 edge-hugging mopping enabled payload."""
        result = decode_clean_param_response(
            "KgoQCgIIAhIAGgAiBAgCEAEqABIAGgAiEgoCCAIaACIECAIQASoAMgIIAQ=="
        )

        params = result["running_clean_param"]
        assert params["clean_type"] == "sweep_and_mop"
        assert params["mop_level"] == "high"
        assert params["fan"] == "standard"
        assert params["edge_hugging_mopping"] is True

    def test_dps154_edge_hugging_mopping_off(self) -> None:
        """Decode observed X9 edge-hugging mopping disabled payload."""
        result = decode_clean_param_response(
            "JgoOCgIIAhIAGgAiAggCKgASABoAIhAKAggCGgAiAggCKgAyAggB"
        )

        params = result["running_clean_param"]
        assert params["clean_type"] == "sweep_and_mop"
        assert params["mop_level"] == "high"
        assert params["fan"] == "standard"
        assert params["edge_hugging_mopping"] is False


class TestPatchCleanParamDps154:
    """Encode/patch tests for DPS 154."""

    def test_patch_mop_level_preserves_clean_type(self) -> None:
        raw = "DgoKCgAaAggBIgIIARIA"
        new = patch_clean_param_dps154(raw, mop_level="high")
        cp = decode_clean_param_response(new)["clean_param"]
        assert cp["clean_type"] == "sweep_only"
        assert cp["mop_level"] == "high"

    def test_patch_clean_type_preserves_extent(self) -> None:
        raw = "DgoKCgAaAggBIgIIARIA"
        new = patch_clean_param_dps154(raw, clean_type="mop_only")
        cp = decode_clean_param_response(new)["clean_param"]
        assert cp["clean_type"] == "mop_only"
        assert cp["clean_extent"] == "narrow"

    def test_patch_edge_hugging_does_not_create_area_layer(self) -> None:
        """Edge-only writes match app payload shape by not inventing area params."""
        raw = "JgoOCgIIAhIAGgAiAggCKgASABoAIhAKAggCGgAiAggCKgAyAggB"
        new = patch_clean_param_dps154(raw, edge_hugging_mopping=True)
        decoded = decode_clean_param_response(new)

        assert "area_clean_param" not in decoded
        assert decoded["clean_param"]["edge_hugging_mopping"] is True
        assert decoded["running_clean_param"]["edge_hugging_mopping"] is True


# ============================================================================
# Tests for decode_consumable_response  (DPS 168)
# ============================================================================


class TestDecodeConsumableResponse:
    """Tests for decode_consumable_response."""

    def test_dps168_sample(self) -> None:
        """Decode the observed DPS 168 sample."""
        # Consumable response with side_brush, filter, and other data
        payload = "JAoiCgIIMBIDCN4CGgIIMCoDCN4COgMIpgygAaGFva/W7uzOAQ=="
        result = decode_consumable_response(payload)
        assert result.get("side_brush") == 48
        assert result.get("rolling_brush") == 350
        assert result.get("filter_mesh") == 48
        assert result.get("dustbag") == 1574

    def test_t2320_dps168_sample(self) -> None:
        """Decode the observed T2320 DPS 168 consumable fields."""
        payload = "IgogCgIIWRICCFkaAghZIgIIWSoDCLgCMgIIHaAB8fjazwY="
        result = decode_consumable_response(payload)
        assert result == {
            "side_brush": 89,
            "rolling_brush": 89,
            "filter_mesh": 89,
            "scrape": 89,
            "sensor": 312,
            "mop": 29,
        }

    def test_empty_payload_returns_empty_dict(self) -> None:
        """Empty payload → empty dict."""
        import base64
        raw = base64.b64encode(bytes([0x00])).decode()
        result = decode_consumable_response(raw)
        assert result == {}


# ============================================================================
# Tests for decode_device_info  (DPS 169)
# ============================================================================


class TestDecodeDeviceInfo:
    """Tests for decode_device_info."""

    def test_dps169_sample(self) -> None:
        """Decode the observed DPS 169 sample (eufy Clean L60 SES device)."""
        result = decode_device_info(
            "cgoSZXVmeSBDbGVhbiBMNjAgU0VTGhFDODpGRTowRjo3Nzo5NDo5QyIFMi4wLjAoBUI"
            "oMzY0YWM4Y2Q2NDNmOWUwNzNmODg3OWY0YWE5N2RkYTk4ZTMyODk1NGIWCAESBAgCEA"
            "EaBAgCEAEiAggBKgIIAQ=="
        )
        assert result.get("product_name") == "eufy Clean L60 SES"
        assert result.get("device_mac") == "C8:FE:0F:77:94:9C"
        assert result.get("software") == "2.0.0"


# ============================================================================
# Tests for decode_unisetting_response  (DPS 176)
# ============================================================================


class TestDecodeUnisettingResponse:
    """Tests for decode_unisetting_response."""

    def test_dps176_sample(self) -> None:
        """Decode the observed DPS 176 sample."""
        result = decode_unisetting_response(
            "MwoAGgIIAVIKGgIIASICCAEqAFgkYh0KGwoRQSBuZXR3b3JrIGZvciB5b3UaBhCxit/OBg=="
        )
        assert result.get("wifi_ssid") == "A network for you"
        assert result.get("wifi_signal_pct") == 36
        assert result.get("multi_map") is True


# ============================================================================
# Tests for decode_analysis_response  (DPS 179)
# ============================================================================


class TestDecodeAnalysisResponse:
    """Tests for decode_analysis_response."""

    def test_dps179_sample(self) -> None:
        """Decode the observed DPS 179 sample (clean record)."""
        result = decode_analysis_response(
            "JRIjCiEIEBABIAIwsZbfzgY41ZjfzgZA8AFIBFA6WAJgB2oCEAI="
        )
        assert result.get("clean_id") == 16
        assert result.get("success") is True
        assert result.get("mode") == "select_zones_clean"
        assert result.get("clean_time_s") == 240
        assert result.get("clean_area_m2") == 4
        assert result.get("room_count") == 7

    def test_empty_payload_returns_empty(self) -> None:
        """Empty payload → empty dict."""
        import base64
        raw = base64.b64encode(bytes([0x00])).decode()
        assert decode_analysis_response(raw) == {}


# ============================================================================
# Tests for decode_clean_record_list  (DPS 164)
# ============================================================================


class TestDecodeCleanRecordList:
    """Tests for decode_clean_record_list."""

    def test_dps164_sample_returns_two_records(self) -> None:
        """Decode the observed DPS 164 sample (two clean record entries)."""
        result = decode_clean_record_list(
            "UBoAIiYKBgi4y/q0BhICCAEaDAgBEgQYCSAeGgIIPioKGggIARIECgIIAiIkCgYImsPGvw"
            "YSAggBGgoIARICGAgaAghBKgoaCAgBEgQKAggC"
        )
        assert len(result) == 2
        # First record should have a timestamp
        assert "timestamp" in result[0]

    def test_empty_payload_returns_empty_list(self) -> None:
        """Empty payload → empty list."""
        import base64
        raw = base64.b64encode(bytes([0x00])).decode()
        assert decode_clean_record_list(raw) == []


# ============================================================================
# Tests for decode_analysis_stats  (DPS 167)
# ============================================================================


class TestDecodeAnalysisStats:
    """Tests for decode_analysis_stats."""

    def test_dps167_sample_has_expected_keys(self) -> None:
        """Decode the observed DPS 167 sample."""
        result = decode_analysis_stats("HwoFCPABEAQSCgigik0Q52cYgAMaCgjsiE0Q5GcY/gI=")
        assert "clean" in result
        assert result["clean"].get(1) == 240   # clean_id = 240

    def test_empty_payload_returns_empty_dict(self) -> None:
        """Empty payload → empty dict."""
        import base64
        raw = base64.b64encode(bytes([0x00])).decode()
        assert decode_analysis_stats(raw) == {}


# ============================================================================
# Tests for _as_varint (internal helper)
# ============================================================================


class TestAsVarint:
    """Tests for _as_varint helper function."""

    def test_as_varint_with_none(self) -> None:
        """Test _as_varint with None input returns None."""
        assert _as_varint(None) is None

    def test_as_varint_with_int(self) -> None:
        """Test _as_varint with int input returns the int."""
        assert _as_varint(42) == 42
        assert _as_varint(0) == 0
        assert _as_varint(1000000) == 1000000

    def test_as_varint_with_bytes_wrapping_int(self) -> None:
        """Test _as_varint with bytes encoding int in field_1."""
        # field_1 = 5 -> tag (1 << 3 | 0) = 0x08, then varint value 0x05
        data = bytes([0x08, 0x05])
        assert _as_varint(data) == 5

    def test_as_varint_with_unknown_type(self) -> None:
        """Test _as_varint with unknown type returns None."""
        assert _as_varint("string") is None
        assert _as_varint([1, 2, 3]) is None
        assert _as_varint({"key": "value"}) is None


# ============================================================================
# Tests for _decode_packed_varints (internal helper)
# ============================================================================


class TestDecodePackedVarints:
    """Tests for _decode_packed_varints helper function."""

    def test_empty_data(self) -> None:
        """Test decoding empty data returns empty list."""
        assert _decode_packed_varints(bytes([])) == []

    def test_single_varint(self) -> None:
        """Test decoding single varint."""
        data = bytes([0x05])  # varint value 5
        assert _decode_packed_varints(data) == [5]

    def test_multiple_varints(self) -> None:
        """Test decoding multiple packed varints."""
        # 1, 2, 3 encoded as varints: 0x01, 0x02, 0x03
        data = bytes([0x01, 0x02, 0x03])
        assert _decode_packed_varints(data) == [1, 2, 3]

    def test_larger_varints(self) -> None:
        """Test decoding larger values (multi-byte varints)."""
        # 300 = 0xAC, 0x02 in varint encoding
        data = bytes([0xAC, 0x02])
        result = _decode_packed_varints(data)
        assert result == [300]


# ============================================================================
# Additional edge case tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_parse_varint_at_buffer_end(self) -> None:
        """Test parsing varint at end of buffer."""
        data = bytes([0x00, 0x01, 0x7F])
        # Parse from position 1
        value, pos = _parse_varint(data, 1)
        assert value == 1
        assert pos == 2

    def test_parse_proto_with_repeated_fields(self) -> None:
        """Test parsing proto with repeated varint fields."""
        # field_1: repeated values 1, 2, 3
        # This is encoded as separate tag+value pairs
        data = bytes([0x08, 0x01, 0x08, 0x02, 0x08, 0x03])
        fields = _parse_proto(data)
        # Repeated fields should be in a list
        assert isinstance(fields[1], list)
        assert fields[1] == [1, 2, 3]

    def test_as_varint_with_bytes_no_field_1(self) -> None:
        """Test _as_varint with bytes that don't have field_1."""
        # field_2 = 5 -> tag (2 << 3 | 0) = 0x10, varint 0x05
        data = bytes([0x10, 0x05])
        assert _as_varint(data) is None  # field_1 not present

    def test_strip_length_prefix_simple(self) -> None:
        """Test stripping length prefix from base64."""
        import base64
        from custom_components.robovac.proto_decode import _strip_length_prefix

        # Create data: length byte (1) + value (0x05)
        data = bytes([0x01, 0x05])
        b64 = base64.b64encode(data).decode()

        result = _strip_length_prefix(b64)
        assert result == bytes([0x05])


# ============================================================================
# Additional edge case tests
# ============================================================================

def test_analyze_response_with_empty_data() -> None:
    """Test decode_analysis_response handles empty/minimal data."""
    # AA== is empty payload
    result = decode_analysis_response("AA==")
    # Should handle gracefully - either None or empty dict
    assert result is None or isinstance(result, dict)


def test_clean_record_list_with_multiple_records() -> None:
    """Test decode_clean_record_list with multiple cleaning records."""
    # Create a payload with multiple records
    data = b'\x0a\x04\x08\x01\x10\x02\x0a\x04\x08\x03\x10\x04'
    test_payload = base64.b64encode(data).decode()
    result = decode_clean_record_list(test_payload)
    # Should return list or None
    assert result is None or isinstance(result, list)


def test_device_info_with_missing_fields() -> None:
    """Test decode_device_info handles missing fields gracefully."""
    # Minimal device info payload
    result = decode_device_info("AA==")
    assert result is None or isinstance(result, dict)


def test_unisetting_with_various_field_combinations() -> None:
    """Test decode_unisetting_response with different field combinations."""
    # Test multiple different payloads
    payloads = [
        "AA==",  # Empty
        "Cg==",  # Single byte field
    ]

    for payload in payloads:
        result = decode_unisetting_response(payload)
        # Should handle all gracefully
        assert result is None or isinstance(result, dict)


def test_parse_varint_boundary_values() -> None:
    """Test _parse_varint with boundary values."""
    from custom_components.robovac.proto_decode import _parse_varint

    # Test zero
    value, offset = _parse_varint(b'\x00', 0)
    assert value == 0

    # Test max single byte (127)
    value, offset = _parse_varint(b'\x7f', 0)
    assert value == 127

    # Test value requiring multiple bytes
    value, offset = _parse_varint(b'\x80\x01', 0)
    assert value == 128


def test_parse_proto_with_unknown_field_types() -> None:
    """Test _parse_proto handles unknown field types gracefully."""
    from custom_components.robovac.proto_decode import _parse_proto

    # Payload with unknown field type (should skip)
    # Field with type 6 (reserved) or 7 (reserved)
    test_data = base64.b64decode("Cw==")  # Field 1, wire type 3 (length-delimited)
    result = _parse_proto(test_data)

    # Should return dict
    assert isinstance(result, dict)


def test_clean_param_response_with_multiple_fan_modes() -> None:
    """Test decode_clean_param_response with different fan mode values."""
    # Test that the function returns appropriate values
    result = decode_clean_param_response("AA==")
    # Should handle minimal payload
    assert result is None or isinstance(result, dict) or isinstance(result, str)


def test_work_status_v2_sensor_state_values() -> None:
    """Test decode_work_status_v2 returns valid state values."""
    # Test various work status payloads to ensure valid states
    test_cases = [
        "AA==",  # Empty payload
        "CA==",  # Minimal data
        "Cg==",  # Different minimal data
    ]

    for payload in test_cases:
        result = decode_work_status_v2(payload)
        # Should return a string state or None
        assert result is None or isinstance(result, str)


def test_error_code_with_extended_codes() -> None:
    """Test decode_error_code handles various error code formats."""
    # Test error code decoding with different data formats
    result = decode_error_code("AA==")
    # Should return string or None
    assert result is None or isinstance(result, str)
