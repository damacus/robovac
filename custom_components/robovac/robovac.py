from typing import Any, Dict, List, Optional, Type, Union, cast

from .tuyalocalapi import TuyaDevice
from .vacuums import ROBOVAC_MODELS
from .vacuums.base import RobovacCommand, RobovacModelDetails


class ModelNotSupportedException(Exception):
    """This model is not supported"""


class RoboVac(TuyaDevice):
    """Tuya RoboVac device."""
    model_details: Type[RobovacModelDetails]

    def __init__(self, model_code: str, *args: Any, **kwargs: Any):
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
        """Get the supported features of the device.

        Returns:
            An integer representing the supported features of the device.
        """
        return self.model_details.homeassistant_features

    def getRoboVacFeatures(self) -> int:
        """Get the supported features of the device.

        Returns:
            An integer representing the supported features of the device.
        """
        return self.model_details.robovac_features

    def _get_command_values(
        self, command_name: RobovacCommand
    ) -> Optional[Union[List[str], Dict[str, str]]]:
        """Get the values for a specific command from the model details.

        This is a helper method to safely access command values.

        Args:
            command_name: The RobovacCommand enum value

        Returns:
            The command values as a list or dict, or None if not found/invalid
        """
        if command_name not in self.model_details.commands:
            return None

        command = self.model_details.commands[command_name]
        if not isinstance(command, dict) or "values" not in command:
            return None

        values = command["values"]
        if not isinstance(values, (list, dict)):
            return None

        return values

    def getFanSpeeds(self) -> list[str]:
        """Get the supported fan speeds of the device.

        Returns:
            A list of strings representing the supported fan speeds of the device.
        """
        values = self._get_command_values(RobovacCommand.FAN_SPEED)
        if values is None:
            return []

        if isinstance(values, list):
            return cast(List[str], values)
        else:  # It's a dict
            return list(values.keys())

    def getSupportedCommands(self) -> list[str]:
        return list(self.model_details.commands.keys())

    def getDpsCodes(self) -> dict[str, str]:
        """Get the DPS codes for this model based on command codes.

        Maps command names to their corresponding DPS code names and returns
        a dictionary of DPS codes for status updates.

        Returns:
            A dictionary mapping DPS code names to their values.
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
        """
        Get the model-specific value for a command.

        For example, L60 (T2267) uses base64 encoded values for MODE commands,
        but G30 (T2250) uses human-readable values directly.

        Args:
            command_name: The command name (e.g., "MODE")
            value: The human-readable value (e.g., "auto")

        Returns:
            The model-specific value for the command (e.g., "BBoCCAE=" for L60 "auto" mode)
        """
        try:
            robovac_command = RobovacCommand(command_name)
            values = self._get_command_values(robovac_command)

            if values is not None:
                # Handle dictionary values (explicit mapping)
                if isinstance(values, dict) and value in values:
                    return str(values[value])

                # Handle list values (value must be in the list to be valid)
                elif isinstance(values, list) and value in values:
                    return str(value)

        except (ValueError, KeyError):
            # Handle invalid command names (ValueError) or missing dictionary keys (KeyError)
            pass

        # If no valid mapping is found, return the original value
        return value
