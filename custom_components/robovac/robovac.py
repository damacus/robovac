from typing import Any, cast, Union
from collections.abc import Mapping
from homeassistant.components.vacuum import VacuumActivity

from .case_insensitive_lookup import case_insensitive_lookup
from .tuyalocalapi import TuyaDevice
from .pytuya_device import PyTuyaDevice
from .vacuums import ROBOVAC_MODELS
from .vacuums.base import RobovacModelDetails, RobovacCommand

import logging

_LOGGER = logging.getLogger(__name__)


class ModelNotSupportedException(Exception):
    """This model is not supported"""


class RoboVac(TuyaDevice):
    """Tuya RoboVac device integration for Home Assistant.

    This class provides the main interface for controlling and monitoring
    Tuya-based robotic vacuum cleaners. It handles model-specific features,
    command mappings, and state translations.

    Attributes:
        model_details: Model-specific configuration and feature mappings
        model_code: The specific model identifier (e.g., "T2080", "L60")
    """
    model_details: type[RobovacModelDetails]

    def __new__(cls, model_code: str, *args: Any, **kwargs: Any) -> "RoboVac":  # type: ignore[misc]
        """Create appropriate RoboVac instance based on model configuration.

        Args:
            model_code: The model identifier for the vacuum
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            RoboVac or PyTuyaRoboVac instance based on model's use_pytuya flag

        Raises:
            ModelNotSupportedException: If the model_code is not supported
        """
        if model_code not in ROBOVAC_MODELS:
            raise ModelNotSupportedException(
                f"Model {model_code} is not supported"
            )

        model_details = ROBOVAC_MODELS[model_code]()

        # Check if model wants to use PyTuya implementation
        if hasattr(model_details, 'use_pytuya') and model_details.use_pytuya:
            _LOGGER.info("Using PyTuya implementation for model %s", model_code)
            return object.__new__(PyTuyaRoboVac)  # type: ignore[return-value]
        else:
            return object.__new__(cls)

    def __init__(self, model_code: str, *args: Any, **kwargs: Any):
        """Initialize the RoboVac device.

        Args:
            model_code: The model identifier for the vacuum (must exist in ROBOVAC_MODELS)
            *args: Additional arguments passed to TuyaDevice
            **kwargs: Additional keyword arguments passed to TuyaDevice

        Raises:
            ModelNotSupportedException: If the model_code is not supported
        """
        # Determine model_details first
        if model_code not in ROBOVAC_MODELS:
            raise ModelNotSupportedException(
                f"Model {model_code} is not supported"
            )
        current_model_details = ROBOVAC_MODELS[model_code]

        super().__init__(current_model_details, *args, **kwargs)

        self.model_code = model_code
        self.model_details = current_model_details

    def getHomeAssistantFeatures(self) -> int:
        """Get the Home Assistant supported features for this vacuum model.

        Returns:
            int: Bitwise OR of VacuumEntityFeature constants indicating which
                 Home Assistant vacuum features are supported by this model.
        """
        return self.model_details.homeassistant_features

    def getRoboVacFeatures(self) -> int:
        """Get the RoboVac-specific supported features for this vacuum model.

        Returns:
            int: Bitwise OR of custom RoboVac feature constants indicating which
                 vacuum-specific features are supported by this model.
        """
        return self.model_details.robovac_features

    def getRoboVacActivityMapping(self) -> dict[str, VacuumActivity] | None:
        """Get the mapping of device statuses to Home Assistant VacuumActivity enums.

        Returns:
            dict[str, VacuumActivity] | None: Dictionary mapping human-readable vacuum
                statuses (e.g., "Auto cleaning", "Returning home") to Home Assistant
                VacuumActivity enum values, or None if not configured for this model.
        """
        return self.model_details.activity_mapping

    def _get_command_values(
        self, command_name: RobovacCommand
    ) -> dict[str, str] | None:
        """Get the values for a specific command from the model details.

        This is a helper method to safely access command values for the current model.

        Args:
            command_name: The RobovacCommand enum value to get values for

        Returns:
            dict[str, str] | None: Dictionary mapping human-readable values to
                device-specific command codes, or None if command not supported
        """
        if command_name not in self.model_details.commands:
            return None

        command = self.model_details.commands[command_name]
        if not isinstance(command, dict) or "values" not in command:
            return None

        values = command["values"]
        if not isinstance(values, dict):
            return None

        return values

    def getFanSpeeds(self) -> list[str]:
        """Get the supported fan speeds for this vacuum model.

        Returns:
            list[str]: List of human-readable fan speed names (e.g., ["Standard", "Boost IQ", "Max"])
                      Returns empty list if fan speed control is not supported by this model.
        """
        values = self._get_command_values(RobovacCommand.FAN_SPEED)
        if values is None:
            return []

        # Return the values from the dictionary (the display names)
        # This preserves existing behavior for tests
        return list(values.values())

    def getSupportedCommands(self) -> list[str]:
        """Get the list of supported commands for this vacuum model.

        Returns:
            list[str]: List of RobovacCommand enum names that are supported by this model
                      (e.g., ["MODE", "FAN_SPEED", "AUTO_RETURN"])
        """
        return list(self.model_details.commands.keys())

    def getDpsCodes(self) -> dict[str, str]:
        """Get the DPS codes for this model based on command codes.

        Maps command names to their corresponding DPS code names and returns
        a dictionary of DPS codes for status updates.

        Returns:
            dict[str, str]: Dictionary mapping DPS code names (e.g., "BATTERY_LEVEL", "ERROR_CODE")
                           to their numeric string values (e.g., "104", "106") for Tuya communication
        """
        # Map command names to DPS code names
        command_to_dps = {
            "BATTERY": "BATTERY_LEVEL",
            "ERROR": "ERROR_CODE",
            # All others use the same code names
        }

        codes = {}
        # Extract codes from commands dictionary
        for key, value in self.model_details.commands.items():
            # Get the DPS name from the mapping, or use the command name if not in mapping
            dps_name = command_to_dps.get(key.name, key.name)

            # Extract code value based on whether it's a direct value or in a dictionary
            if isinstance(value, dict) and "code" in value:
                # If it has a code property, use that
                codes[dps_name] = str(value["code"])
            elif isinstance(value, dict):
                # Skip dictionaries without code property (like when only 'values' is present)
                continue
            else:
                # For direct values, use the value itself
                codes[dps_name] = str(value)

        return codes

    def getRoboVacCommandValue(self, command_name: RobovacCommand, value: str) -> str:
        """Convert human-readable command value to model-specific device value.

        Translates user-friendly command values to the actual values that need to be
        sent to the vacuum device via the Tuya protocol.

        Args:
            command_name: The command type (e.g., RobovacCommand.MODE, RobovacCommand.FAN_SPEED)
            value: The human-readable value (e.g., "auto", "edge", "Standard")

        Returns:
            str: The model-specific value for the device (e.g., "BBoCCAE=" for L60 "auto" mode,
                 "CAoCCAE=" for T2080 base64-encoded commands). Returns the original value
                 if no mapping exists.
        """
        try:
            # Check if command_name is already a RobovacCommand enum
            cmd = command_name if isinstance(command_name, RobovacCommand) else RobovacCommand(command_name)
            values = self._get_command_values(cmd)

            if values is not None and value in values:
                return str(values[value])

        except (ValueError, KeyError):
            pass

        return value

    def getRoboVacHumanReadableValue(self, command_name: RobovacCommand, value: str) -> str:
        """Convert model-specific device value to human-readable command value.

        Translates device-specific values received from the vacuum via Tuya protocol
        to user-friendly, human-readable values for display in Home Assistant.

        Args:
            command_name: The command type (e.g., RobovacCommand.STATUS, RobovacCommand.MODE)
            value: The model-specific value from device (e.g., "CAoCCAE=" base64 encoded, "2")

        Returns:
            str: The human-readable value (e.g., "Auto cleaning", "Returning home", "auto").
                 Returns the original value if no mapping exists.
        """
        values = None
        try:
            # Check if command_name is already a RobovacCommand enum
            cmd = command_name if isinstance(command_name, RobovacCommand) else RobovacCommand(command_name)
            values = self._get_command_values(cmd)

            if values is not None:
                # Try case-insensitive lookup
                result = case_insensitive_lookup(values, value)
                if result is not None:
                    return str(result)

                # Only log if values dict exists but value not found
                _LOGGER.debug(
                    "Command %s with value %r (type: %s) not found for model %s. "
                    "Available keys: %r",
                    command_name,
                    value,
                    type(value).__name__,
                    self.model_code,
                    list(values.keys()),
                )

        except (ValueError, KeyError):
            pass

        return value


class PyTuyaRoboVac(PyTuyaDevice):
    """RoboVac implementation using PyTuya protocol.

    This class uses LocalTuya's PyTuya implementation for models that require
    protocol version 3.5 or have issues with the legacy implementation.
    It provides the same interface as RoboVac but uses PyTuyaDevice for protocol.
    """

    model_details: type[RobovacModelDetails]
    model_code: str

    def __init__(self, model_code: str, device_id: str, host: str, local_key: str,
                 timeout: float, ping_interval: float, update_entity_state: Any,
                 port: int = 6668, **kwargs: Any):
        """Initialize PyTuya-based RoboVac.

        Args:
            model_code: The model identifier for the vacuum
            device_id: Tuya device ID
            host: IP address of device
            local_key: Encryption key
            timeout: Connection timeout
            ping_interval: Heartbeat interval (not used in PyTuya)
            update_entity_state: Callback for status updates
            port: Device port
            **kwargs: Additional arguments
        """
        # Validate model
        if model_code not in ROBOVAC_MODELS:
            raise ModelNotSupportedException(
                f"Model {model_code} is not supported"
            )

        current_model_details = ROBOVAC_MODELS[model_code]
        self.model_code = model_code
        self.model_details = current_model_details

        # Get protocol version from model details
        protocol_version = getattr(current_model_details, 'protocol_version', 3.1)

        # Initialize PyTuyaDevice
        PyTuyaDevice.__init__(
            self,
            device_id=device_id,
            host=host,
            local_key=local_key,
            timeout=timeout,
            ping_interval=ping_interval,
            protocol_version=protocol_version,
            update_entity_state=update_entity_state,
            port=port,
        )

        _LOGGER.info(
            "Initialized PyTuyaRoboVac for %s (model: %s, protocol: %s)",
            device_id,
            model_code,
            protocol_version,
        )

    # Copy all RoboVac methods that don't depend on TuyaDevice
    def getHomeAssistantFeatures(self) -> int:
        """Get the Home Assistant supported features for this vacuum model."""
        return self.model_details.homeassistant_features

    def getRoboVacFeatures(self) -> int:
        """Get the RoboVac-specific features for this vacuum model."""
        return self.model_details.robovac_features

    def getAvailableCommands(self) -> list[str]:
        """Get list of available commands for this vacuum model."""
        return list(self.model_details.commands.keys())

    def getDpsCodes(self) -> dict[str, str]:
        """Get the DPS codes for this model based on command codes."""
        command_to_dps = {
            "BATTERY": "BATTERY_LEVEL",
            "ERROR": "ERROR_CODE",
        }

        codes = {}
        for key, value in self.model_details.commands.items():
            dps_name = command_to_dps.get(key.name, key.name)

            if isinstance(value, dict) and "code" in value:
                codes[dps_name] = str(value["code"])
            elif isinstance(value, dict):
                continue
            else:
                codes[dps_name] = str(value)

        return codes

    def getRoboVacCommandValue(self, command_name: RobovacCommand, value: str) -> str:
        """Convert human-readable command value to model-specific device value."""
        values = None
        try:
            cmd = command_name if isinstance(command_name, RobovacCommand) else RobovacCommand(command_name)
            values = self._get_command_values(cmd)

            if values is not None:
                result = case_insensitive_lookup(values, value)
                if result is not None:
                    return str(result)

        except (ValueError, KeyError):
            pass

        return value

    def getRoboVacHumanReadableValue(self, command_name: RobovacCommand | str, value: str) -> str:
        """Convert model-specific value to human-readable value."""
        values = None
        try:
            cmd = command_name if isinstance(command_name, RobovacCommand) else RobovacCommand(command_name)
            values = self._get_command_values(cmd)

            if values is not None:
                result = case_insensitive_lookup(values, value)
                if result is not None:
                    return str(result)

                _LOGGER.debug(
                    "Command %s with value %r (type: %s) not found for model %s. "
                    "Available keys: %r",
                    command_name,
                    value,
                    type(value).__name__,
                    self.model_code,
                    list(values.keys()),
                )

        except (ValueError, KeyError):
            pass

        return value

    def getRoboVacActivityMapping(self) -> Mapping[str, VacuumActivity] | None:
        """Get the activity mapping for this vacuum model."""
        return self.model_details.activity_mapping

    def _get_command_values(self, command_name: RobovacCommand) -> dict[str, str] | None:
        """Get the values dictionary for a specific command."""
        if command_name not in self.model_details.commands:
            return None

        command_data = self.model_details.commands[command_name]
        if isinstance(command_data, dict) and "values" in command_data:
            return cast(dict[str, str], command_data["values"])

        return None
