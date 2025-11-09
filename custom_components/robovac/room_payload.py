"""Helpers for decoding Tuya RoboVac binary room payloads."""

from __future__ import annotations

from typing import List, Sequence, Tuple


def decode_binary_room_list(payload: bytes) -> List[Tuple[int | str, str | None]]:
    """Decode a binary room list payload emitted by Tuya-based vacuums.

    The payload is a protobuf message (optionally prefixed with a size varint)
    where field ``1`` contains repeated room entries. Each room entry embeds
    further protobuf messages that include the room identifier and the human
    friendly label. Only the minimal structure required for extracting those
    values is implemented here so that we can operate without the generated
    protobuf classes.

    Args:
        payload: Raw bytes extracted from the room clean data point.

    Returns:
        A list of ``(identifier, label)`` tuples for every room discovered. The
        identifier is returned as either an ``int`` (when the payload stores the
        ID numerically) or as a ``str`` when the device provides textual IDs.
        Labels may be ``None`` if the payload omits the friendly name.
    """

    if not payload:
        return []

    message = _strip_length_prefix(payload)
    try:
        top_level = _parse_message(message)
    except ValueError:
        return []

    rooms: List[Tuple[int | str, str | None]] = []
    for room_payload in top_level.get(1, []):
        if not isinstance(room_payload, (bytes, bytearray, memoryview)):
            continue
        try:
            room_fields = _parse_message(bytes(room_payload))
        except ValueError:
            continue

        identifier = _extract_identifier(room_fields)
        if identifier is None:
            continue

        label = _extract_label(room_fields)
        rooms.append((identifier, label))

    return rooms


def _strip_length_prefix(payload: bytes) -> bytes:
    """Remove a leading length prefix when present."""

    try:
        length, offset = _read_varint(payload, 0)
    except ValueError:
        return payload

    if length == len(payload) - offset:
        return payload[offset:]

    return payload


def _parse_message(message: bytes) -> dict[int, List[int | bytes]]:
    """Parse a protobuf message into a field dictionary.

    Only wire types used by the RoboVac payloads are supported (varint, length
    delimited, fixed32 and fixed64). Values are collected in lists to account for
    repeated fields.
    """

    offset = 0
    result: dict[int, List[int | bytes]] = {}
    length = len(message)

    while offset < length:
        tag, offset = _read_varint(message, offset)
        field_number = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 0:  # Varint
            value, offset = _read_varint(message, offset)
        elif wire_type == 1:  # 64-bit
            if offset + 8 > length:
                raise ValueError("unexpected end of data while reading fixed64")
            value = int.from_bytes(message[offset : offset + 8], "little", signed=False)
            offset += 8
        elif wire_type == 2:  # Length-delimited
            size, offset = _read_varint(message, offset)
            if offset + size > length:
                raise ValueError("unexpected end of data while reading bytes field")
            value = message[offset : offset + size]
            offset += size
        elif wire_type == 5:  # 32-bit
            if offset + 4 > length:
                raise ValueError("unexpected end of data while reading fixed32")
            value = int.from_bytes(message[offset : offset + 4], "little", signed=False)
            offset += 4
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")

        result.setdefault(field_number, []).append(value)

    return result


def _read_varint(buffer: Sequence[int], offset: int) -> tuple[int, int]:
    """Read a protobuf varint from *buffer* starting at *offset*."""

    result = 0
    shift = 0
    length = len(buffer)

    while offset < length:
        byte = buffer[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, offset
        shift += 7
        if shift >= 64:
            break

    raise ValueError("invalid varint encoding")


def _extract_identifier(room_fields: dict[int, List[int | bytes]]) -> int | str | None:
    """Extract the primary room identifier from the parsed fields."""

    for field_number in (1, 4, 5, 2, 3):
        for value in room_fields.get(field_number, []):
            identifier = _decode_identifier_value(value)
            if identifier is not None:
                return identifier

    return None


def _decode_identifier_value(value: int | bytes | bytearray | memoryview) -> int | str | None:
    if isinstance(value, int):
        return value

    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        try:
            nested = _parse_message(raw)
        except ValueError:
            nested = {}

        nested_values = list(nested.get(1, [])) if nested else []
        if nested_values:
            for nested_value in nested_values:
                if isinstance(nested_value, int):
                    return nested_value
                text = _decode_text(nested_value)
                if text:
                    return text

        text = _decode_text(raw)
        if text:
            return text

    return None


def _extract_label(room_fields: dict[int, List[int | bytes]]) -> str | None:
    """Extract the friendly room name from the parsed fields."""

    for field_number in (6, 7, 8):
        for value in room_fields.get(field_number, []):
            label = _decode_label_value(value)
            if label:
                return label

    return None


def _decode_label_value(value: int | bytes | bytearray | memoryview) -> str | None:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        try:
            nested = _parse_message(raw)
        except ValueError:
            nested = {}

        if nested:
            for field_number in (2, 1, 3):
                for nested_value in nested.get(field_number, []):
                    text = _decode_text(nested_value)
                    if text:
                        return text

        return _decode_text(raw)

    return None


def _decode_text(value: int | bytes | bytearray | memoryview) -> str | None:
    if isinstance(value, int):
        return None

    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        if not raw:
            return None

        for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
            try:
                decoded = raw.decode(encoding)
            except UnicodeDecodeError:
                continue
            cleaned = decoded.strip("\x00").strip()
            if cleaned:
                return cleaned

    return None
