"""Tests for Protocol 3.5 message format and parsing."""

import struct
import pytest
from unittest.mock import MagicMock, patch

from custom_components.robovac.tuyalocalapi import (
    Message,
    TuyaCipher,
    TuyaDevice,
    MAGIC_PREFIX,
    MAGIC_SUFFIX,
)


# Protocol 3.5 magic constants
MAGIC_PREFIX_35 = 0x00006699
MAGIC_SUFFIX_35 = 0x00009966


class TestProtocol35MessageConstants:
    """Test Protocol 3.5 message constants are defined."""

    def test_magic_prefix_35_constant_exists(self) -> None:
        """Protocol 3.5 should have a distinct magic prefix constant."""
        from custom_components.robovac import tuyalocalapi
        assert hasattr(tuyalocalapi, 'MAGIC_PREFIX_35')
        assert tuyalocalapi.MAGIC_PREFIX_35 == 0x00006699

    def test_magic_suffix_35_constant_exists(self) -> None:
        """Protocol 3.5 should have a distinct magic suffix constant."""
        from custom_components.robovac import tuyalocalapi
        assert hasattr(tuyalocalapi, 'MAGIC_SUFFIX_35')
        assert tuyalocalapi.MAGIC_SUFFIX_35 == 0x00009966

    def test_message_prefix_format_35_exists(self) -> None:
        """Protocol 3.5 should have a message prefix format constant."""
        from custom_components.robovac import tuyalocalapi
        assert hasattr(tuyalocalapi, 'MESSAGE_PREFIX_FORMAT_35')


class TestProtocol35MessageFormat:
    """Test Protocol 3.5 message format structure."""

    @pytest.fixture
    def cipher_v35(self) -> TuyaCipher:
        """Create a Protocol 3.5 cipher instance."""
        return TuyaCipher("abcdefghijklmnop", (3, 5))

    def test_v35_message_uses_6699_prefix(self, cipher_v35: TuyaCipher) -> None:
        """Protocol 3.5 messages should use 0x00006699 prefix."""
        # Create a mock device with v3.5
        mock_device = MagicMock()
        mock_device.version = (3, 5)
        mock_device.cipher = cipher_v35

        message = Message(
            command=Message.GET_COMMAND,
            payload=b'{"test": true}',
            encrypt=True,
            device=mock_device,
        )

        msg_bytes = message.to_bytes()
        prefix = struct.unpack(">I", msg_bytes[:4])[0]
        assert prefix == MAGIC_PREFIX_35

    def test_v35_message_uses_9966_suffix(self, cipher_v35: TuyaCipher) -> None:
        """Protocol 3.5 messages should use 0x00009966 suffix."""
        mock_device = MagicMock()
        mock_device.version = (3, 5)
        mock_device.cipher = cipher_v35

        message = Message(
            command=Message.GET_COMMAND,
            payload=b'{"test": true}',
            encrypt=True,
            device=mock_device,
        )

        msg_bytes = message.to_bytes()
        suffix = struct.unpack(">I", msg_bytes[-4:])[0]
        assert suffix == MAGIC_SUFFIX_35

    def test_v35_message_contains_12_byte_iv(self, cipher_v35: TuyaCipher) -> None:
        """Protocol 3.5 messages should contain a 12-byte IV after header."""
        mock_device = MagicMock()
        mock_device.version = (3, 5)
        mock_device.cipher = cipher_v35

        message = Message(
            command=Message.GET_COMMAND,
            payload=b'{"test": true}',
            encrypt=True,
            device=mock_device,
        )

        msg_bytes = message.to_bytes()
        # Header is: prefix(4) + version(1) + reserved(1) + seq(4) + cmd(4) + len(4) = 18 bytes
        # IV should be next 12 bytes
        header_size = 18
        iv = msg_bytes[header_size:header_size + 12]
        assert len(iv) == 12

    def test_v35_message_contains_16_byte_tag(self, cipher_v35: TuyaCipher) -> None:
        """Protocol 3.5 messages should contain a 16-byte GCM tag before suffix."""
        mock_device = MagicMock()
        mock_device.version = (3, 5)
        mock_device.cipher = cipher_v35

        message = Message(
            command=Message.GET_COMMAND,
            payload=b'{"test": true}',
            encrypt=True,
            device=mock_device,
        )

        msg_bytes = message.to_bytes()
        # Tag is 16 bytes before the 4-byte suffix
        tag = msg_bytes[-20:-4]
        assert len(tag) == 16

    def test_v34_message_still_uses_55aa_prefix(self) -> None:
        """Protocol 3.4 messages should still use 0x000055AA prefix."""
        cipher_v34 = TuyaCipher("abcdefghijklmnop", (3, 4))
        mock_device = MagicMock()
        mock_device.version = (3, 4)
        mock_device.cipher = cipher_v34

        message = Message(
            command=Message.GET_COMMAND,
            payload=b'{"test": true}',
            encrypt=True,
            device=mock_device,
        )

        msg_bytes = message.to_bytes()
        prefix = struct.unpack(">I", msg_bytes[:4])[0]
        assert prefix == MAGIC_PREFIX  # 0x000055AA


class TestProtocol35MessageParsing:
    """Test Protocol 3.5 message parsing from bytes."""

    @pytest.fixture
    def cipher_v35(self) -> TuyaCipher:
        """Create a Protocol 3.5 cipher instance."""
        return TuyaCipher("abcdefghijklmnop", (3, 5))

    def test_v35_from_bytes_detects_6699_prefix(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Message.from_bytes should detect Protocol 3.5 by 0x6699 prefix."""
        mock_device = MagicMock()
        mock_device.version = (3, 5)
        mock_device.cipher = cipher_v35
        mock_device._LOGGER = MagicMock()

        # Create a valid v3.5 message
        message = Message(
            command=Message.GET_COMMAND,
            payload=b'{"dps":{"1":true}}',
            encrypt=True,
            device=mock_device,
        )
        msg_bytes = message.to_bytes()

        # Parse it back
        parsed = Message.from_bytes(mock_device, msg_bytes, cipher_v35)
        assert parsed.command == Message.GET_COMMAND

    def test_v35_from_bytes_decrypts_payload(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Message.from_bytes should correctly decrypt Protocol 3.5 payload."""
        mock_device = MagicMock()
        mock_device.version = (3, 5)
        mock_device.cipher = cipher_v35
        mock_device._LOGGER = MagicMock()

        original_payload = {"dps": {"1": True, "2": "test"}}

        message = Message(
            command=Message.GET_COMMAND,
            payload=original_payload,
            encrypt=True,
            device=mock_device,
        )
        msg_bytes = message.to_bytes()

        parsed = Message.from_bytes(mock_device, msg_bytes, cipher_v35)
        assert parsed.payload == original_payload

    def test_v35_from_bytes_validates_gcm_tag(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Message.from_bytes should fail if GCM tag is invalid."""
        mock_device = MagicMock()
        mock_device.version = (3, 5)
        mock_device.cipher = cipher_v35
        mock_device._LOGGER = MagicMock()

        message = Message(
            command=Message.GET_COMMAND,
            payload=b'{"dps":{"1":true}}',
            encrypt=True,
            device=mock_device,
        )
        msg_bytes = bytearray(message.to_bytes())

        # Corrupt the GCM tag (16 bytes before suffix)
        msg_bytes[-20] ^= 0xFF

        from custom_components.robovac.tuyalocalapi import InvalidMessage
        with pytest.raises(InvalidMessage):
            Message.from_bytes(mock_device, bytes(msg_bytes), cipher_v35)
