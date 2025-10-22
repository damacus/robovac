"""PyTuya Device Wrapper.

Wrapper around LocalTuya's PyTuya implementation to provide the same interface
as our existing TuyaDevice class. This allows gradual migration to PyTuya
for models that need protocol 3.5 support.

This is a bridge/adapter pattern to minimize code changes during migration.
"""
import asyncio
import logging
from typing import Any, Callable, Optional

from .pytuya import connect, TuyaListener

_LOGGER = logging.getLogger(__name__)


class PyTuyaDeviceListener(TuyaListener):
    """Listener for PyTuya device status updates."""

    def __init__(self, callback: Optional[Callable[[dict], None]] = None):
        """Initialize listener with optional callback."""
        self.callback = callback
        self._status: dict[str, Any] = {}

    def status_updated(self, status: dict) -> None:
        """Handle status update from device."""
        _LOGGER.debug("PyTuya status updated: %s", status)
        self._status = status
        if self.callback:
            self.callback(status)

    def disconnected(self) -> None:
        """Handle device disconnection."""
        _LOGGER.debug("PyTuya device disconnected")


class PyTuyaDevice:
    """Wrapper around PyTuya protocol to match TuyaDevice interface.

    This class provides the same API as TuyaDevice but uses LocalTuya's
    PyTuya implementation under the hood. This allows us to support
    protocol versions 3.1-3.5 without breaking existing code.
    """

    def __init__(
        self,
        device_id: str,
        host: str,
        local_key: str,
        timeout: float = 5.0,
        ping_interval: float = 120.0,
        protocol_version: float = 3.1,
        update_entity_state: Optional[Callable[[dict], None]] = None,
        port: int = 6668,
    ):
        """Initialize PyTuya device wrapper.

        Args:
            device_id: Tuya device ID
            host: IP address of device
            local_key: Encryption key for device
            timeout: Connection timeout in seconds
            ping_interval: Heartbeat interval in seconds (not used in PyTuya)
            protocol_version: Tuya protocol version (3.1, 3.3, 3.4, 3.5)
            update_entity_state: Callback for status updates
            port: Device port (default 6668)
        """
        self.device_id = device_id
        self.host = host
        self.local_key = local_key
        self.timeout = timeout
        self.port = port
        self.protocol_version = protocol_version

        # Convert protocol version to string format PyTuya expects
        self.protocol_version_str = str(protocol_version)

        self._protocol: Optional[Any] = None
        self._listener = PyTuyaDeviceListener(callback=update_entity_state)
        self._dps: dict[str, Any] = {}
        self._connected = False

        _LOGGER.info(
            "Initialized PyTuyaDevice for %s at %s (protocol %s)",
            device_id,
            host,
            protocol_version,
        )

    async def connect(self) -> None:
        """Connect to the device using PyTuya."""
        if self._connected:
            _LOGGER.debug("Already connected to %s", self.device_id)
            return

        try:
            _LOGGER.debug(
                "Connecting to %s at %s using protocol %s",
                self.device_id,
                self.host,
                self.protocol_version_str,
            )

            self._protocol = await connect(
                address=self.host,
                device_id=self.device_id,
                local_key=self.local_key,
                protocol_version=self.protocol_version_str,
                enable_debug=True,
                listener=self._listener,
                port=self.port,
                timeout=self.timeout,
            )

            self._connected = True
            _LOGGER.info("Successfully connected to %s", self.device_id)

        except Exception as e:
            _LOGGER.error("Failed to connect to %s: %s", self.device_id, e)
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._protocol:
            try:
                self._protocol.close()
                _LOGGER.debug("Disconnected from %s", self.device_id)
            except Exception as e:
                _LOGGER.error("Error disconnecting from %s: %s", self.device_id, e)
            finally:
                self._protocol = None
                self._connected = False

    async def status(self) -> dict[str, Any]:
        """Get current device status.

        Returns:
            Dictionary of DPS values
        """
        if not self._connected:
            await self.connect()

        if not self._protocol:
            raise RuntimeError(f"Not connected to {self.device_id}")

        try:
            # Request status update
            await self._protocol.status()

            # Wait a bit for response
            await asyncio.sleep(0.5)

            # Return cached status from listener
            return self._listener._status

        except Exception as e:
            _LOGGER.error("Error getting status from %s: %s", self.device_id, e)
            raise

    async def set_dp(self, value: Any, dp_index: int) -> None:
        """Set a datapoint value.

        Args:
            value: Value to set
            dp_index: DPS index to set
        """
        if not self._connected:
            await self.connect()

        if not self._protocol:
            raise RuntimeError(f"Not connected to {self.device_id}")

        try:
            _LOGGER.debug("Setting DP %s to %s on %s", dp_index, value, self.device_id)

            # PyTuya expects DPS as a dictionary
            dps_dict = {str(dp_index): value}
            await self._protocol.set_dps(dps_dict)

            _LOGGER.debug("Successfully set DP %s on %s", dp_index, self.device_id)

        except Exception as e:
            _LOGGER.error(
                "Error setting DP %s on %s: %s",
                dp_index,
                self.device_id,
                e,
            )
            raise

    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._connected

    def __repr__(self) -> str:
        """Return string representation."""
        return f"PyTuyaDevice({self.device_id} at {self.host}, protocol {self.protocol_version})"
