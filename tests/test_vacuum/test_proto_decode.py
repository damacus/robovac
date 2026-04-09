"""Unit tests for proto_decode module - protobuf decoder for T2277 DPS messages."""

import base64
import pytest

from custom_components.robovac.proto_decode import (
    _parse_varint,
    _parse_proto,
    decode_mode_ctrl,
    decode_work_status,
    decode_error_code,
)
from custom_components.robovac.errors import getT2277ErrorMessage


# ============================================================================
# Tests for _parse_varint
# ============================================================================


class TestParseVarint:
    """Tests for _parse_varint function."""

    def test_single_byte_varint_value_1(self):
        """Test parsing single-byte varint with value 1."""
        data = bytes([0x01])
        value, pos = _parse_varint(data, 0)
        assert value == 1
        assert pos == 1

    def test_single_byte_varint_value_127(self):
        """Test parsing single-byte varint with value 127 (max single byte)."""
        data = bytes([0x7F])
        value, pos = _parse_varint(data, 0)
        assert value == 127
        assert pos == 1

    def test_single_byte_varint_value_0(self):
        """Test parsing single-byte varint with value 0."""
        data = bytes([0x00])
        value, pos = _parse_varint(data, 0)
        assert value == 0
        assert pos == 1

    def test_multibyte_varint_value_300(self):
        """Test parsing multi-byte varint with value 300."""
        # 300 = 0xAC, 0x02 in varint encoding
        data = bytes([0xAC, 0x02])
        value, pos = _parse_varint(data, 0)
        assert value == 300
        assert pos == 2

    def test_multibyte_varint_value_2101(self):
        """Test parsing multi-byte varint with value 2101."""
        # 2101 in binary is 0x835 = varint [0xB5, 0x10]
        data = bytes([0xB5, 0x10])
        value, pos = _parse_varint(data, 0)
        assert value == 2101
        assert pos == 2

    def test_varint_at_nonzero_position(self):
        """Test parsing varint starting at non-zero position."""
        data = bytes([0xFF, 0xFF, 0x05])  # junk + varint for 5
        value, pos = _parse_varint(data, 2)
        assert value == 5
        assert pos == 3

    def test_varint_three_byte_value(self):
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

    def test_empty_bytes(self):
        """Test parsing empty protobuf data."""
        data = bytes([])
        fields = _parse_proto(data)
        assert fields == {}

    def test_single_varint_field(self):
        """Test parsing single varint field (field_1 = 5)."""
        # Tag for field_1 varint = (1 << 3) | 0 = 0x08
        # Value = 5
        data = bytes([0x08, 0x05])
        fields = _parse_proto(data)
        assert fields == {1: 5}

    def test_single_varint_field_value_300(self):
        """Test parsing varint field with value 300."""
        # Tag for field_1 = 0x08, value 300 = [0xAC, 0x02]
        data = bytes([0x08, 0xAC, 0x02])
        fields = _parse_proto(data)
        assert fields == {1: 300}

    def test_single_length_delimited_field(self):
        """Test parsing single length-delimited field (field_2 = some bytes)."""
        # Tag for field_2 length-delimited = (2 << 3) | 2 = 0x12
        # Length = 3, value = b'hello'[0:3] = b'hel'
        data = bytes([0x12, 0x03]) + b'hel'
        fields = _parse_proto(data)
        assert fields == {2: b'hel'}

    def test_repeated_varint_field_becomes_list(self):
        """Test parsing repeated varint field creates a list."""
        # field_3 = 5, field_3 = 10
        # Tag for field_3 = (3 << 3) | 0 = 0x18
        data = bytes([0x18, 0x05, 0x18, 0x0A])
        fields = _parse_proto(data)
        assert fields == {3: [5, 10]}

    def test_repeated_varint_field_three_values(self):
        """Test repeated varint field with three values."""
        data = bytes([0x18, 0x05, 0x18, 0x0A, 0x18, 0x0F])
        fields = _parse_proto(data)
        assert fields == {3: [5, 10, 15]}

    def test_mixed_fields_varint_and_length_delimited(self):
        """Test parsing mixed field types."""
        # field_1 = 5 (varint)
        # field_2 = b'hi' (length-delimited)
        # field_3 = 10 (varint)
        data = bytes([0x08, 0x05, 0x12, 0x02]) + b'hi' + bytes([0x18, 0x0A])
        fields = _parse_proto(data)
        assert fields == {1: 5, 2: b'hi', 3: 10}

    def test_field_numbers_with_higher_values(self):
        """Test parsing fields with higher field numbers."""
        # field_10 = 42
        # Tag = (10 << 3) | 0 = 0x50
        data = bytes([0x50, 0x2A])
        fields = _parse_proto(data)
        assert fields == {10: 42}

    def test_skips_64bit_fields(self):
        """Test that 64-bit fields (wire_type 1) are skipped."""
        # field_1 = 5, field_2 (64-bit), field_3 = 10
        # Tag for field_2 64-bit = (2 << 3) | 1 = 0x11
        data = bytes([0x08, 0x05, 0x11]) + bytes([0] * 8) + bytes([0x18, 0x0A])
        fields = _parse_proto(data)
        # 64-bit field is skipped, but varint fields are parsed
        assert 1 in fields and 3 in fields
        assert fields[1] == 5
        assert fields[3] == 10

    def test_skips_32bit_fields(self):
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
            ("AA==", "standby"),            # empty payload (no method, no param)
            ("AggN", "pause"),              # method=PAUSE_TASK (13)
            ("AggG", "stop"),               # method=START_GOHOME (6)
            ("BBoCCAE=", "auto"),           # param.auto_clean present (method=0 or absent)
            ("AggO", "nosweep"),            # method=RESUME_TASK (14)
            ("BAgNEGg=", "pause"),          # method=PAUSE_TASK (13) with seq=104
            ("BAgOEGg=", "nosweep"),        # method=RESUME_TASK (14) with seq=104
            ("BAgOEGw=", "nosweep"),        # method=RESUME_TASK (14) with seq=108
        ],
    )
    def test_mode_ctrl_payloads(self, raw_b64, expected):
        """Test decoding MODE control payloads from T2277."""
        result = decode_mode_ctrl(raw_b64)
        assert result == expected

    def test_mode_ctrl_seq_only_no_param(self):
        """Test that seq without method or param defaults to standby."""
        # AhBw decodes to field_2=112 (seq), no method or param
        result = decode_mode_ctrl("AhBw")
        # With no method and no param, should return standby
        assert result == "standby"


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
            ("BgoAEAUyAA==", "auto"),       # state=CLEANING(5), mode=AUTO, no relocating
            ("CAoAEAUyAggB", "Paused"),     # state=CLEANING(5), cleaning.run_state=PAUSED
            ("CAoCCAEQBTIA", "room"),       # state=CLEANING(5), mode=SELECT_ROOM(1)
            ("CgoCCAEQBTICCAE=", "room_pause"),  # state=CLEANING(5), mode=SELECT_ROOM, paused
            ("CAoCCAIQBTIA", "spot"),       # state=CLEANING(5), mode=SELECT_ZONE(2)
            ("CgoCCAIQBTICCAE=", "spot_pause"),  # state=CLEANING(5), mode=SELECT_ZONE, paused
            ("BAoAEAY=", "start_manual"),   # state=REMOTE_CTRL(6)
            ("BBAHQgA=", "going_to_charge"),  # state=GO_HOME(7), no breakpoint
            ("BBADGgA=", "Charging"),       # state=CHARGING(3), charging.state != DONE
            ("BhADGgIIAQ==", "completed"),  # state=CHARGING(3), charging.state=DONE
        ],
    )
    def test_work_status_payloads(self, raw_b64, expected):
        """Test decoding WORK_STATUS payloads from T2277."""
        result = decode_work_status(raw_b64)
        assert result == expected

    def test_work_status_empty_standby(self):
        """Test that empty payload with no state field defaults to Standby-like behavior."""
        # AA== has no fields, so state is None
        # The code returns state_None for this case
        result = decode_work_status("AA==")
        # When state is None, code returns f"state_{state}" which is "state_None"
        assert result == "state_None"

    def test_work_status_positioning_with_empty_relocating(self):
        """Test positioning payloads that have relocating field."""
        # BgoAEAVSAA== has state=CLEANING(5) and field_10 (relocating) with empty bytes
        # Empty bytes are falsy, so relocating_fields = {}
        # This causes it to fall through to active cleaning logic
        result = decode_work_status("BgoAEAVSAA==")
        assert result == "auto"  # Falls through to active cleaning

    def test_work_status_room_positioning_with_empty_relocating(self):
        """Test room positioning payloads that have relocating field."""
        result = decode_work_status("CAoCCAEQBVIA")
        # Has state=CLEANING(5), mode=SELECT_ROOM(1), empty relocating
        assert result == "room"

    def test_work_status_spot_positioning_with_empty_relocating(self):
        """Test spot positioning payloads that have relocating field."""
        result = decode_work_status("CAoCCAIQBVIA")
        # Has state=CLEANING(5), mode=SELECT_ZONE(2), empty relocating
        assert result == "spot"

    def test_work_status_going_to_recharge(self):
        """Test going_to_recharge with breakpoint field."""
        result = decode_work_status("CAoAEAdCAFoA")
        # Has state=GO_HOME(7) and breakpoint field (field_11) with empty bytes
        # Empty bytes are falsy, so the breakpoint check fails and returns going_to_charge
        assert result == "going_to_charge"

    def test_work_status_recharging(self):
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

    def test_empty_error_payload(self):
        """Test that empty/no-error payload returns 'no_error'."""
        # "AA==" is the empty payload (length prefix only)
        result = decode_error_code("AA==")
        assert result == "no_error"

    def test_single_error_code_2101(self):
        """Test payload with single error code 2101 (Front bumper stuck)."""
        # Build proto bytes with field_3 (warn) = 2101
        # 2101 varint = [0xB5, 0x10]
        # Tag for field_3 = (3 << 3) | 0 = 0x18
        # Proto bytes = [0x18, 0xB5, 0x10]
        proto_bytes = bytes([0x18, 0xB5, 0x10])
        # Add length prefix
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        assert result == "Front bumper stuck"

    def test_single_error_code_2102(self):
        """Test payload with single error code 2102 (Left wheel stuck)."""
        # 2102 varint = [0xB6, 0x10]
        proto_bytes = bytes([0x18, 0xB6, 0x10])
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        assert result == "Left wheel stuck"

    def test_multiple_error_codes_sorted(self):
        """Test payload with multiple error codes (should be sorted)."""
        # field_3 (warn) with values 2102 and 2103
        # 2102 varint = [0xB6, 0x10], 2103 = [0xB7, 0x10]
        # Tag for field_3 = 0x18
        proto_bytes = bytes([0x18, 0xB6, 0x10, 0x18, 0xB7, 0x10])
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        # Should be sorted by code value, comma-separated
        assert result == "Left wheel stuck, Right wheel stuck"

    def test_error_code_with_new_code_message(self):
        """Test payload with error codes in new_code message (field_10)."""
        # field_10 is a message containing field_1 (error codes)
        # Create new_code message: field_1 = 2104 (Both wheels stuck)
        # 2104 varint = [0xB8, 0x10]
        inner_proto = bytes([0x08, 0xB8, 0x10])  # field_1 = 2104
        # Tag for field_10 = (10 << 3) | 2 = 0x52
        proto_bytes = bytes([0x52, len(inner_proto)]) + inner_proto
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        assert result == "Both wheels stuck"

    def test_error_code_from_both_warn_and_new_code(self):
        """Test payload with codes from both field_3 (warn) and new_code."""
        # field_3 (warn) = 2102, field_10 (new_code.field_1) = 2104
        warn_bytes = bytes([0x18, 0xB6, 0x10])  # field_3 = 2102 (Left wheel)

        inner_proto = bytes([0x08, 0xB8, 0x10])  # new_code.field_1 = 2104 (Both wheels)
        new_code_bytes = bytes([0x52, len(inner_proto)]) + inner_proto

        proto_bytes = warn_bytes + new_code_bytes
        with_length = bytes([len(proto_bytes)]) + proto_bytes
        raw_b64 = base64.b64encode(with_length).decode()

        result = decode_error_code(raw_b64)
        # Should contain both codes, sorted
        assert "Left wheel stuck" in result
        assert "Both wheels stuck" in result
        assert result.startswith("Left wheel stuck")  # sorted by code

    def test_error_code_unknown_code(self):
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

    def test_error_code_field_3_repeated(self):
        """Test field_3 with multiple repeated values."""
        # field_3 repeated with values 2102 and 2103
        # 2102 = [0xB6, 0x10], 2103 = [0xB7, 0x10]
        proto_bytes = bytes([0x18, 0xB6, 0x10, 0x18, 0xB7, 0x10])
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
            (2101, "Front bumper stuck"),
            (2102, "Left wheel stuck"),
            (2103, "Right wheel stuck"),
            (2104, "Both wheels stuck"),
            (2601, "Battery low"),
            (7000, "Robot trapped"),
            (7001, "Return to dock failed"),
            (9999, "Unknown error 9999"),
        ],
    )
    def test_t2277_error_messages(self, code, expected):
        """Test error message lookup for known and unknown codes."""
        result = getT2277ErrorMessage(code)
        assert result == expected

    def test_all_defined_error_codes_have_messages(self):
        """Verify all T2277 error codes are defined."""
        from custom_components.robovac.proto_decode import T2277_ERROR_CODES

        test_codes = [
            2101,  # Front bumper stuck
            2102,  # Left wheel stuck
            2103,  # Right wheel stuck
            2104,  # Both wheels stuck
            2601,  # Battery low
            7000,  # Robot trapped
            7001,  # Return to dock failed
            8103,  # System error
        ]

        for code in test_codes:
            message = getT2277ErrorMessage(code)
            assert not message.startswith("Unknown")
            assert code in T2277_ERROR_CODES
            assert T2277_ERROR_CODES[code] == message
