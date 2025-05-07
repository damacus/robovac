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
from typing import Any, Awaitable, Callable, Coroutine, Optional, Union
from asyncio import Semaphore, StreamWriter
from .vacuums.base import RobovacCommand

from cryptography.hazmat.backends.openssl import backend as openssl_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hashes import Hash, MD5
from cryptography.hazmat.primitives.padding import PKCS7

INITIAL_BACKOFF = 5
INITIAL_QUEUE_TIME = 0.1
BACKOFF_MULTIPLIER = 1.70224
_LOGGER = logging.getLogger(__name__)
MESSAGE_PREFIX_FORMAT = ">IIII"
MESSAGE_SUFFIX_FORMAT = ">II"
MAGIC_PREFIX = 0x000055AA
MAGIC_SUFFIX = 0x0000AA55
MAGIC_SUFFIX_BYTES = struct.pack(">I", MAGIC_SUFFIX)
CRC_32_TABLE = [
    0x00000000,
    0x77073096,
    0xEE0E612C,
    0x990951BA,
    0x076DC419,
    0x706AF48F,
    0xE963A535,
    0x9E6495A3,
    0x0EDB8832,
    0x79DCB8A4,
    0xE0D5E91E,
    0x97D2D988,
    0x09B64C2B,
    0x7EB17CBD,
    0xE7B82D07,
    0x90BF1D91,
    0x1DB71064,
    0x6AB020F2,
    0xF3B97148,
    0x84BE41DE,
    0x1ADAD47D,
    0x6DDDE4EB,
    0xF4D4B551,
    0x83D385C7,
    0x136C9856,
    0x646BA8C0,
    0xFD62F97A,
    0x8A65C9EC,
    0x14015C4F,
    0x63066CD9,
    0xFA0F3D63,
    0x8D080DF5,
    0x3B6E20C8,
    0x4C69105E,
    0xD56041E4,
    0xA2677172,
    0x3C03E4D1,
    0x4B04D447,
    0xD20D85FD,
    0xA50AB56B,
    0x35B5A8FA,
    0x42B2986C,
    0xDBBBC9D6,
    0xACBCF940,
    0x32D86CE3,
    0x45DF5C75,
    0xDCD60DCF,
    0xABD13D59,
    0x26D930AC,
    0x51DE003A,
    0xC8D75180,
    0xBFD06116,
    0x21B4F4B5,
    0x56B3C423,
    0xCFBA9599,
    0xB8BDA50F,
    0x2802B89E,
    0x5F058808,
    0xC60CD9B2,
    0xB10BE924,
    0x2F6F7C87,
    0x58684C11,
    0xC1611DAB,
    0xB6662D3D,
    0x76DC4190,
    0x01DB7106,
    0x98D220BC,
    0xEFD5102A,
    0x71B18589,
    0x06B6B51F,
    0x9FBFE4A5,
    0xE8B8D433,
    0x7807C9A2,
    0x0F00F934,
    0x9609A88E,
    0xE10E9818,
    0x7F6A0DBB,
    0x086D3D2D,
    0x91646C97,
    0xE6635C01,
    0x6B6B51F4,
    0x1C6C6162,
    0x856530D8,
    0xF262004E,
    0x6C0695ED,
    0x1B01A57B,
    0x8208F4C1,
    0xF50FC457,
    0x65B0D9C6,
    0x12B7E950,
    0x8BBEB8EA,
    0xFCB9887C,
    0x62DD1DDF,
    0x15DA2D49,
    0x8CD37CF3,
    0xFBD44C65,
    0x4DB26158,
    0x3AB551CE,
    0xA3BC0074,
    0xD4BB30E2,
    0x4ADFA541,
    0x3DD895D7,
    0xA4D1C46D,
    0xD3D6F4FB,
    0x4369E96A,
    0x346ED9FC,
    0xAD678846,
    0xDA60B8D0,
    0x44042D73,
    0x33031DE5,
    0xAA0A4C5F,
    0xDD0D7CC9,
    0x5005713C,
    0x270241AA,
    0xBE0B1010,
    0xC90C2086,
    0x5768B525,
    0x206F85B3,
    0xB966D409,
    0xCE61E49F,
    0x5EDEF90E,
    0x29D9C998,
    0xB0D09822,
    0xC7D7A8B4,
    0x59B33D17,
    0x2EB40D81,
    0xB7BD5C3B,
    0xC0BA6CAD,
    0xEDB88320,
    0x9ABFB3B6,
    0x03B6E20C,
    0x74B1D29A,
    0xEAD54739,
    0x9DD277AF,
    0x04DB2615,
    0x73DC1683,
    0xE3630B12,
    0x94643B84,
    0x0D6D6A3E,
    0x7A6A5AA8,
    0xE40ECF0B,
    0x9309FF9D,
    0x0A00AE27,
    0x7D079EB1,
    0xF00F9344,
    0x8708A3D2,
    0x1E01F268,
    0x6906C2FE,
    0xF762575D,
    0x806567CB,
    0x196C3671,
    0x6E6B06E7,
    0xFED41B76,
    0x89D32BE0,
    0x10DA7A5A,
    0x67DD4ACC,
    0xF9B9DF6F,
    0x8EBEEFF9,
    0x17B7BE43,
    0x60B08ED5,
    0xD6D6A3E8,
    0xA1D1937E,
    0x38D8C2C4,
    0x4FDFF252,
    0xD1BB67F1,
    0xA6BC5767,
    0x3FB506DD,
    0x48B2364B,
    0xD80D2BDA,
    0xAF0A1B4C,
    0x36034AF6,
    0x41047A60,
    0xDF60EFC3,
    0xA867DF55,
    0x316E8EEF,
    0x4669BE79,
    0xCB61B38C,
    0xBC66831A,
    0x256FD2A0,
    0x5268E236,
    0xCC0C7795,
    0xBB0B4703,
    0x220216B9,
    0x5505262F,
    0xC5BA3BBE,
    0xB2BD0B28,
    0x2BB45A92,
    0x5CB36A04,
    0xC2D7FFA7,
    0xB5D0CF31,
    0x2CD99E8B,
    0x5BDEAE1D,
    0x9B64C2B0,
    0xEC63F226,
    0x756AA39C,
    0x026D930A,
    0x9C0906A9,
    0xEB0E363F,
    0x72076785,
    0x05005713,
    0x95BF4A82,
    0xE2B87A14,
    0x7BB12BAE,
    0x0CB61B38,
    0x92D28E9B,
    0xE5D5BE0D,
    0x7CDCEFB7,
    0x0BDBDF21,
    0x86D3D2D4,
    0xF1D4E242,
    0x68DDB3F8,
    0x1FDA836E,
    0x81BE16CD,
    0xF6B9265B,
    0x6FB077E1,
    0x18B74777,
    0x88085AE6,
    0xFF0F6A70,
    0x66063BCA,
    0x11010B5C,
    0x8F659EFF,
    0xF862AE69,
    0x616BFFD3,
    0x166CCF45,
    0xA00AE278,
    0xD70DD2EE,
    0x4E048354,
    0x3903B3C2,
    0xA7672661,
    0xD06016F7,
    0x4969474D,
    0x3E6E77DB,
    0xAED16A4A,
    0xD9D65ADC,
    0x40DF0B66,
    0x37D83BF0,
    0xA9BCAE53,
    0xDEBB9EC5,
    0x47B2CF7F,
    0x30B5FFE9,
    0xBDBDF21C,
    0xCABAC28A,
    0x53B39330,
    0x24B4A3A6,
    0xBAD03605,
    0xCDD70693,
    0x54DE5729,
    0x23D967BF,
    0xB3667A2E,
    0xC4614AB8,
    0x5D681B02,
    0x2A6F2B94,
    0xB40BBE37,
    0xC30C8EA1,
    0x5A05DF1B,
    0x2D02EF8D,
]


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
        self.cipher = Cipher(
            algorithms.AES(key.encode("ascii")), modes.ECB(), backend=openssl_backend
        )

    def get_prefix_size_and_validate(self, command: int, encrypted_data: bytes) -> int:
        """Get the prefix size and validate the encrypted data.

        Args:
            command: The command to be encrypted.
            encrypted_data: The encrypted data.

        Returns:
            The prefix size.
        """
        try:
            version = tuple(map(int, encrypted_data[:3].decode("utf8").split(".")))
        except ValueError:
            version = (0, 0)
        if version != self.version:
            return 0
        if version < (3, 3):
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
        prefix_size = self.get_prefix_size_and_validate(command, data)
        data = data[prefix_size:]
        decryptor = self.cipher.decryptor()
        if self.version < (3, 3):
            data = base64.b64decode(data)
        decrypted_data = decryptor.update(data)
        decrypted_data += decryptor.finalize()
        unpadder = PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted_data)
        unpadded_data += unpadder.finalize()

        # Explicitly cast to bytes to satisfy mypy
        return bytes(unpadded_data)

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
    c = 0xFFFFFFFF
    for b in data:
        c = (c >> 8) ^ CRC_32_TABLE[(c ^ b) & 255]

    return c ^ 0xFFFFFFFF


class Message:
    PING_COMMAND = 0x09
    GET_COMMAND = 0x0A
    SET_COMMAND = 0x07
    GRATUITOUS_UPDATE = 0x08

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
        if isinstance(payload_data, dict):
            payload_data = json.dumps(payload_data, separators=(",", ":"))
        if not isinstance(payload_data, bytes):
            payload_data = payload_data.encode("utf8")

        if self.encrypt and self.device is not None:
            payload_data = self.device.cipher.encrypt(self.command, payload_data)

        payload_size = len(payload_data) + struct.calcsize(MESSAGE_SUFFIX_FORMAT)

        header = struct.pack(
            MESSAGE_PREFIX_FORMAT,
            MAGIC_PREFIX,
            self.sequence,
            self.command,
            payload_size,
        )
        if self.device and self.device.version >= (3, 3):
            checksum = crc(header + payload_data)
        else:
            checksum = crc(payload_data)
        footer = struct.pack(MESSAGE_SUFFIX_FORMAT, checksum, MAGIC_SUFFIX)
        return header + payload_data + footer

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
        try:
            prefix, sequence, command, payload_size = struct.unpack_from(
                MESSAGE_PREFIX_FORMAT, data
            )
        except struct.error as e:
            raise InvalidMessage("Invalid message header format.") from e
        if prefix != MAGIC_PREFIX:
            raise InvalidMessage("Magic prefix missing from message.")

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
                - struct.calcsize(MESSAGE_SUFFIX_FORMAT)
            ]
            return_code = None
        else:
            payload_data = data[
                header_size
                + struct.calcsize(">I"):header_size
                + payload_size
                - struct.calcsize(MESSAGE_SUFFIX_FORMAT)
            ]

        try:
            expected_crc, suffix = struct.unpack_from(
                MESSAGE_SUFFIX_FORMAT,
                data,
                header_size + payload_size - struct.calcsize(MESSAGE_SUFFIX_FORMAT),
            )
        except struct.error as e:
            raise InvalidMessage("Invalid message suffix format.") from e
        if suffix != MAGIC_SUFFIX:
            raise InvalidMessage("Magic suffix missing from message")

        # Ensure data is not None before indexing
        if data is None:
            raise InvalidMessage("Data cannot be None")

        actual_crc = crc(
            data[: header_size + payload_size - struct.calcsize(MESSAGE_SUFFIX_FORMAT)]
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
                device._LOGGER.error(e)
                raise MessageDecodeFailed() from e
            try:
                payload = json.loads(payload_text)
            except json.decoder.JSONDecodeError as e:
                # data may be encrypted
                device._LOGGER.debug(payload_data.hex())
                device._LOGGER.error(e)
                raise MessageDecodeFailed() from e

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
        }
        self._dps: dict[str, Any] = {}
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
                        600,
                    )
                    self._LOGGER.warn(
                        "{} failures, backing off for {} seconds".format(
                            self._failures, self._queue_interval
                        )
                    )

        await asyncio.sleep(self._queue_interval)
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
        """
        if self._connected is True or self._enabled is False:
            return

        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        self._LOGGER.debug("Connecting to {}".format(self))
        try:
            sock.connect((self.host, self.port))
        except (socket.timeout, TimeoutError):
            self._dps[self.model_details.commands[RobovacCommand.ERROR]] = ("CONNECTION_FAILED")
            raise ConnectionTimeoutException("Connection timed out")
        loop = asyncio.get_running_loop()
        loop.create_connection
        self.reader, self.writer = await asyncio.open_connection(sock=sock)
        self._connected = True

        if self._ping_task is None:
            self._ping_task = asyncio.create_task(self.async_ping(self.ping_interval))

        asyncio.create_task(self._async_handle_message())

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

    async def async_get(self) -> None:
        """Get the current state of the device.

        This method retrieves the current state of the device.
        """
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
        payload_dict = {"devId": self.device_id, "uid": "", "t": t, "dps": dps}
        payload_bytes = json.dumps(payload_dict).encode('utf-8')
        message = Message(
            Message.SET_COMMAND,
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
        if self.last_pong < self.last_ping:
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
        """
        if (
            state_message is not None
            and state_message.payload is not None
            and isinstance(state_message.payload, dict)
            and "dps" in state_message.payload
        ):
            self._dps.update(state_message.payload["dps"])
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
            self._response_task = asyncio.create_task(
                self.reader.readuntil(MAGIC_SUFFIX_BYTES)
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
                    self._LOGGER.debug("Incomplete read")
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
