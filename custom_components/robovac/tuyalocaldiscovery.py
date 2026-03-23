import asyncio
import json
import logging
import struct
from hashlib import md5
from typing import Any, Callable, Dict, List, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_LOGGER = logging.getLogger(__name__)

UDP_KEY = md5(b"yGAdlopoPVldABfn").digest()
_AESGCM_UDP = AESGCM(UDP_KEY)

# Protocol 3.5 magic bytes
_PREFIX_35 = 0x00006699
# Protocol 3.5 header: prefix(4) + ver(1) + reserved(1) + seq(4) + cmd(4) + len(4) = 18 bytes
_HEADER_SIZE_35 = 18


def _decrypt_ecb(data_bytes: bytes) -> str:
    """Decrypt AES-ECB encrypted data with PKCS7 unpadding."""
    cipher = Cipher(algorithms.AES(UDP_KEY), modes.ECB(), default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(data_bytes) + decryptor.finalize()
    padding_size = padded_data[-1]
    return padded_data[:-padding_size].decode("utf-8")


def _decrypt_v35(data: bytes) -> str:
    """Decrypt a Protocol 3.5 (AES-GCM) discovery packet.

    Format: prefix(4) + ver(1) + reserved(1) + seq(4) + cmd(4) + len(4)
            + IV(12) + ciphertext + tag(16) + suffix(4)
    """
    # Parse header to get payload_size
    _prefix, _ver, _reserved, _seq, _cmd, payload_size = struct.unpack_from(
        ">IBBIII", data
    )
    iv = data[_HEADER_SIZE_35:_HEADER_SIZE_35 + 12]
    # payload_size covers IV(12) + ciphertext + tag(16)
    ciphertext_len = payload_size - 12 - 16
    ct_start = _HEADER_SIZE_35 + 12
    ciphertext = data[ct_start:ct_start + ciphertext_len]
    tag = data[ct_start + ciphertext_len:ct_start + ciphertext_len + 16]
    # AAD = header bytes after prefix (14 bytes)
    aad = data[4:_HEADER_SIZE_35]
    plaintext = _AESGCM_UDP.decrypt(iv, ciphertext + tag, aad)
    # v3.5 may have binary prefix before JSON (retcode, version header)
    if plaintext and plaintext[0:1] != b"{":
        json_start = plaintext.find(b"{")
        if json_start > 0:
            plaintext = plaintext[json_start:]
    return plaintext.decode("utf-8")


class DiscoveryPortsNotAvailableException(Exception):
    """This model is not supported"""


class TuyaLocalDiscovery(asyncio.DatagramProtocol):
    def __init__(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        self.devices: Dict[str, Any] = {}
        self._listeners: List[Tuple[asyncio.DatagramTransport, Any]] = []
        self.discovered_callback = callback

    async def start(self) -> None:
        """Start listening for Tuya local broadcasts.

        Sets up UDP listeners on ports 6666 and 6667 to receive
        broadcast messages from Tuya devices on the local network.

        Raises:
            DiscoveryPortsNotAvailableException: If the required ports are unavailable.
        """
        loop = asyncio.get_running_loop()
        listener = loop.create_datagram_endpoint(
            lambda: self, local_addr=("0.0.0.0", 6666), reuse_port=True
        )
        encrypted_listener = loop.create_datagram_endpoint(
            lambda: self, local_addr=("0.0.0.0", 6667), reuse_port=True
        )

        try:
            # Store the listeners directly
            listener_result, encrypted_listener_result = await asyncio.gather(
                listener, encrypted_listener
            )
            self._listeners = [listener_result, encrypted_listener_result]
            _LOGGER.debug("Listening to broadcasts on UDP port 6666 and 6667")
        except Exception:
            # Log the error before raising the exception
            _LOGGER.exception("Failed to set up Tuya local discovery")
            error_msg = (
                "Ports 6666 and 6667 are needed for autodiscovery but are unavailable. "
                "This may be due to having the localtuya integration installed and it not "
                "allowing other integrations to use the same ports. "
                "A pull request has been raised to address this: "
                "https://github.com/rospogrigio/localtuya/pull/1481"
            )
            raise DiscoveryPortsNotAvailableException(error_msg)

    def close(self, *args: Any, **kwargs: Any) -> None:
        """Close all open UDP listeners.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        for transport, _ in self._listeners:
            transport.close()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Process received UDP datagrams from Tuya devices.

        Handles Protocol 3.1-3.3 (AES-ECB), 3.4 (AES-ECB with HMAC footer),
        3.5 (AES-GCM), and unencrypted broadcasts.

        Args:
            data: The raw bytes received from the device.
            addr: The address (IP, port) tuple of the sender.
        """
        if len(data) < 24:
            return

        try:
            data_str_value = self._decrypt_payload(data)
        except Exception:
            _LOGGER.debug(
                "Failed to decrypt discovery packet from %s (%d bytes)",
                addr[0],
                len(data),
            )
            return

        try:
            decoded = json.loads(data_str_value)
        except (json.JSONDecodeError, ValueError):
            _LOGGER.debug("Failed to parse discovery JSON from %s", addr[0])
            return

        asyncio.ensure_future(self.discovered_callback(decoded))

    @staticmethod
    def _decrypt_payload(data: bytes) -> str:
        """Decrypt a discovery packet payload, trying all supported protocols."""
        prefix = struct.unpack_from(">I", data)[0]

        # Protocol 3.5: AES-GCM with 0x00006699 magic prefix
        if prefix == _PREFIX_35:
            return _decrypt_v35(data)

        # Protocol 3.1-3.3: AES-ECB, header(20) + payload + crc(4) + suffix(4)
        data_bytes = data[20:-8]
        try:
            return _decrypt_ecb(data_bytes)
        except Exception:
            pass

        # Protocol 3.4: AES-ECB, header(20) + payload + hmac(32) + suffix(4)
        data_bytes_34 = data[20:-36]
        if len(data_bytes_34) > 0 and len(data_bytes_34) % 16 == 0:
            try:
                return _decrypt_ecb(data_bytes_34)
            except Exception:
                pass

        # Unencrypted broadcast (port 6666): raw UTF-8
        return data[20:-8].decode("utf-8")
