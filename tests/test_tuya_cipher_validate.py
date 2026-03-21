import pytest
from custom_components.robovac.tuyalocalapi import TuyaCipher, Message
import struct


def test_get_prefix_size_and_validate_v31():
    cipher = TuyaCipher("1234567890123456", (3, 1))

    # Valid prefix
    valid_data = b"3.1" + b"a" * 16 + b"payload"
    assert cipher.get_prefix_size_and_validate(0, valid_data) == 0  # Invalid hash will return 0

    # We just want to test coverage for line 263-274
    # To hit line 268 (return 19), we need a valid hash
    payload = b"testpayload"
    hash_value = cipher.hash(payload)
    valid_data_with_hash = b"3.1" + hash_value.encode("ascii") + payload
    assert cipher.get_prefix_size_and_validate(0, valid_data_with_hash) == 19


def test_get_prefix_size_and_validate_v33():
    cipher = TuyaCipher("1234567890123456", (3, 3))

    # Valid prefix, SET_COMMAND
    valid_data = b"3.3" + b"\x00" * 12 + b"payload"
    # sequence=1, _, _, _ -> struct unpack ">IIIH" requires 14 bytes
    header = struct.pack(">IIIH", 0, 1, 0, 0)
    valid_data = b"3.3" + header + b"payload"
    assert cipher.get_prefix_size_and_validate(Message.SET_COMMAND, valid_data) == 15
    assert cipher.get_prefix_size_and_validate(Message.GRATUITOUS_UPDATE, valid_data) == 15
    assert cipher.get_prefix_size_and_validate(Message.GET_COMMAND, valid_data) == 0


def test_get_prefix_size_and_validate_invalid():
    cipher = TuyaCipher("1234567890123456", (3, 3))
    assert cipher.get_prefix_size_and_validate(0, b"3.4") == 0
    assert cipher.get_prefix_size_and_validate(0, b"") == 0
    assert cipher.get_prefix_size_and_validate(0, b"random") == 0
