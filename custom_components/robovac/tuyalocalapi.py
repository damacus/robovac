# -*- coding: utf-8 -*-

# Copyright 2019 Richard Mitchell
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Based on portions of https://github.com/codetheweb/tuyapi/
#
# MIT License
#
# Copyright (c) 2017 Max Isom
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import asyncio
import base64
import json
import logging
import socket
import struct
import time
import traceback
import zlib
from typing import Any, Awaitable, Callable, Coroutine, Optional, Union
from asyncio import Semaphore, StreamWriter
from .vacuums.base import RobovacCommand

from cryptography.hazmat.backends.openssl import backend as openssl_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
from cryptography.hazmat.primitives.hashes import Hash, MD5, SHA256
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives import hmac as crypto_hmac

INITIAL_BACKOFF = 5
INITIAL_QUEUE_TIME = 0.1
BACKOFF_MULTIPLIER = 1.70224
_LOGGER = logging.getLogger(__name__)
MESSAGE_PREFIX_FORMAT = ">IIII"
MESSAGE_SUFFIX_FORMAT = ">II"
MESSAGE_SUFFIX_FORMAT_34 = ">32sI"  # 32-byte HMAC + 4-byte suffix for v3.4
MAGIC_PREFIX = 0x000055AA
MAGIC_SUFFIX = 0x0000AA55
MAGIC_SUFFIX_BYTES = struct.pack(">I", MAGIC_SUFFIX)

# Protocol 3.5 constants
MAGIC_PREFIX_35 = 0x00006699
MAGIC_SUFFIX_35 = 0x00009966
MAGIC_SUFFIX_35_BYTES = struct.pack(">I", MAGIC_SUFFIX_35)
# Format: prefix(4) + version(1) + reserved(1) + seq(4) + cmd(4) + len(4) = 18 bytes
MESSAGE_PREFIX_FORMAT_35 = ">IBBIII"
MESSAGE_SUFFIX_FORMAT_35 = ">16sI"  # 16-byte GCM tag + 4-byte suffix
# v3.4+/v3.5 prepend a version header to the plaintext before encryption,
# except for commands in NO_PROTOCOL_HEADER_CMDS.
PROTOCOL_35_VERSION_HEADER = b"3.5" + b"\x00" * 12  # 15 bytes


class TuyaException(Exception):
    """Base for Tuya exceptions."""


class InvalidKey(TuyaException):
    """The local key is invalid."""


class InvalidMessage(TuyaException):
    """The message received is invalid."""


class MessageDecodeFailed(TuyaException):
    """The message received cannot be decoded as JSON."""


class ConnectionException(TuyaException):
    """The socket connection failed."""


class ConnectionTimeoutException(ConnectionException):
    """The socket connection timed out."""


class ConnectionFailedException(ConnectionException):
    """The socket connection failed for a reason other than timeout."""


class RequestResponseCommandMismatch(TuyaException):
    """The command in the response didn't match the one from the request."""


class ResponseTimeoutException(TuyaException):
    """Did not recieve a response to the request within the timeout"""


class BackoffException(TuyaException):
    """Backoff time not reached"""


class TuyaCipher:
    """Tuya cryptographic helpers."""

    def __init__(self, key: str, version: tuple[int, int]):
        """Initialize the cipher."""
        self.version = version
        self.key = key
        self.key_bytes = key.encode("ascii")
        self.cipher = Cipher(
            algorithms.AES(self.key_bytes), modes.ECB(), backend=openssl_backend
        )
        # Initialize GCM cipher for Protocol 3.5
        self._aesgcm = AESGCM(self.key_bytes)
        # Store the real (local) key for session key negotiation
        self.real_key_bytes = self.key_bytes
        # ⚡ Bolt optimization: Pre-calculate the version string as bytes to avoid decoding every packet
        self._version_bytes = ".".join(map(str, self.version)).encode("utf8")

    def set_session_key(self, session_key: bytes) -> None:
        """Switch cipher to use a negotiated session key.

        After Protocol 3.5 session key negotiation, all subsequent
        messages must be encrypted with the derived session key.
        """
        self.key_bytes = session_key
        self.cipher = Cipher(
            algorithms.AES(self.key_bytes), modes.ECB(), backend=openssl_backend
        )
        self._aesgcm = AESGCM(self.key_bytes)

    @property
    def is_gcm_mode(self) -> bool:
        """Check if this cipher uses GCM mode (Protocol 3.5+).

        Returns:
            True if Protocol 3.5 or higher (uses GCM), False otherwise (uses ECB).
        """
        return self.version >= (3, 5)

    def generate_iv(self) -> bytes:
        """Generate a random 12-byte IV/nonce for GCM mode.

        Returns:
            A 12-byte random IV suitable for AES-GCM.
        """
        return os.urandom(12)

    def encrypt_gcm(
        self, plaintext: bytes, aad: bytes | None = None
    ) -> tuple[bytes, bytes, bytes]:
        """Encrypt data using AES-GCM for Protocol 3.5.

        Args:
            plaintext: The data to encrypt.
            aad: Optional additional authenticated data (signed but not encrypted).

        Returns:
            A tuple of (iv, ciphertext, tag) where:
            - iv: 12-byte initialization vector/nonce
            - ciphertext: The encrypted data (same length as plaintext)
            - tag: 16-byte GCM authentication tag
        """
        iv = self.generate_iv()
        # AESGCM.encrypt returns ciphertext + tag concatenated
        if aad is None:
            aad = b""
        ct_with_tag = self._aesgcm.encrypt(iv, plaintext, aad)
        # Split ciphertext and tag (tag is last 16 bytes)
        ciphertext = ct_with_tag[:-16]
        tag = ct_with_tag[-16:]
        return (iv, ciphertext, tag)

    def decrypt_gcm(
        self,
        iv: bytes,
        ciphertext: bytes,
        tag: bytes,
        aad: bytes | None = None,
    ) -> bytes:
        """Decrypt data using AES-GCM for Protocol 3.5.

        Args:
            iv: 12-byte initialization vector/nonce.
            ciphertext: The encrypted data.
            tag: 16-byte GCM authentication tag.
            aad: Optional additional authenticated data.

        Returns:
            The decrypted plaintext.

        Raises:
            InvalidTag: If the GCM tag verification fails.
        """
        if aad is None:
            aad = b""
        # AESGCM.decrypt expects ciphertext + tag concatenated
        ct_with_tag = ciphertext + tag
        return self._aesgcm.decrypt(iv, ct_with_tag, aad)

    def hmac_sha256(self, data: bytes) -> bytes:
        """Calculate HMAC-SHA256 for protocol 3.4.

        Args:
            data: The data to calculate HMAC for.

        Returns:
            The 32-byte HMAC-SHA256 digest.
        """
        h = crypto_hmac.HMAC(self.key_bytes, SHA256(), backend=openssl_backend)
        h.update(data)
        return h.finalize()

    def verify_hmac(self, data: bytes, expected_hmac: bytes) -> bool:
        """Verify HMAC-SHA256 for protocol 3.4.

        Args:
            data: The data to verify.
            expected_hmac: The expected HMAC value.

        Returns:
            True if HMAC matches, False otherwise.
        """
        calculated = self.hmac_sha256(data)
        return calculated == expected_hmac

    def get_prefix_size_and_validate(self, command: int, encrypted_data: bytes) -> int:
        """Get the prefix size and validate the encrypted data.

        Args:
            command: The command to be encrypted.
            encrypted_data: The encrypted data.

        Returns:
            The prefix size.
        """
        if not encrypted_data.startswith(self._version_bytes):
            return 0

        if self.version < (3, 3):
            # 3.1 header length is 19 bytes: version (3 bytes) + MD5 hash (16 bytes)
            hash = encrypted_data[3:19].decode("ascii")
            expected_hash = self.hash(encrypted_data[19:])
            if hash != expected_hash:
                return 0
            return 19
        else:
            if command in (Message.SET_COMMAND, Message.GRATUITOUS_UPDATE):
                _, sequence, __, ___ = struct.unpack_from(">IIIH", encrypted_data, 3)
                return 15
        return 0

    def decrypt(self, command: int, data: bytes) -> bytes:
        """Decrypt the encrypted data.

        Args:
            command: The command to be encrypted.
            data: The encrypted data.

        Returns:
            The decrypted data.
        """
        # For protocol 3.3+, check if data starts with version prefix
        prefix_size = self.get_prefix_size_and_validate(command, data)

        # If no valid prefix found, try to decrypt the raw data
        # This handles cases where device sends data without version prefix
        data_to_decrypt = data[prefix_size:]

        # Check if data might already be JSON (unencrypted)
        if data_to_decrypt and data_to_decrypt[0:1] == b'{':
            return data_to_decrypt

        # Check if data length is valid for AES (must be multiple of 16)
        if len(data_to_decrypt) % 16 != 0:
            # Data length not valid for AES - indicates corruption or protocol mismatch
            raise ValueError(
                f"Invalid encrypted data length for AES block cipher: "
                f"{len(data_to_decrypt)} bytes (must be multiple of 16)"
            )

        decryptor = self.cipher.decryptor()
        if self.version < (3, 3):
            data_to_decrypt = base64.b64decode(data_to_decrypt)

        decrypted_data = decryptor.update(data_to_decrypt)
        decrypted_data += decryptor.finalize()

        # Try to unpad - if it fails, the key might be wrong
        try:
            unpadder = PKCS7(128).unpadder()
            unpadded_data = unpadder.update(decrypted_data)
            unpadded_data += unpadder.finalize()
            return bytes(unpadded_data)
        except ValueError:
            # PKCS7 unpadding failed - likely wrong key or corrupted data
            # Return raw decrypted data and let caller handle the error
            return decrypted_data

    def encrypt(self, command: int, data: bytes) -> bytes:
        """Encrypt the data.

        Args:
            command: The command to be encrypted.
            data: The data to be encrypted.

        Returns:
            The encrypted data.
        """
        encrypted_data = b""
        if data:
            padder = PKCS7(128).padder()
            padded_data = padder.update(data)
            padded_data += padder.finalize()
            encryptor = self.cipher.encryptor()
            encrypted_data = encryptor.update(padded_data)
            encrypted_data += encryptor.finalize()

        prefix = ".".join(map(str, self.version)).encode("utf8")
        if self.version < (3, 3):
            payload = base64.b64encode(encrypted_data)
            hash_value = self.hash(payload)
            prefix += hash_value.encode("utf8")
        else:
            payload = encrypted_data
            if command in (Message.SET_COMMAND, Message.GRATUITOUS_UPDATE):
                prefix += b"\x00" * 12
            else:
                prefix = b""

        # Ensure we're always returning bytes
        return prefix + payload

    def hash(self, data: bytes) -> str:
        """Calculate the hash of the data.

        Args:
            data: The data to be hashed.

        Returns:
            The hash of the data.
        """
        digest = Hash(MD5(), backend=openssl_backend)
        to_hash = "data={}||lpv={}||{}".format(
            data.decode("ascii"), ".".join(map(str, self.version)), self.key
        )
        digest.update(to_hash.encode("utf8"))
        intermediate = digest.finalize().hex()
        # Explicitly cast to str to satisfy mypy
        return str(intermediate[8:24])


def crc(data: bytes) -> int:
    """Calculate the Tuya-flavored CRC of some data."""
    return zlib.crc32(data)


class Message:
    SESS_KEY_NEG_START = 0x03
    SESS_KEY_NEG_RESP = 0x04
    SESS_KEY_NEG_FINISH = 0x05
    PING_COMMAND = 0x09
    GET_COMMAND = 0x0A
    SET_COMMAND = 0x07
    GRATUITOUS_UPDATE = 0x08
    # v3.4+/v3.5 use new command codes for SET and GET
    SET_COMMAND_NEW = 0x0D  # CONTROL_NEW
    GET_COMMAND_NEW = 0x10  # DP_QUERY_NEW
    UPDATEDPS = 0x12  # Request refresh of specific DPS

    # Commands that do NOT get the v3.4+/v3.5 version header prepended
    # (matches TinyTuya's NO_PROTOCOL_HEADER_CMDS + 0x07/0x08).
    # 0x07 (SET_COMMAND) is included because some v3.5 devices (e.g. T2276)
    # accept v3.3-style SET commands over v3.5 framing without the header.
    NO_PROTOCOL_HEADER_CMDS = {0x07, 0x08, 0x0A, 0x10, 0x12, 0x09, 0x03, 0x04, 0x05, 0x40}

    def __init__(
        self,
        command: int,
        payload: bytes | None = None,
        sequence: int | None = None,
        encrypt: bool = False,
        device: 'TuyaDevice | None' = None,
        expect_response: bool = True,
        ttl: int = 5,
    ):
        if payload is None:
            payload = b""
        self.payload = payload
        self.command = command
        self.original_sequence = sequence
        if sequence is None:
            self.set_sequence()
        else:
            self.sequence = sequence
        self.encrypt = encrypt
        self.device = device
        self.expiry = int(time.time()) + ttl
        self.expect_response = expect_response
        self.listener = None
        if expect_response is True:
            self.listener = asyncio.Semaphore(0)
            if device is not None:
                device._listeners[self.sequence] = self.listener

    def __repr__(self) -> str:
        """Return a string representation of the message.

        Returns:
            A string representation of the message.
        """
        return "{}({}, {!r}, {!r}, {})".format(
            self.__class__.__name__,
            hex(self.command),
            self.payload,
            self.sequence,
            "<Device {}>".format(self.device) if self.device else None,
        )

    def set_sequence(self) -> None:
        """Set the sequence number for the message.

        The sequence number is a unique identifier for the message.
        """
        self.sequence = int(time.perf_counter() * 1000) & 0xFFFFFFFF

    def hex(self) -> str:
        """Return the message in hex format.

        Returns:
            A string containing the message in hex format.
        """
        return self.to_bytes().hex()

    def to_bytes(self) -> bytes:
        """Return the message in bytes format.

        Returns:
            A bytes object containing the message.
        """
        payload_data = self.payload
        if payload_data is None:
            payload_data = b""
        if isinstance(payload_data, dict):
            payload_data = json.dumps(payload_data, separators=(",", ":"))
        if not isinstance(payload_data, bytes):
            payload_data = payload_data.encode("utf8")

        # Check protocol version
        is_v35 = self.device is not None and self.device.version >= (3, 5)
        is_v34 = self.device is not None and self.device.version >= (3, 4)

        if is_v35 and self.device is not None:
            # Protocol 3.5 uses AES-GCM encryption
            return self._to_bytes_v35(payload_data)

        if self.encrypt and self.device is not None:
            payload_data = self.device.cipher.encrypt(self.command, payload_data)

        # Determine suffix format based on protocol version
        if is_v34:
            suffix_format = MESSAGE_SUFFIX_FORMAT_34
        else:
            suffix_format = MESSAGE_SUFFIX_FORMAT

        payload_size = len(payload_data) + struct.calcsize(suffix_format)

        header = struct.pack(
            MESSAGE_PREFIX_FORMAT,
            MAGIC_PREFIX,
            self.sequence,
            self.command,
            payload_size,
        )

        if is_v34 and self.device is not None:
            # Protocol 3.4 uses HMAC-SHA256 (32 bytes)
            hmac_data = self.device.cipher.hmac_sha256(header + payload_data)
            footer = struct.pack(MESSAGE_SUFFIX_FORMAT_34, hmac_data, MAGIC_SUFFIX)
        elif self.device and self.device.version >= (3, 3):
            checksum = crc(header + payload_data)
            footer = struct.pack(MESSAGE_SUFFIX_FORMAT, checksum, MAGIC_SUFFIX)
        else:
            checksum = crc(payload_data)
            footer = struct.pack(MESSAGE_SUFFIX_FORMAT, checksum, MAGIC_SUFFIX)
        return header + payload_data + footer

    def _to_bytes_v35(self, payload_data: bytes) -> bytes:
        """Return the message in Protocol 3.5 format.

        Protocol 3.5 format:
        00006699 VV RR SSSSSSSS MMMMMMMM LLLLLLLL (IV*12) (encrypted_data) (TAG*16) 00009966

        Args:
            payload_data: The payload data to encrypt.

        Returns:
            A bytes object containing the Protocol 3.5 message.
        """
        if self.device is None:
            raise InvalidMessage("Cannot create v3.5 message without a device")

        cipher = self.device.cipher

        # v3.4+/v3.5: prepend version header for commands that need it
        if self.command not in Message.NO_PROTOCOL_HEADER_CMDS:
            payload_data = PROTOCOL_35_VERSION_HEADER + payload_data

        # Calculate payload size first (needed for header/AAD)
        # We need a preliminary encrypt to get ciphertext length, but since
        # GCM doesn't pad, ciphertext length == plaintext length
        payload_size = 12 + len(payload_data) + 16

        # Build header: prefix(4) + version(1) + reserved(1) + seq(4) + cmd(4) + len(4)
        header = struct.pack(
            MESSAGE_PREFIX_FORMAT_35,
            MAGIC_PREFIX_35,
            0x00,  # version field
            0x00,  # reserved field
            self.sequence,
            self.command,
            payload_size,
        )

        # AAD = header bytes after prefix: version(1)+reserved(1)+seq(4)+cmd(4)+len(4) = 14 bytes
        aad = header[4:]

        # Encrypt payload with GCM using header as AAD
        iv, ciphertext, tag = cipher.encrypt_gcm(payload_data, aad=aad)

        # Build footer: tag(16) + suffix(4)
        footer = struct.pack(MESSAGE_SUFFIX_FORMAT_35, tag, MAGIC_SUFFIX_35)

        return header + iv + ciphertext + footer

    def __bytes__(self) -> bytes:
        """Convert the message to bytes.

        Returns:
            The message as bytes.
        """
        return self.to_bytes()

    async def async_send(self) -> None:
        """Send the message asynchronously.

        Raises:
            InvalidMessage: If the message is invalid.
        """
        if self.device is not None:
            await self.device._async_send(self)
        else:
            raise InvalidMessage("Cannot send message without a device")

    @classmethod
    def from_bytes(
        cls,
        device: "TuyaDevice",
        data: bytes,
        cipher: Optional[TuyaCipher] = None
    ) -> "Message":
        """Create a message from bytes.

        This method creates a message from bytes received from the device.

        Args:
            device: The device the message is from.
            data: The bytes received from the device.
            cipher: The cipher to use for decryption.

        Returns:
            A Message object created from the bytes.
        """
        # Check for Protocol 3.5 prefix first
        prefix_check = struct.unpack_from(">I", data)[0]
        if prefix_check == MAGIC_PREFIX_35:
            return cls._from_bytes_v35(device, data, cipher)

        try:
            prefix, sequence, command, payload_size = struct.unpack_from(
                MESSAGE_PREFIX_FORMAT, data
            )
        except struct.error as e:
            raise InvalidMessage("Invalid message header format.") from e
        if prefix != MAGIC_PREFIX:
            raise InvalidMessage("Magic prefix missing from message.")

        # Determine protocol version from cipher
        is_v34 = cipher is not None and cipher.version >= (3, 4)

        # Calculate suffix size based on protocol version
        if is_v34:
            suffix_size = struct.calcsize(MESSAGE_SUFFIX_FORMAT_34)  # 32-byte HMAC + 4-byte suffix
        else:
            suffix_size = struct.calcsize(MESSAGE_SUFFIX_FORMAT)  # 4-byte CRC + 4-byte suffix

        # check for an optional return code
        header_size = struct.calcsize(MESSAGE_PREFIX_FORMAT)
        try:
            (return_code,) = struct.unpack_from(">I", data, header_size)
        except struct.error as e:
            raise InvalidMessage("Unable to unpack return code.") from e
        if return_code >> 8:
            payload_data = data[
                header_size:header_size
                + payload_size
                - suffix_size
            ]
            return_code = None
        else:
            payload_data = data[
                header_size
                + struct.calcsize(">I"):header_size
                + payload_size
                - suffix_size
            ]

        # Validate checksum based on protocol version
        if is_v34:
            # Protocol 3.4 uses HMAC-SHA256 (32 bytes)
            try:
                expected_hmac, suffix = struct.unpack_from(
                    MESSAGE_SUFFIX_FORMAT_34,
                    data,
                    header_size + payload_size - suffix_size,
                )
            except struct.error as e:
                raise InvalidMessage("Invalid message suffix format for v3.4.") from e
            if suffix != MAGIC_SUFFIX:
                raise InvalidMessage("Magic suffix missing from message")

            # Verify HMAC-SHA256 - cipher is required for v3.4
            if cipher is None:
                raise InvalidMessage("Missing cipher for v3.4 message; cannot verify HMAC")

            data_to_verify = data[: header_size + payload_size - suffix_size]
            if not cipher.verify_hmac(data_to_verify, expected_hmac):
                device._LOGGER.debug(f"HMAC verification failed. Expected: {expected_hmac.hex()}")
                raise InvalidMessage("HMAC check failed")
        else:
            # Protocol 3.3 and earlier use CRC32
            try:
                expected_crc, suffix = struct.unpack_from(
                    MESSAGE_SUFFIX_FORMAT,
                    data,
                    header_size + payload_size - suffix_size,
                )
            except struct.error as e:
                raise InvalidMessage("Invalid message suffix format.") from e
            if suffix != MAGIC_SUFFIX:
                raise InvalidMessage("Magic suffix missing from message")

            # Ensure data is not None before indexing
            if data is None:
                raise InvalidMessage("Data cannot be None")

            actual_crc = crc(
                data[: header_size + payload_size - suffix_size]
            )
            if expected_crc != actual_crc:
                raise InvalidMessage("CRC check failed")

        payload = None
        if payload_data:
            try:
                if cipher is not None:
                    payload_data = cipher.decrypt(command, payload_data)
            except ValueError:
                pass
            try:
                payload_text = payload_data.decode("utf8")
            except UnicodeDecodeError as e:
                device._LOGGER.debug(payload_data.hex())
                device._LOGGER.error(
                    "Decryption failed - the local key may be incorrect or has changed. "
                    "Try removing and re-adding the integration to refresh the key. "
                    "Error: %s", e
                )
                raise MessageDecodeFailed() from e
            try:
                payload = json.loads(payload_text)
            except json.decoder.JSONDecodeError as e:
                device._LOGGER.debug(payload_data.hex())
                device._LOGGER.error(
                    "Failed to parse decrypted data as JSON - the local key may be "
                    "incorrect. Try removing and re-adding the integration. Error: %s", e
                )
                raise MessageDecodeFailed() from e

        return cls(command, payload, sequence)

    @classmethod
    def _from_bytes_v35(
        cls,
        device: "TuyaDevice",
        data: bytes,
        cipher: Optional[TuyaCipher] = None
    ) -> "Message":
        """Create a message from Protocol 3.5 bytes.

        Protocol 3.5 format:
        00006699 VV RR SSSSSSSS MMMMMMMM LLLLLLLL (IV*12) (encrypted_data) (TAG*16) 00009966

        Args:
            device: The device the message is from.
            data: The bytes received from the device.
            cipher: The cipher to use for decryption.

        Returns:
            A Message object created from the bytes.
        """
        header_size = struct.calcsize(MESSAGE_PREFIX_FORMAT_35)  # 18 bytes

        try:
            prefix, version_byte, reserved, sequence, command, payload_size = (
                struct.unpack_from(MESSAGE_PREFIX_FORMAT_35, data)
            )
        except struct.error as e:
            raise InvalidMessage("Invalid v3.5 message header format.") from e

        if prefix != MAGIC_PREFIX_35:
            raise InvalidMessage("Magic prefix 0x6699 missing from v3.5 message.")

        # Extract IV (12 bytes after header)
        iv = data[header_size:header_size + 12]
        if len(iv) != 12:
            raise InvalidMessage("Invalid IV length in v3.5 message.")

        # Extract ciphertext (between IV and tag)
        # payload_size = IV(12) + ciphertext + tag(16)
        ciphertext_len = payload_size - 12 - 16
        ciphertext_start = header_size + 12
        ciphertext = data[ciphertext_start:ciphertext_start + ciphertext_len]

        # Extract tag (16 bytes before suffix)
        tag_start = ciphertext_start + ciphertext_len
        tag = data[tag_start:tag_start + 16]
        if len(tag) != 16:
            raise InvalidMessage("Invalid GCM tag length in v3.5 message.")

        # Verify suffix
        suffix_start = tag_start + 16
        try:
            (suffix,) = struct.unpack_from(">I", data, suffix_start)
        except struct.error as e:
            raise InvalidMessage("Invalid v3.5 message suffix format.") from e

        if suffix != MAGIC_SUFFIX_35:
            raise InvalidMessage("Magic suffix 0x9966 missing from v3.5 message.")

        # Decrypt payload using GCM with header AAD
        # AAD = header bytes after prefix: version(1)+reserved(1)+seq(4)+cmd(4)+len(4)
        aad = data[4:header_size]
        payload = None
        if cipher is not None and ciphertext:
            try:
                payload_data = cipher.decrypt_gcm(iv, ciphertext, tag, aad=aad)
                # v3.5 responses may have binary prefixes before the JSON:
                # - 4-byte retcode (e.g. \x00\x00\x00\x00)
                # - 4-byte retcode + 15-byte version header (gratuitous
                #   updates: retcode + "3.5" + 12 bytes + JSON)
                # Find the first '{' to locate where JSON starts.
                if payload_data and payload_data[0:1] != b'{':
                    json_start = payload_data.find(b'{')
                    if json_start > 0:
                        payload_data = payload_data[json_start:]
                try:
                    payload_text = payload_data.decode("utf8")
                    payload = json.loads(payload_text)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    # Binary payload (e.g. session key negotiation)
                    payload = payload_data
            except Exception as e:
                device._LOGGER.debug(f"v3.5 decryption failed: {e}")
                raise InvalidMessage("GCM decryption/verification failed") from e

        return cls(command, payload, sequence)


class TuyaDevice:
    """Represents a generic Tuya device."""

    def __init__(
        self,
        model_details: Any,
        device_id: str,
        host: str,
        timeout: float,
        ping_interval: float,
        update_entity_state: Callable[[], Awaitable[None]],
        local_key: Optional[str] = None,
        port: int = 6668,
        gateway_id: Optional[str] = None,
        version: tuple[int, int] = (3, 3),
    ) -> None:
        """Initialize the device."""
        self._LOGGER = _LOGGER.getChild(device_id)
        self.model_details = model_details
        self.device_id = device_id
        self.host = host
        self.port = port
        if not gateway_id:
            gateway_id = self.device_id
        self.gateway_id = gateway_id
        self.version = version
        self.timeout = timeout
        self.last_pong: float = 0.0
        self._last_connect_attempt: float = 0.0
        self.ping_interval = ping_interval
        self.update_entity_state_cb = update_entity_state

        if local_key is None:
            raise InvalidKey("Local key cannot be None")

        if len(local_key) != 16:
            raise InvalidKey("Local key should be a 16-character string")

        self.cipher = TuyaCipher(local_key, self.version)
        self.writer: Optional[StreamWriter] = None
        self._response_task: Optional[asyncio.Task[Any]] = None
        self._recieve_task: Optional[asyncio.Task[Any]] = None
        self._ping_task: Optional[asyncio.Task[Any]] = None
        self._handlers: dict[int, Callable[[Message], Coroutine]] = {
            Message.GRATUITOUS_UPDATE: self.async_gratuitous_update_state,
            Message.PING_COMMAND: self._async_pong_received,
            # v3.5 devices use their own sequence numbers, so GET/SET
            # responses won't match the original request's listener.
            # Handle them as gratuitous state updates instead.
            Message.GET_COMMAND: self.async_gratuitous_update_state,
            Message.SET_COMMAND: self.async_gratuitous_update_state,
            Message.GET_COMMAND_NEW: self.async_gratuitous_update_state,
            Message.SET_COMMAND_NEW: self.async_gratuitous_update_state,
            Message.UPDATEDPS: self.async_gratuitous_update_state,
        }
        self._dps: dict[str, Any] = {}
        self._seqno = 0  # Incrementing sequence number for v3.5
        self._connected = False
        self._enabled = True
        self._queue: list[Message] = []
        self._listeners: dict[int, Union[Message, Exception, Semaphore]] = {}
        self._backoff = False
        self._queue_interval = INITIAL_QUEUE_TIME
        self._failures = 0

        asyncio.create_task(self.process_queue())

    def __repr__(self) -> str:
        """Return a string representation of the device.

        Returns:
            A string representation of the device.
        """
        return "{}({!r}, {!r}, {!r}, {!r})".format(
            self.__class__.__name__,
            self.device_id,
            self.host,
            self.port,
            self.cipher.key,
        )

    def __str__(self) -> str:
        """Return a string representation of the device.

        Returns:
            A string representation of the device.
        """
        return "{} ({}:{})".format(self.device_id, self.host, self.port)

    async def process_queue(self) -> None:
        """Process the queue of messages.

        This method processes the queue of messages and sends them to the device.
        """
        if self._enabled is False:
            return

        self.clean_queue()

        if len(self._queue) > 0:
            self._LOGGER.debug(
                "Processing queue. Current length: {}".format(len(self._queue))
            )
            try:
                message = self._queue.pop(0)
                await message.async_send()
                self._failures = 0
                self._queue_interval = INITIAL_QUEUE_TIME
                self._backoff = False
            except Exception as e:
                self._failures += 1
                self._LOGGER.debug(
                    "{} failures. Most recent: {}".format(self._failures, e)
                )
                if self._failures > 3:
                    self._backoff = True
                    self._queue_interval = min(
                        INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ** (self._failures - 4)),
                        30,
                    )
                    self._LOGGER.warn(
                        "{} failures, backing off for {} seconds".format(
                            self._failures, self._queue_interval
                        )
                    )

        await asyncio.sleep(self._queue_interval)
        # After sleeping through the backoff period, allow pings to be
        # queued again so the next cycle can attempt a reconnection.
        if self._backoff:
            self._backoff = False
        asyncio.create_task(self.process_queue())

    def clean_queue(self) -> None:
        """Clean the queue of messages.

        This method removes expired messages from the queue.
        """
        cleaned_queue = []
        now = int(time.time())
        for item in self._queue:
            if item.expiry > now:
                cleaned_queue.append(item)
        self._queue = cleaned_queue

    async def async_connect(self) -> None:
        """Connect to the device.

        This method establishes a connection to the device.
        For protocol 3.5+, enforces a minimum cooldown between connection
        attempts to give the device time to accept a new session.
        """
        if self._connected is True or self._enabled is False:
            return

        # Protocol 3.5 devices need a brief pause between connection
        # attempts.  Without this, multiple code paths (EOF handler, send
        # retry, process_queue) hammer the device with rapid reconnects and
        # every session key negotiation fails with "0 bytes read".
        # Keep this short (5s) — the device itself idles out at ~30s, so a
        # long cooldown means we reconnect to a stale connection every time.
        if self.version >= (3, 5):
            now = time.time()
            elapsed = now - self._last_connect_attempt
            if elapsed < 5:
                wait = 5 - elapsed
                self._LOGGER.debug(
                    "Reconnect cooldown: waiting %.1fs before connecting to %s",
                    wait, self
                )
                await asyncio.sleep(wait)
            self._last_connect_attempt = time.time()

        self._LOGGER.debug("Connecting to {}".format(self))
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
        except (asyncio.TimeoutError, OSError) as e:
            self._dps[self.model_details.commands[RobovacCommand.ERROR]] = ("CONNECTION_FAILED")
            raise ConnectionTimeoutException("Connection timed out: {}".format(e))
        self._connected = True

        # Protocol 3.5 requires session key negotiation before any communication
        if self.version >= (3, 5):
            try:
                await self._negotiate_session_key()
                # Reset failure count on successful handshake so that a subsequent
                # clean disconnect (EOF) doesn't compound with prior failures.
                self._failures = 0
                self._backoff = False
            except Exception as e:
                self._LOGGER.error("Session key negotiation failed: %s", e)
                await self.async_disconnect()
                raise ConnectionFailedException(
                    "Session key negotiation failed: {}".format(e)
                )

        if self._ping_task is None:
            # Delay first ping to let initial data exchange complete
            async def _start_ping() -> None:
                await asyncio.sleep(self.ping_interval)
                self._ping_task = asyncio.create_task(self.async_ping(self.ping_interval))
            self._ping_task = asyncio.create_task(_start_ping())

        asyncio.create_task(self._async_handle_message())

    async def _negotiate_session_key(self) -> None:
        """Negotiate a session key with a Protocol 3.5 device.

        Performs the 3-step handshake:
        1. Send SESS_KEY_NEG_START with 16-byte client nonce
        2. Receive SESS_KEY_NEG_RESP with 16-byte device nonce + HMAC
        3. Send SESS_KEY_NEG_FINISH with HMAC of device nonce
        4. Derive session key from both nonces
        """
        local_nonce = os.urandom(16)
        real_key = self.cipher.real_key_bytes
        # Session key negotiation MUST use the local key, not any previously
        # negotiated session key.  Reset the cipher so that both our
        # encryption (steps 1 & 3) and the response decryption (step 2,
        # via Message.from_bytes → cipher.decrypt_gcm) use the local key.
        self.cipher.key_bytes = real_key
        self.cipher._aesgcm = AESGCM(real_key)
        local_aesgcm = AESGCM(real_key)

        # Step 1: Build SESS_KEY_NEG_START directly (bypass Message class)
        if self.writer is None:
            raise ConnectionFailedException("Writer not initialized")

        seq = 1
        cmd = Message.SESS_KEY_NEG_START  # 0x03
        payload_size = 12 + len(local_nonce) + 16  # IV + ct + tag
        header = struct.pack(">IBBIII", MAGIC_PREFIX_35, 0, 0, seq, cmd, payload_size)
        aad = header[4:]  # 14 bytes

        iv = os.urandom(12)
        ct_with_tag = local_aesgcm.encrypt(iv, local_nonce, aad)
        ciphertext = ct_with_tag[:-16]
        tag = ct_with_tag[-16:]

        msg_bytes = header + iv + ciphertext + struct.pack(">16sI", tag, MAGIC_SUFFIX_35)

        self.writer.write(msg_bytes)
        await self.writer.drain()

        # Step 2: Read device response
        suffix = MAGIC_SUFFIX_35_BYTES
        try:
            raw = await asyncio.wait_for(
                self.reader.readuntil(suffix), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            raise
        except asyncio.IncompleteReadError:
            raise
        except Exception:
            raise

        resp = Message.from_bytes(self, raw, self.cipher)

        if resp.command != Message.SESS_KEY_NEG_RESP:
            raise InvalidMessage(
                "Expected SESS_KEY_NEG_RESP (0x04), got 0x{:02x}".format(resp.command)
            )

        payload = resp.payload
        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        # Device response is decrypted by _from_bytes_v35.
        # Strip 4-byte return code prefix if present (v3.5 responses include it).
        if len(payload) >= 52:
            payload = payload[4:]

        if len(payload) < 48:
            raise InvalidMessage(
                "SESS_KEY_NEG_RESP payload too short: {} bytes".format(len(payload))
            )

        remote_nonce = payload[:16]
        device_hmac = payload[16:48]

        # Verify device HMAC: device proves it has our local key by
        # computing HMAC-SHA256(local_key, client_nonce)
        h = crypto_hmac.HMAC(real_key, SHA256(), backend=openssl_backend)
        h.update(local_nonce)
        expected_hmac = h.finalize()

        if device_hmac != expected_hmac:
            raise InvalidMessage("Device HMAC verification failed")

        # Step 3: Build SESS_KEY_NEG_FINISH directly (seq=2 to match tinytuya)
        h2 = crypto_hmac.HMAC(real_key, SHA256(), backend=openssl_backend)
        h2.update(remote_nonce)
        client_hmac = h2.finalize()

        seq3 = 2
        cmd3 = Message.SESS_KEY_NEG_FINISH  # 0x05
        payload_size3 = 12 + len(client_hmac) + 16  # IV + ct + tag
        header3 = struct.pack(">IBBIII", MAGIC_PREFIX_35, 0, 0, seq3, cmd3, payload_size3)
        aad3 = header3[4:]
        iv3 = os.urandom(12)
        ct3_with_tag = local_aesgcm.encrypt(iv3, client_hmac, aad3)
        ciphertext3 = ct3_with_tag[:-16]
        tag3 = ct3_with_tag[-16:]
        msg3_bytes = header3 + iv3 + ciphertext3 + struct.pack(">16sI", tag3, MAGIC_SUFFIX_35)

        self.writer.write(msg3_bytes)
        await self.writer.drain()

        # Step 4: Derive session key (XOR nonces, then AES-GCM encrypt)
        xored = bytes(a ^ b for a, b in zip(local_nonce, remote_nonce))
        aesgcm = AESGCM(real_key)
        ct_with_tag = aesgcm.encrypt(local_nonce[:12], xored, None)
        session_key = ct_with_tag[:16]

        self.cipher.set_session_key(session_key)
        self._LOGGER.debug("Session key negotiated successfully for %s", self)
        await asyncio.sleep(0.1)

    async def async_disable(self) -> None:
        """Disable the device.

        This method disables the device.
        """
        self._enabled = False

        await self.async_disconnect()

    async def async_disconnect(self) -> None:
        """Disconnect from the device.

        This method disconnects from the device.
        """
        if self._connected is False:
            return

        self._LOGGER.debug("Disconnected from {}".format(self))
        self._connected = False
        self.last_pong = 0

        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()

        if self.reader is not None and not self.reader.at_eof():
            self.reader.feed_eof()

    def _dps_to_request(self) -> dict[str, None]:
        """Build a DPS map for device22-style status queries.

        Returns a dict with known DPS keys mapped to None.  If we already
        have cached state, use those keys; otherwise request common DPS
        codes for the device model.
        """
        if self._dps:
            return {k: None for k in self._dps}
        # Request common DPS codes that T2276 and similar vacuums use.
        # This is better than requesting DPS 1 which doesn't exist on
        # most vacuum models.
        return {str(k): None for k in [2, 5, 15, 101, 102, 103, 104, 106]}

    async def async_get(self) -> None:
        """Get the current state of the device.

        This method retrieves the current state of the device.
        """
        if self.version >= (3, 4):
            # v3.5 devices reject all known GET/query commands:
            # - DP_QUERY (0x0a) → "json obj data unvalid"
            # - DP_QUERY_NEW (0x10) → same
            # - UPDATEDPS (0x12) → empty ACK, no DPS data (tested with
            #   valid DPS IDs [2,5,15,101,102,103,104,106] — still empty)
            #
            # The only way to get DPS state is via gratuitous updates (0x08)
            # the device sends after SET commands.  So just stay connected.
            await self.async_connect()
            return
        payload_dict = {"gwId": self.gateway_id, "devId": self.device_id}
        payload_bytes = json.dumps(payload_dict).encode('utf-8')
        encrypt = False if self.version < (3, 3) else True
        message = Message(Message.GET_COMMAND, payload_bytes, encrypt=encrypt, device=self)
        self._queue.append(message)
        response = await self.async_receive(message)
        if response is not None:
            await self.async_update_state(response)

    async def async_set(self, dps: dict[str, Any]) -> None:
        """Set the state of the device.

        This method sets the state of the device.
        """
        t = int(time.time())
        if self.version >= (3, 4):
            payload_dict: dict[str, Any] = {
                "protocol": 5,
                "t": t,
                "data": {"dps": dps},
            }
            cmd = Message.SET_COMMAND_NEW
        else:
            payload_dict = {"devId": self.device_id, "uid": "", "t": t, "dps": dps}
            cmd = Message.SET_COMMAND
        payload_bytes = json.dumps(payload_dict).encode('utf-8')
        message = Message(
            cmd,
            payload_bytes,
            encrypt=True,
            device=self,
            expect_response=False,
        )
        self._queue.append(message)

    async def _async_request_dps_update(self, dps_ids: list[str] | None = None) -> None:
        """Request the device to send updated DPS values.

        Sends UPDATEDPS (0x12) which asks the device to push the current
        values for the specified DPS IDs.  This is how TinyTuya retrieves
        state from v3.4+/v3.5 devices that don't respond to DP_QUERY.
        """
        if dps_ids:
            payload_dict = {"dpId": [int(d) for d in dps_ids]}
        else:
            payload_dict = {"dpId": [int(d) for d in self._dps_to_request()]}
        payload_bytes = json.dumps(payload_dict).encode('utf-8')
        message = Message(
            Message.UPDATEDPS,
            payload_bytes,
            encrypt=True,
            device=self,
            expect_response=False,
        )
        self._queue.append(message)

    async def async_ping(self, ping_interval: float) -> None:
        """Send a ping to the device.

        This method sends a ping to the device.
        """
        if self._enabled is False:
            return

        if self._backoff is True:
            self._LOGGER.debug("Currently in backoff, not adding ping to queue")
        elif self.version >= (3, 5):
            # v3.5 devices (like T2276) don't support Tuya heartbeats — they
            # close the TCP connection after receiving any ping, regardless of
            # format.  Skip heartbeats entirely; the device will naturally EOF
            # when idle, and process_queue will drive reconnection.
            pass
        else:
            self.last_ping = time.time()
            encrypt = False if self.version < (3, 3) else True
            message = Message(
                Message.PING_COMMAND,
                payload=None,
                sequence=0,
                encrypt=encrypt,
                device=self,
                expect_response=False,
            )
            self._queue.append(message)

        await asyncio.sleep(ping_interval)
        self._ping_task = asyncio.create_task(self.async_ping(self.ping_interval))
        # v3.5 doesn't send heartbeats so skip the pong timeout check.
        if self.version < (3, 5) and self.last_pong < self.last_ping:
            await self.async_disconnect()

    async def _async_pong_received(self, message: Message) -> None:
        """Handle a received pong message.

        This method handles a received pong message from the device.
        """
        self.last_pong = time.time()

    async def async_gratuitous_update_state(self, state_message: Message) -> None:
        """Handle a gratuitous update state message.

        This method handles a gratuitous update state message from the device.
        """
        await self.async_update_state(state_message)
        await self.update_entity_state_cb()

    async def async_update_state(self, state_message: Message, _: Any = None) -> None:
        """Handle a received state message.

        This method handles a received state message from the device.
        Supports both v3.3 format ({"dps": {...}}) and v3.5 format
        ({"protocol": 4, "data": {"dps": {...}}}).
        """
        if (
            state_message is not None
            and state_message.payload is not None
            and isinstance(state_message.payload, dict)
        ):
            payload = state_message.payload
            # v3.5 gratuitous updates nest DPS under "data"
            if "data" in payload and isinstance(payload["data"], dict):
                dps = payload["data"].get("dps")
            else:
                dps = payload.get("dps")
            if dps:
                self._dps.update(dps)
                self._LOGGER.debug("Received updated state {}: {}".format(self, self._dps))

    @property
    def state(self) -> dict[str, Any]:
        """Get the current state of the device.

        Returns:
            A dictionary containing the current state of the device.
        """
        return dict(self._dps)

    @state.setter
    def state(self, new_values: dict[str, Any]) -> None:
        """Set the state of the device.

        This method sets the state of the device.

        Args:
            new_values: A dictionary containing the new state values.
        """
        asyncio.create_task(self.async_set(new_values))

    async def _async_handle_message(self) -> None:
        """Handle incoming messages.

        This method handles incoming messages from the device.
        """
        if self._enabled is False or self._connected is False:
            return

        try:
            suffix = MAGIC_SUFFIX_35_BYTES if self.version >= (3, 5) else MAGIC_SUFFIX_BYTES
            self._response_task = asyncio.create_task(
                self.reader.readuntil(suffix)
            )
            await self._response_task
            response_data = self._response_task.result()
            message = Message.from_bytes(self, response_data, self.cipher)
        except Exception as e:
            if isinstance(e, InvalidMessage):
                self._LOGGER.debug("Invalid message from {}: {}".format(self, e))
            elif isinstance(e, MessageDecodeFailed):
                self._LOGGER.debug("Failed to decrypt message from {}".format(self))
            elif isinstance(e, asyncio.IncompleteReadError):
                if self._connected:
                    self._LOGGER.debug(
                        "Incomplete read (%d bytes partial): %s",
                        len(e.partial), e.partial[:40].hex() if e.partial else "empty"
                    )
                    if len(e.partial) == 0:
                        self._LOGGER.debug("Connection closed by device (EOF)")
                        await self.async_disconnect()
                        return  # Don't reschedule — process_queue will reconnect
            elif isinstance(e, ConnectionResetError):
                self._LOGGER.debug(
                    "Connection reset: {}\n{}".format(e, traceback.format_exc())
                )
                await self.async_disconnect()

        else:
            self._LOGGER.debug("Received message from {}: {}".format(self, message))
            if message.sequence in self._listeners:
                sem = self._listeners[message.sequence]
                if isinstance(sem, asyncio.Semaphore):
                    self._listeners[message.sequence] = message
                    sem.release()
            else:
                handler = self._handlers.get(message.command, None)
                if handler is not None:
                    asyncio.create_task(handler(message))

        self._response_task = None
        asyncio.create_task(self._async_handle_message())

    async def _async_send(self, message: Message, retries: int = 2) -> None:
        """Send a message to the device.

        This method sends a message to the device.
        """
        self._LOGGER.debug("Sending to {}: {}".format(self, message))
        try:
            await self.async_connect()
            if self.writer is None:
                raise ConnectionFailedException("Writer is not initialized")
            self.writer.write(message.to_bytes())
            await self.writer.drain()
        except Exception as e:
            if retries == 0:
                if isinstance(e, socket.error):
                    await self.async_disconnect()

                    raise ConnectionException(
                        "Connection to {} failed: {}".format(self, e)
                    )
                elif isinstance(e, asyncio.IncompleteReadError):
                    raise InvalidMessage(
                        "Incomplete read from: {} : {}".format(self, e)
                    )
                else:
                    raise TuyaException("Failed to send data to {}".format(self))

            if isinstance(e, socket.error):
                self._LOGGER.debug(
                    "Retrying send due to error. Connection to {} failed: {}".format(
                        self, e
                    )
                )
            elif isinstance(e, asyncio.IncompleteReadError):
                self._LOGGER.debug(
                    "Retrying send due to error. Incomplete read from: {} : {}."
                    " Partial data received: {!r}".format(
                        self, e, e.partial
                    )
                )
            else:
                self._LOGGER.debug(
                    "Retrying send due to error. Failed to send data to {}".format(self)
                )
            await asyncio.sleep(0.25)
            await self._async_send(message, retries=retries - 1)

    async def async_receive(self, message: Message) -> Message | None:
        """Receive a message from the device.

        This method receives a message from the device.
        """
        if self._connected is False:
            return None

        has_listener = (message.expect_response is True
                        and hasattr(message, 'listener')
                        and message.listener is not None)
        if has_listener:
            try:
                # We've already checked that message.listener is not None
                listener = message.listener  # This helps mypy understand it's not None
                # Create and await the task directly without storing it in self._recieve_task
                # This avoids type compatibility issues
                if listener is not None:  # Extra check for mypy
                    await asyncio.wait_for(listener.acquire(), timeout=self.timeout)
                response = self._listeners.pop(message.sequence)

                if isinstance(response, Exception):
                    raise response

                # Ensure we're returning the correct type
                if isinstance(response, Message):
                    return response
                return None
            except TimeoutError:
                del self._listeners[message.sequence]
                await self.async_disconnect()
                raise ResponseTimeoutException(
                    "Timed out waiting for response to sequence number {}".format(
                        message.sequence
                    )
                )
            except Exception as e:
                del self._listeners[message.sequence]
                await self.async_disconnect()
                raise e

        # If we don't have a listener, return None
        return None
