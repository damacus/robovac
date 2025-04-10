import asyncio
import json
import logging
from hashlib import md5
from typing import Any, Callable, Dict, List, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_LOGGER = logging.getLogger(__name__)

UDP_KEY = md5(b"yGAdlopoPVldABfn").digest()


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

        This method is called automatically when a datagram is received on one of
        the listening ports. It decrypts the data using AES-ECB and passes the
        decoded JSON to the callback function.

        Args:
            data: The raw bytes received from the device.
            addr: The address (IP, port) tuple of the sender.
        """
        data_bytes = data[20:-8]
        try:
            cipher = Cipher(algorithms.AES(UDP_KEY), modes.ECB(), default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(data_bytes) + decryptor.finalize()
            # Convert bytes to str for JSON parsing
            padding_size = ord(padded_data[len(padded_data) - 1:])
            data_str_value = padded_data[:-padding_size].decode("utf-8")

        except Exception:
            data_str_value = data_bytes.decode()

        decoded = json.loads(data_str_value)
        asyncio.ensure_future(self.discovered_callback(decoded))
